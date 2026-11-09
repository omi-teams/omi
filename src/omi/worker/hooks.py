"""Project hooks (.omi/hooks/<event>) run in a one-shot container."""

import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ..common import core
from . import creds, docker
from ..state import resolve as state
from ..project import scope, structure, tasks


HOOK_EVENTS = ("pre-run", "post-run", "pre-merge")
OMI_MOUNT = "/opt/omi"  # host dir holding the stdlib-only omi package, mounted ro so hooks can run `python3 -m omi`
HOOK_RUNNERS = {".sh": ["sh", "-s"], ".py": ["python3", "-"]}


def git_env(wt):
    """Mount and env that make git work in a container when the worktree's .git file points to a host path:
    (main .git dir to mount ro at /gitdir, env pairs), or None for a normal checkout.
    OMI_GIT_DIR, not GIT_DIR: the hook script exports GIT_DIR=$OMI_GIT_DIR GIT_WORK_TREE=/work only around the git-using command,
    since a global GIT_DIR would break the temp repos its test suite creates."""
    dotgit = Path(wt) / ".git"
    text = dotgit.read_text(encoding="utf-8").strip() if dotgit.is_file() else ""
    gitdir = Path(text.removeprefix("gitdir:").strip()) if text.startswith("gitdir:") else None
    if not gitdir or gitdir.parent.name != "worktrees":
        return None
    return str(gitdir.parents[1]), (f"OMI_GIT_DIR=/gitdir/worktrees/{gitdir.name}",
                                    "GIT_CONFIG_COUNT=1", "GIT_CONFIG_KEY_0=safe.directory", "GIT_CONFIG_VALUE_0=*")


def hook_timeout(main):
    cfg = Path(main) / ".omi" / "config.json"
    return (json.loads(cfg.read_text(encoding="utf-8")) if cfg.exists() else {}).get("hook_timeout", 600)


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
    git_mount, git_vars = git_env(wt) or (None, ())
    # Overlay the authoritative map only in the hook container: leave the host worktree
    # and its index unchanged so a fixed map cannot make advance fail its clean check.
    with tempfile.TemporaryDirectory(prefix="omi-hook-map-") as tmp:
        map_mount = []
        if event == "post-run" and not project.detached:
            mapping = core.git(wt, "show", "development:.omi/structure.md")
            mapping = mapping.replace("\r\n", "\n") if mapping is not None else None
            local = Path(wt) / ".omi" / "structure.md"
            # read_text normalizes the checkout's CRLF to LF as well.
            if mapping is not None and (not local.is_file() or local.read_text(encoding="utf-8").strip() != mapping):
                source = Path(tmp) / "structure.md"
                core.write_text(source, mapping + "\n")
                map_mount = [f"{source}:/work/.omi/structure.md"]
        argv = docker.worker_argv(wt, image, HOOK_RUNNERS[script.suffix], name, docker.repo_key(main), docker.worker_labels(f"hook-{event}", tid, None, None),
                           ro=True, env_names=(f"PYTHONPATH={OMI_MOUNT}", *(("OMI_PROJECT_STATE=/state",) if project.detached else ()), *git_vars), offline=True,
                           mounts=[f"{Path(__file__).parents[1]}:{OMI_MOUNT}/omi", *([f"{project.state}:/state"] if project.detached else []),
                                   *([f"{git_mount}:/gitdir"] if git_mount else []), *map_mount],
                           **docker.worker_sizes(main))
        limit = hook_timeout(main)
        try:
            r = subprocess.run(argv, env=env, input=script.read_bytes().replace(b"\r\n", b"\n"), stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, timeout=limit)
        except subprocess.TimeoutExpired as e:
            subprocess.run(["docker", "rm", "-f", name], capture_output=True)
            return 124, (e.stdout or b"").decode("utf-8", "replace") + f"hook {event} timed out after {limit} s\n"
        return r.returncode, r.stdout.decode("utf-8", "replace")


def run_test(wt, main, cmd, tid, image):
    """Run the shell command `cmd` in the worker image on a temporary copy of the worktree, no network, no token.
    Returns (exit code, output); the copy is removed afterwards."""
    docker.need_docker()
    image = image or docker.ensure_image(main)
    env = dict(os.environ)
    env.pop(creds.TOKEN_ENV, None)
    name = docker.container_name(docker.repo_label(main), "test", tid)
    with tempfile.TemporaryDirectory(prefix="omi-test-") as tmp:
        copy = Path(tmp) / "work"
        shutil.copytree(wt, copy, symlinks=True)
        argv = docker.worker_argv(copy, image, ["bash", "-c", cmd], name, docker.repo_key(main), docker.worker_labels("test", tid, None, None),
                                  env_names=(), offline=True, **docker.worker_sizes(main))
        ended = False
        try:
            r = subprocess.run(argv, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=hook_timeout(main))
            ended = True
        except subprocess.TimeoutExpired as e:
            return 124, (e.stdout or b"").decode("utf-8", "replace") + "test timed out\n"
        finally:  # the per-task test container goes on a timeout, Ctrl-C or kill too (--rm covers a normal exit)
            if not ended:
                subprocess.run(["docker", "rm", "-f", name], capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def review_test_in_worker(main):
    """`review_test_in_worker` from .omi/config.json: run the pre-review test in the worker image; false when unset."""
    try:
        return json.loads((Path(main) / ".omi" / "config.json").read_text(encoding="utf-8")).get("review_test_in_worker") is True
    except (OSError, ValueError, AttributeError):
        return False


def hook_passed_on(text, sha):
    """True when the task's `## Reports` has a passed post-run hook line recorded for commit `sha`."""
    return bool(sha) and f" hook post-run passed on {sha}:" in text


def hook_note(task, event, res, sha=None):
    """Print a hook's output and record the outcome under `## Reports` (step done reads the last post-run line).
    `sha` (the clean HEAD the hook ran on) is recorded on a pass, so later test runs can reuse it."""
    rc, out = res
    print(out, end="")
    print(f"hook {event} " + ("passed" if rc == 0 else f"FAILED (exit {rc})"))
    line = f"{datetime.datetime.now():%Y-%m-%d %H:%M} hook {event} " + ("passed" + (f" on {sha}" if sha else "") if rc == 0 else f"FAILED (exit {rc})") + ":"
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


def regenerate(wt, project):
    """Run the project's `regenerate` command in the worktree so `generated` files match the engineer's changes."""
    cmd = scope.config(project, "regenerate", "")
    if not (scope.generated(project) and cmd):
        return
    try:
        res = subprocess.run(structure.tool_argv(cmd, posix=not core.WINDOWS), cwd=wt, stdin=subprocess.DEVNULL, capture_output=True,
                             encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"REGENERATE FAILED: {cmd} ({exc})")
        return
    if res.returncode:
        print(f"REGENERATE FAILED: {cmd} (exit {res.returncode})")
        print("\n".join((res.stdout + res.stderr).strip().splitlines()[-20:]))
    else:
        print(f"REGENERATED: {cmd}")
