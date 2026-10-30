"""Board data contracts, read-only behavior and state path boundaries."""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import helpers
from helpers import git
from omi.board import data


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def fixture(home):
    root = home / "projects" / "sample"
    write(root / ".omi/plans/PLAN-001.md", "---\nid: PLAN-001\ntitle: Plan\nstatus: active\n---\n")
    write(root / ".omi/workflows/feature.md", "---\nsteps:\n- id: accept | gate: po\n---\n")
    for id, status, extra in (("TASK-001", "done", ""), ("TASK-002", "in-progress", "step: accept\nworkflow: feature\n"),
                              ("TASK-003", "blocked", ""), ("TASK-004", "planned", "depends: TASK-001\n"),
                              ("TASK-005", "planned", "depends: TASK-003\n")):
        write(root / f".omi/tasks/{id}.md", f"---\nid: {id}\ntitle: <script>alert(1)</script>\nstatus: {status}\nplan: PLAN-001\n{extra}---\n"
              "## Goal\nShip it\n\n## Acceptance criteria\n- [x] one\n- [ ] two\n\n## Checkpoint\nDone: one\nNext: ask PO\n"
              "\n## Steps\n- accept started 2026-10-29 12:00\n\n## Reports\n- review 2026-10-29 13:00 took 12s\n\n## Usage\n"
              "| role | model | effort | input | output | cache | duration | skills read | verdict |\n"
              "|---|---|---|---|---|---|---|---|---|\n"
              "| omi-agent-reviewer | model-a | high | 10 | 2 | n/a | 12s | - | PASS |\n"
              "| omi-agent-reviewer | model-a | high | n/a | 0 | 3 | 1s | - | QUOTA->other |\n")
    write(root / ".omi/decisions.md", "# Decisions\n- 2026-10-28 | old\n- 2026-10-29 | new\n")
    return root


def test_views():
    with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OMI_STATE": directory}):
        home = Path(directory)
        root = fixture(home)
        git(home, "init", "-q", "-b", "main")
        git(home, "add", ".")
        git(home, "commit", "-qm", "initial state")
        git(home, "update-ref", "refs/remotes/origin/main", "HEAD")
        git(home, "config", "branch.main.remote", ".")
        git(home, "config", "branch.main.merge", "refs/remotes/origin/main")
        before = {f: f.read_bytes() for f in root.rglob("*") if f.is_file()}
        detail = data.task("sample", "TASK-002")
        assert detail["goal"] == "Ship it"
        assert detail["frontmatter"]["title"].startswith("<script>")
        assert detail["criteria"] == [{"text": "one", "checked": True}, {"text": "two", "checked": False}]
        assert "Next: ask PO" in detail["checkpoint"] and "accept started" in detail["steps"]
        assert "took 12s" in detail["reports"]
        assert detail["usage"]["input"] == 10 and detail["usage"]["review_rounds"] == 1
        view = data.project("sample")
        assert view["plans"][0]["done"] == 1 and view["plans"][0]["total"] == 5
        assert view["task_counts"] == {"planned": 2, "in-progress": 1, "blocked": 1, "review": 0, "done": 1}
        assert {(w["id"], w["reason"]) for w in view["po_waiting"]} == {
            ("TASK-002", "po_gate"), ("TASK-002", "next"), ("TASK-003", "blocked"), ("TASK-004", "next_task")}
        assert view["po_waiting_count"] == 3
        assert view["activity"][0]["time"] == "2026-10-29 13:00" and view["activity"][0]["duration"] == "12s"
        assert "new" in view["decisions"][0]
        assert view["usage"]["models"]["model-a"] == {"runs": 10, "input": 50, "output": 10, "cache": 15, "review_rounds": 5}
        assert view["sync"]["ahead"] == view["sync"]["behind"] == 0
        assert view["sync"]["dirty"] is False and "initial state" in view["sync"]["last_commit"]
        assert view["path"] == str(root.resolve()) and view["branch"] == "main"
        assert data.projects() == [{"name": "sample", "path": view["path"], "branch": "main", "sync": view["sync"],
                                    "plans": view["plans"], "task_counts": view["task_counts"], "po_waiting_count": 3}]
        json.dumps(view)
        assert before == {f: f.read_bytes() for f in root.rglob("*") if f.is_file()}
        path = root / ".omi/tasks/TASK-002.md"
        write(path, path.read_text(encoding="utf-8").replace("accept started", "accept done").replace("Ship it", "Updated"))
        assert data.task("sample", "TASK-002")["goal"] == "Updated"
        assert "po_gate" not in [w["reason"] for w in data.project("sample")["po_waiting"]]
        git(home, "add", ".")
        git(home, "commit", "-qm", "new state")
        assert data.project("sample")["sync"]["ahead"] == 1
        git(home, "update-ref", "refs/remotes/origin/main", "HEAD")
        git(home, "reset", "--soft", "HEAD~1")
        assert data.project("sample")["sync"]["behind"] == 1
        assert data.project("sample")["sync"]["dirty"] is True
        root.rename(root.with_name("sample.repo"))
        assert data.projects()[0]["name"] == "sample.repo"


def test_workflow_detail():
    with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OMI_STATE": directory}):
        root = fixture(Path(directory))
        steps = [{"id": id, "gate": "po" if id == "accept" else "none"}
                 for id in ("plan", "design", "build", "review", "accept", "qa")]
        definition = "---\nsteps:\n" + "".join(f"- id: {s['id']} | gate: {s['gate']}\n" for s in steps) + "---\n"
        write(root / ".omi/workflows/feature.md", definition)
        detail = data.task("sample", "TASK-002")
        assert detail["workflow_steps"] == steps and detail["current_step"] == "accept"
        assert data.project("sample")["kanban"]["in-progress"][0] == detail
        # Default, missing and changed definitions are read from state, never inferred from history.
        assert data.task("sample", "TASK-001")["workflow_steps"] == []
        write(root / ".omi/workflows/omi-flow-feature.md", definition)
        assert data.task("sample", "TASK-001")["workflow_steps"] == steps
        assert data.task("sample", "TASK-001")["current_step"] is None
        write(root / ".omi/workflows/feature.md", "---\nsteps:\n- id: custom | gate: po\n---\n")
        assert data.task("sample", "TASK-002")["workflow_steps"] == [{"id": "custom", "gate": "po"}]
        path = root / ".omi/tasks/TASK-002.md"
        write(path, path.read_text(encoding="utf-8").replace("workflow: feature", "workflow: ../../escape"))
        refuses(lambda: data.task("sample", "TASK-002"))


def test_path_refusal():
    with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OMI_STATE": str(Path(directory) / "state")}):
        home = Path(directory) / "state"
        root = fixture(home)
        for call in (lambda: data.project("../escape"), lambda: data.project("/absolute"),
                     lambda: data.task("sample", "../TASK-001"), lambda: data.task("sample", "x/y"),
                     lambda: data.project("."), lambda: data.task("sample", "x\\y")):
            refuses(call)
        outside = Path(directory) / "outside"
        outside.mkdir()
        for relative, directory_link in ((".omi/tasks/TASK-escape.md", False), (".omi/plans/PLAN-escape.md", False),
                                         (".omi/workflows/feature.md", False), (".omi/decisions.md", False)):
            target = root / relative
            if target.exists():
                target.unlink()
            try:
                target.symlink_to(outside / "missing", target_is_directory=directory_link)
            except OSError:
                print("skip board symlink refusal: symlink creation unavailable")
                return
            refuses(lambda: data.project("sample"))
            if relative == ".omi/workflows/feature.md":
                refuses(lambda: data.task("sample", "TASK-002"))
            target.unlink()
        try:
            (home / "projects/escape").symlink_to(outside, target_is_directory=True)
        except OSError:
            print("skip board symlink refusal: symlink creation unavailable")
            return
        refuses(data.projects)
        refuses(lambda: data.project("escape"))
        (home / "projects/escape").unlink()
        (root / ".omi/tasks").rename(root / ".omi/saved")
        try:
            (root / ".omi/tasks").symlink_to(outside, target_is_directory=True)
        except OSError:
            print("skip board symlink refusal: symlink creation unavailable")
            return
        refuses(lambda: data.project("sample"))


def refuses(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError("unsafe path accepted")


def test_empty_and_layer():
    with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OMI_STATE": directory}):
        assert data.projects() == []
        (Path(directory) / "projects/empty").mkdir(parents=True)
        view = data.project("empty")
        assert view["plans"] == view["po_waiting"] == view["activity"] == view["decisions"] == []
        assert view["usage"]["totals"]["runs"] == 0
        assert view["sync"]["ahead"] is None
        assert view["path"] == str(Path(directory).resolve() / "projects/empty")
        assert view["branch"] is None and view["sync"]["dirty"] is None
    rule = (Path(__file__).parents[1] / ".omi/rules/omi-modules.md").read_text(encoding="utf-8")
    order = next(line for line in rule.splitlines() if "module layer order" in line)
    assert order.index("app.cli") < order.index("board.data") < order.index("project.tasks") < order.index("state.resolve")


def main():
    test_views()
    test_workflow_detail()
    test_path_refusal()
    test_empty_and_layer()


if __name__ == "__main__":
    main()
