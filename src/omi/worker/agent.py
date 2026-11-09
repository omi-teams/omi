"""The agent container run: name retry, `run_timeout`, and the switch to the other tool after a usage limit or a bad login."""

import os
import re
import secrets
import subprocess
import sys
import threading
import types
from pathlib import Path

from ..project import scope
from . import creds, docker, tools

CLAUDE_ONLY = ("omi-agent-architect",)  # PO rule: the architect never runs on Codex
AUTH_RC, TIMEOUT_RC = 8, 9
TIMEOUTS = {"write": 7200, "read": 3600}  # default run_timeout in seconds per role access
LOGIN = {"claude": "claude /login", "codex": "codex login"}


class Timeout(Exception):
    """The agent container passed its run_timeout and was killed."""


def run_timeout(project, access: str) -> float:
    """`run_timeout` from .omi/config.json: seconds for every run, or {"write": s, "read": s}; defaults 2 h write, 1 h read."""
    value = scope.config(project, "run_timeout", None)
    if isinstance(value, dict):
        value = value.get(access)
    ok = isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0
    return value if ok else TIMEOUTS[access]


def killed(code):
    """A hook or container exit from a kill (`omi stop`, run_timeout, `docker stop`/`kill`): never resumed by the hook-fix path."""
    stopped = os.environ.get("OMI_RUN_DIR") and (Path(os.environ["OMI_RUN_DIR"]) / "stopped").exists()
    return bool(stopped) or code in (137, 143) or code < 0


def run_container(argv, env, name, timeout):
    """`docker run` with stderr echoed live; past `timeout` seconds the container is killed and Timeout raised."""
    fired = threading.Event()

    def expire():
        fired.set()
        docker.kill(containers=[name])

    timer = threading.Timer(timeout, expire)
    timer.daemon = True
    with subprocess.Popen(argv, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          encoding="utf-8", errors="replace") as p:
        err = []

        def pump():  # echo the agent's stderr live, keep a copy for the name-conflict check
            for line in p.stderr:
                err.append(line)
                sys.stderr.write(line)
                sys.stderr.flush()

        th = threading.Thread(target=pump, daemon=True)
        th.start()
        timer.start()
        try:
            out = p.stdout.read()
            p.wait()
        finally:
            timer.cancel()
        th.join()
    if fired.is_set():
        raise Timeout(f"{name} passed its run_timeout of {timeout:g} s")
    r = types.SimpleNamespace(stdout=out, stderr="".join(err), returncode=p.returncode)
    if r.returncode and docker.name_taken(r.stderr, name):
        raise docker.NameTaken(name)
    return r


def run_named(name_for, run_once, what):
    """run_once(name) with the container name from name_for(salt); a name in use gets one retry with a random 2-char suffix."""
    for salt in ("", secrets.token_hex(1)):
        try:
            return run_once(name_for(salt))
        except docker.NameTaken:
            continue
    sys.exit(f"container name in use again for {what}. Nothing changed.")


def failure(tool, r):
    """'quota' or 'auth' when the run ended on a usage limit or a revoked, expired or missing login, else None."""
    if tools.quota_hit(tool, r.stdout, r.returncode, r.stderr):
        return "quota"
    return "auth" if tools.auth_failed(tool, r.stdout, r.returncode, r.stderr) else None


def fresh_secret(tool):
    """The tool's host credentials read again (a rotated login is picked up)."""
    return creds.claude_auth() if tool == "claude" else creds.tool_secret(tool)


def other_tool(tool, role, main, want, want_model, role_model, efforts, models):
    """(other tool, its secret) to continue on, filling efforts/models; (None, why not) when it cannot."""
    other = "codex" if tool == "claude" else "claude"
    if role in CLAUDE_ONLY:
        return None, f"{role} runs on Claude only, no fallback to {other}"
    try:
        efforts[other] = tools.resolve_effort(want, other)
        try:
            models[other] = tools.resolve_model(main, want_model, other)
        except SystemExit:  # a full ID is specific to one tool; use the role alias on a switch
            if not re.fullmatch(tools.CODEX_ID if tool == "codex" else r"claude-[a-zA-Z0-9_.-]+", want_model or ""):
                raise
            models[other] = tools.resolve_model(main, role_model, other)
    except SystemExit as exc:
        return None, f"{other} cannot continue ({exc})"
    secret = fresh_secret(other)
    if not secret[1]:
        return None, f"{other} cannot continue ({secret[2] or f'no {other} token'})"
    return other, secret


def auth_line(tool):
    return f"AUTH: {tool} login invalid; run {LOGIN[tool]} on the host"


def cmd_shims(wt) -> list[str]:
    """The pre-review problem line for Windows `.cmd` shims in node_modules/.bin (npm ran on the Windows host, so the Linux
    worker gets host binaries); [] when there are none."""
    # ponytail: root and two workspace levels; a deeper monorepo layout needs a walk
    found = sorted({p.relative_to(wt).as_posix() for pat in ("", "*/", "*/*/") for p in Path(wt).glob(pat + "node_modules/.bin/*.cmd")})
    return [f"node_modules has {len(found)} Windows .cmd shims (npm ran on the host; delete node_modules and install in the worker): "
            + ", ".join(found[:5])] if found else []
