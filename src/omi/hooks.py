"""Project hooks (.omi/hooks/<event>) run in a one-shot container."""

import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

from . import core, creds, docker, state, tasks


HOOK_EVENTS = ("pre-run", "post-run", "pre-merge")
HOOK_RUNNERS = {".sh": ["sh", "-s"], ".py": ["python3", "-"]}


def run_hook(wt, main, event, tid, image):
    """Run .omi/hooks/<event>.sh|.py from state or the main checkout in its own one-shot container:
    worktree ro as cwd, no network, no token. Returns (exit code, output), or None when there is no hook."""
    project = state.resolve(wt)
    if project.detached:
        main = project.state
    script = next((p for e in HOOK_RUNNERS if (p := Path(main) / ".omi" / "hooks" / f"{event}{e}").is_file()), None)
    if not script:
        return None
    docker.need_docker()
    image = image or docker.ensure_image(main)
    env = dict(os.environ)
    env.pop(creds.TOKEN_ENV, None)
    name = docker.container_name(docker.repo_label(main), f"hook-{event}", tid)
    argv = docker.worker_argv(wt, image, HOOK_RUNNERS[script.suffix], name, docker.repo_label(main), docker.worker_labels(f"hook-{event}", tid, None, None),
                       ro=True, env_names=("OMI_PROJECT_STATE=/state",) if project.detached else (), offline=True,
                       mounts=[f"{project.state}:/state"] if project.detached else (),
                       **docker.worker_sizes(main))
    cfg = Path(main) / ".omi" / "config.json"
    limit = (json.loads(cfg.read_text(encoding="utf-8")) if cfg.exists() else {}).get("hook_timeout", 600)
    try:
        r = subprocess.run(argv, env=env, input=script.read_bytes().replace(b"\r\n", b"\n"), stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=limit)
    except subprocess.TimeoutExpired as e:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
        return 124, (e.stdout or b"").decode("utf-8", "replace") + f"hook {event} timed out after {limit} s\n"
    return r.returncode, r.stdout.decode("utf-8", "replace")


def hook_note(task, event, res):
    """Print a hook's output and record the outcome under `## Reports` (step done reads the last post-run line)."""
    rc, out = res
    print(out, end="")
    print(f"hook {event} " + ("passed" if rc == 0 else f"FAILED (exit {rc})"))
    line = f"{datetime.datetime.now():%Y-%m-%d %H:%M} hook {event} " + ("passed" if rc == 0 else f"FAILED (exit {rc})") + ":"
    tasks.append_note(task, "Reports", line + "\n" + "\n".join("> " + l for l in tasks.clip_report(out or "(no output)")))
    return rc


def wt_task(wt, tid):
    return state.task_file(state.resolve(wt), tid)


def hook_cmd(event, tid):
    project = state.resolve(core.main_checkout(".") or Path(".").resolve())
    root = project.state
    wt = core.task_worktrees(project.code).get(tid)
    if event not in HOOK_EVENTS or not wt:
        sys.exit(f"usage: omi hook {'|'.join(HOOK_EVENTS)} <TASK-ID> (the task needs a worktree). Nothing changed.")
    res = run_hook(wt, root, event, tid, None)
    if res is None:
        print(f"no {event} hook")
        return 0
    return hook_note(state.task_file(project, tid), event, res)
