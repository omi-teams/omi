"""Engineer session resume: the per-task transcript cache outside the repo and the `Session:` line in the task file."""

import json
import os
import re
import shutil
from pathlib import Path


# where each CLI keeps its transcripts under $HOME; only these directories reach the cache, never the auth files
TRANSCRIPTS = {"claude": ".claude/projects", "codex": ".codex/sessions"}
LINE = re.compile(r"^Session: (claude|codex) (\S+)\n?", re.M)


def root(repo):
    base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return base / "omi" / "sessions" / repo


def task_dir(repo, tid, tool):
    return root(repo) / tid / tool


def mount_args(repo, tid, tool):
    """`docker run` args binding this task's transcript cache (rw) at /sessions."""
    d = task_dir(repo, tid, tool)
    d.mkdir(parents=True, exist_ok=True)
    d.chmod(0o777)  # ponytail: the container user (uid 1000) must write; per-user cache dir above it stays private
    return ["--mount", f"type=bind,src={d},dst=/sessions"]


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
            found = sid if isinstance(sid, str) and re.fullmatch(r"[\w-]+", sid) else found
    return found


def recorded(text, tool):
    """The session id the task file records for this tool, or None (no line, or the last run used the other tool)."""
    m = LINE.search(text or "")
    return m[2] if m and m[1] == tool else None


def with_session(text, tool, sid):
    """Task text with its `Session:` line replaced by this one (appended under `## Checkpoint`, else at the end)."""
    text, line = LINE.sub("", text), f"Session: {tool} {sid}"
    head, sep, rest = text.partition("\n## Checkpoint")
    if not sep:
        return f"{text.rstrip()}\n\n## Checkpoint\n{line}\n"
    body, sep2, tail = rest.partition("\n## ")
    return f"{head}\n## Checkpoint{body.rstrip()}\n{line}\n" + (f"\n## {tail}" if sep2 else "")


def available(repo, tid, tool, sid):
    """True when the cache still holds the transcript of this session."""
    d = task_dir(repo, tid, tool)
    return d.is_dir() and any(d.rglob(f"*{sid}*"))


def clear(repo):
    shutil.rmtree(root(repo), ignore_errors=True)
