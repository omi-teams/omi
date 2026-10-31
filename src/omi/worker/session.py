"""Engineer session resume: the per-task transcript volume (a Docker named volume, never on the host filesystem) and the task's `Session:` line."""

import contextlib
import json
import re
import subprocess
from pathlib import Path


# where each CLI keeps its transcripts under $HOME; only these directories reach the volume, never the auth files
TRANSCRIPTS = {"claude": ".claude/projects", "codex": ".codex/sessions"}
LINE = re.compile(r"^Session: (claude|codex) (\S+)\n?", re.M)
SID = re.compile(r"\w[\w-]*")  # no leading '-': the id goes into argv
HELPER = ["--rm", "--network", "none", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--read-only"]
SCAN_TIMEOUT = 300


def _docker(*a, **kw):
    return subprocess.run(["docker", *a], capture_output=True, encoding="utf-8", errors="replace", **kw)


def volume(repo, tid, tool):
    """omi-sess-<repo key>-<task>-<tool> (repo: docker.repo_key), limited to Docker's [a-zA-Z0-9_.-]."""
    return re.sub(r"[^a-zA-Z0-9_.-]", "-", f"omi-sess-{repo}-{tid}-{tool}")


def exists(vol):
    return _docker("volume", "inspect", vol).returncode == 0


def drop(vol, why=None):
    """Remove the volume; `SESSION DROPPED: <why>` when given, `SESSION CACHE NOT REMOVED: <vol>` when docker refuses."""
    if why:
        print(f"SESSION DROPPED: {why}")
    try:
        ok = _docker("volume", "rm", vol).returncode == 0
    except OSError:
        ok = False
    if not ok:
        print(f"SESSION CACHE NOT REMOVED: {vol}")
    return ok


def mount_args(repo, tid, tool, image, fresh):
    """`docker run` args mounting this task's transcript volume at /sessions; fresh: a new, empty volume.
    A new volume is root-owned 0755, so a one-shot root helper (no caps, no network, ro rootfs) opens it to the container user."""
    vol = volume(repo, tid, tool)
    if fresh and exists(vol) and not drop(vol):  # never reuse an old session as a fresh one
        raise SystemExit(f"cannot remove the old session volume {vol}; remove it (omi clean) and retry. Nothing changed.")
    if fresh or not exists(vol):
        labels = [x for kv in ("omi-worker=1", f"omi-repo={repo}", f"omi-task={tid}", "omi-session=1") for x in ("--label", kv)]
        for cmd in (["volume", "create", *labels, vol],
                    ["run", *HELPER, "--user", "0", "--mount", f"type=volume,src={vol},dst=/s", image, "chmod", "0777", "/s"]):
            if (r := _docker(*cmd)).returncode:
                raise SystemExit(f"cannot prepare the session volume {vol} (docker {cmd[0]}): {r.stderr.strip()}. Nothing changed.")
    return ["--mount", f"type=volume,src={vol},dst=/sessions"]


def wrap(tool, cmd):
    """cmd run behind a shell that links the CLI's transcript directory to /sessions."""
    link = TRANSCRIPTS[tool]
    boot = f'mkdir -p "$HOME/{Path(link).parent.as_posix()}" && ln -s /sessions "$HOME/{link}"; exec "$@"'
    return ["sh", "-c", boot, "sh", *cmd]


def session_id(tool, out):
    """The last session id in the CLI's JSON event output (claude `session_id`, codex `thread.started`), or None."""
    found = None
    for line in (out or "").splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if isinstance(ev, dict):
            sid = ev.get("thread_id") if tool == "codex" and ev.get("type") == "thread.started" else \
                ev.get("session_id") if tool == "claude" else None
            found = sid if isinstance(sid, str) and SID.fullmatch(sid) else found
    return found


def recorded(text, tool):
    """The session id the task file records for this tool, or None (no line, or the last run used the other tool)."""
    m = LINE.search(text or "")
    return m[2] if m and m[1] == tool and SID.fullmatch(m[2]) else None


def with_session(text, tool, sid):
    """Task text with its `Session:` line replaced by this one (appended under `## Checkpoint`, else at the end)."""
    text, line = LINE.sub("", text), f"Session: {tool} {sid}"
    head, sep, rest = text.partition("\n## Checkpoint")
    if not sep:
        return f"{text.rstrip()}\n\n## Checkpoint\n{line}\n"
    body, sep2, tail = rest.partition("\n## ")
    return f"{head}\n## Checkpoint{body.rstrip()}\n{line}\n" + (f"\n## {tail}" if sep2 else "")


def available(repo, tid, tool, sid):
    """True when this session's volume still exists (a transcript lost inside it fails the resume: RESUME FAILED)."""
    return bool(SID.fullmatch(sid)) and exists(volume(repo, tid, tool))


def scrub(repo, tid, tool, image, secret_value):
    """False when a scan container finds no token value in the volume; else the volume is dropped and True (e.g. after `env`).
    Fails closed: a hit (grep 0), an unreadable entry (2), a docker error or a timeout all drop the volume; only grep 1 keeps it."""
    values = [secret_value] if secret_value else []
    try:
        blob = json.loads(secret_value or "")
    except ValueError:
        blob = None
    tokens = blob.get("tokens") if isinstance(blob, dict) else None
    if isinstance(tokens, dict):  # a codex ChatGPT login is the whole auth.json (creds.codex_login): each token alone is a secret too
        values += [v for k, v in tokens.items() if k.endswith("_token") and isinstance(v, str) and v and v != "omi-no-refresh"]
    # the raw values and their JSON-escaped forms (transcripts are JSON lines); grep -f reads one pattern per line,
    # so a multi-line raw value is left to its escaped form and its tokens, and an empty pattern (matches all) never goes in
    needles = sorted({n for v in values for n in (v, json.dumps(v)[1:-1]) if n and "\n" not in n})
    if not needles:
        return False
    vol = volume(repo, tid, tool)
    name, rc = f"{vol}-scan", None
    try:  # the token goes in on stdin, never in argv
        rc = _docker("run", "-i", "--name", name, "--label", "omi-worker=1", "--label", f"omi-repo={repo}", *HELPER,
                     "--user", "node", "--mount", f"type=volume,src={vol},dst=/s,readonly", image,
                     "grep", "-rqF", "-f", "-", "/s", input="\n".join(needles) + "\n", timeout=SCAN_TIMEOUT).returncode
    except (OSError, subprocess.SubprocessError):
        pass
    finally:  # Ctrl-C included
        if rc is None:  # timeout or Ctrl-C kill only the docker client; the container would keep the volume in use
            with contextlib.suppress(OSError):
                _docker("rm", "-f", name)
        if rc != 1:
            drop(vol, "token found in transcript" if rc == 0 else "cannot scan the session volume")
    return rc != 1


def clear(repo):
    """Remove this repo's session volumes; returns how many went."""
    r = _docker("volume", "ls", "-q", "--filter", "label=omi-session=1", "--filter", f"label=omi-repo={repo}")
    return sum(drop(v) for v in (r.stdout.split() if r.returncode == 0 else []))
