"""File findings about omi in its shared project state."""

import argparse
import os
import re
import shlex
from pathlib import Path

from ..common import core
from ..state import resolve as state, sync as state_sync


WORKFLOWS = {"bug": "omi-flow-bugfix", "security": "omi-flow-feature-sensitive", "idea": "omi-flow-feature"}


def omi_project() -> state.Project | None:
    root = state.state_home() / "projects" / "omi"
    return state.Project(root, root, True) if root in state.registry().values() else None


def source_context(cwd: str | Path = ".") -> tuple[str, str, str]:
    project = state.resolve(cwd)
    name = project.state.name if project.detached else project.code.name
    branch = core.git(cwd, "rev-parse", "--abbrev-ref", "HEAD") or ""
    tid = os.environ.get("OMI_TASK", "") or (branch[5:] if branch.startswith("task/") else "")
    if not tid:
        active = [f.stem for f in (project.state / ".omi" / "tasks").glob("TASK-*.md")
                  if core.meta(f).get("status") == "in-progress"]
        tid = active[0] if len(active) == 1 else "unknown"
    return name, tid, os.environ.get("OMI_AGENT", "Coordinator")


def open_count(source: str) -> int:
    project = omi_project()
    if project is None:
        return 0
    return sum(core.meta(f).get("status") != "done" and f"source_project: {source}" in f.read_text(encoding="utf-8").splitlines()
               for f in (project.state / ".omi" / "tasks").glob("TASK-*.md"))


def improve(args: list[str], cwd: str | Path = ".") -> None:
    parser = argparse.ArgumentParser(prog="omi improve")
    parser.add_argument("text")
    parser.add_argument("--kind", choices=WORKFLOWS, default="bug")
    parser.add_argument("--from", dest="source")
    opts = parser.parse_args(args)
    source, tid, agent = source_context(cwd)
    source = opts.source if opts.source is not None else source
    summary = opts.text.strip()
    if any(not value.strip() or len(value.splitlines()) != 1 for value in (summary, source, tid, agent)):
        raise state.StateError("improvement text and source context must be nonempty single lines")
    goal = f"{summary}\n\nSource project: {source}\nSource task: {tid}\nSource agent: {agent}\n"
    project = omi_project()
    if project is None:
        body = f"## Goal\n{goal}\nKind: {opts.kind}\n"
        print("No omi project in shared state. Ready-to-paste issue for omi-teams/omi:")
        print(f"Title: {summary}\n\n{body}")
        print(shlex.join(["gh", "issue", "create", "--repo", "omi-teams/omi", "--title", summary, "--body", body]))
        return
    state_sync.pull(project)
    directory = project.state / ".omi" / "tasks"
    found = list(directory.glob("TASK-*.md"))
    for task in sorted(found):
        text = task.read_text(encoding="utf-8")
        if core.parse(text).get("status") != "done" and f"title: {summary}" in text.partition("\n---")[0].splitlines():
            print(task.stem)
            return
    number = max((int(m[1]) for f in found if (m := re.fullmatch(r"TASK-(\d+)", f.stem))), default=0) + 1
    directory.mkdir(parents=True, exist_ok=True)
    while True:
        new_id = f"TASK-{number:03d}"
        task = directory / f"{new_id}.md"
        try:
            with task.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(f"---\nid: {new_id}\ntitle: {summary}\nstatus: planned\ntype: task\n"
                             f"workflow: {WORKFLOWS[opts.kind]}\nsource_project: {source}\n"
                             "role: omi-agent-engineer\nskills: []\nrefs: []\n---\n"
                             f"## Goal\n{goal}\n## Acceptance criteria\n- [ ] Resolve the reported finding.\n\n"
                             "## Checkpoint\nDone:\nNot done:\nTests:\nNext:\n")
            break
        except FileExistsError:
            number += 1
    path = task.relative_to(state_sync.repo(project)).as_posix()
    state_sync.commit(project, [path], f"file {new_id}: {summary}")
    print(new_id)
    if not state_sync.push(project):
        raise state.StateError(f"{new_id} saved locally; run omi sync to push it")
