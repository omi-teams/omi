import contextlib
import datetime
import io
import json
import re
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
from helpers import omi, git
from omi.project import tasks, tree


def test_plan_status():
    assert tasks.plan_status("active", ["done", "done"]) == "done"
    assert tasks.plan_status("active", ["done", "planned"]) == "active"
    assert tasks.plan_status("active", []) == "active"
    assert tasks.plan_status("done", []) == "done"


def test_hierarchy():
    t = lambda status="planned", **kw: {"status": status, **kw}
    assert tree.tree_errors({"A": t(type="epic"), "B": t(type="", parent="A")}) == [] and tree.derived_status({"A": {}}) == {"A": "planned"}
    assert tree.tree_errors({"A": t(type="story")}) == ["A: unknown type `story` (use milestone|epic|fr|nfr|task|bug|security|incident|change|spike|chore)"]
    assert tree.tree_errors({"A": t(parent="Z")}) == ["A: parent Z does not exist"]
    cyc = tree.tree_errors({"A": t(parent="B"), "B": t(parent="A"), "C": t(parent="C")})
    assert "A: parent cycle A -> B -> A" in cyc and "C: parent cycle C -> C" in cyc
    ds = lambda *sts: tree.derived_status({"P": t("done"), **{f"C{i}": t(s, parent="P") for i, s in enumerate(sts)}})["P"]
    assert (ds("done", "done"), ds("done", "blocked", "planned"), ds("planned", "planned"),
            ds("done", "planned"), ds("in-progress", "planned"), ds("review")) == ("done", "blocked", "planned", "in-progress", "in-progress", "in-progress")
    deep = {"M": t("done"), "E": t("done", parent="M"), "T1": t("done", parent="E"), "T2": t("blocked", parent="E")}
    assert tree.derived_status(deep) == {"M": "blocked", "E": "blocked", "T1": "done", "T2": "blocked"}
    with patch.object(sys, "stderr", io.StringIO()):
        try:
            tasks.rolled_up({"A": t(parent="Z")})
        except SystemExit as e:
            assert "A: parent Z does not exist" in str(e.code)
        else:
            raise AssertionError("invalid hierarchy accepted")


def test_hierarchy_status_and_run():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        for tid, extra in (("TASK-001", "type: epic\nstatus: planned\n"), ("TASK-002", "parent: TASK-001\nstatus: done\n"),
                           ("TASK-003", "parent: TASK-001\nstatus: planned\n")):
            f = root / ".omi" / "tasks" / f"{tid}.md"
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(f"---\nid: {tid}\ntitle: T\n{extra}---\n", encoding="utf-8")
        git(root, "init", "-q")
        out = io.StringIO()
        with contextlib.redirect_stdout(out), patch.object(Path, "cwd", return_value=root):
            omi.app.cli.status(str(root))
        text = out.getvalue()
        assert "tree:\nTASK-001 [epic] in-progress T (1/2 done)\n  TASK-002 [task] done T\n  TASK-003 [task] planned T\n" in text, text
        assert text.endswith("next: TASK-003\n") and "[Đang làm] TASK-001" not in text, text
        try:
            tasks.check_runnable(root, "TASK-001")
        except SystemExit as e:
            assert "has child tasks (TASK-002, TASK-003)" in str(e.code)
        else:
            raise AssertionError("parent runnable")
        tasks.check_runnable(root, "TASK-003")


def test_roles():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        saved, sys.stdout = sys.stdout, io.StringIO()
        try:
            omi.setup.upgrade.init(root)
            omi.project.catalogs.agents_catalog(root)
        finally:
            sys.stdout = saved
        assert not (root / ".claude" / "agents").exists()
        cat = (root / ".omi" / "agents" / "CATALOG.md").read_text()
        assert "- omi-agent-engineer (write, sonnet/medium):" in cat and "- omi-agent-reviewer (read, sonnet/medium):" in cat
        assert omi.project.catalogs.get_role(root, "omi-agent-reviewer")["access"] == "read"
        try:
            omi.project.catalogs.get_role(root, "ghost")
        except SystemExit as e:
            assert "unknown role" in str(e)
        else:
            raise AssertionError("unknown role accepted")
        try:
            omi.project.catalogs.task_skill_ids(root, {"role": "ghost"})
        except SystemExit as e:
            assert "ghost" in str(e)
        else:
            raise AssertionError("unknown task role accepted")
        assert omi.project.catalogs.task_skill_ids(root, {"skills": "[a]"}) == ["a"]
        (root / ".omi" / "agents" / "omi-agent-reviewer.md").write_text("---\nrole: omi-agent-reviewer\nmodel: sonnet\neffort: low\naccess: read\n"
                                                           "skills: [x, a]\nsummary: s\n---\nbody")
        assert omi.project.catalogs.task_skill_ids(root, {"role": "omi-agent-reviewer", "skills": "[a, b]"}) == ["x", "a", "b"]
        (root / ".omi" / "agents" / "reviewer.md").write_text("---\nrole: reviewer\nmodel: sonnet\neffort: low\naccess: read\n"
                                                           "skills: []\nsummary: s\n---\nbody")
        try:
            omi.project.catalogs.load_roles(root)
        except SystemExit as e:
            assert "must start with `omi-agent-`" in str(e) or "differs from file name" in str(e), str(e)
        else:
            raise AssertionError("role without omi-agent- prefix accepted")
        (root / ".omi" / "agents" / "reviewer.md").unlink()
        assert "tests/test_omi.py" not in omi.worker.run.test_command(root, root)[-1]
    a = omi.worker.tools.codex_cmd("---\n---\nbody", "t.md", "claude-sonnet-5-5", "low")
    assert a[:8] == ["codex", "exec", "-c", "project_doc_max_bytes=0", "-m", "claude-sonnet-5-5", "-c", "model_reasoning_effort=low"] and "/work/t.md" in a[-1]
    assert "git rm" in a[-1] and "rm` may be refused" in a[-1]
    # claude's command never gets the codex option
    assert "project_doc_max_bytes=0" not in omi.worker.tools.engineer_cmd("---\n---\nbody", "t.md", "claude-sonnet-5-5", "low", "")


def test_task_flow_commit_scope_sync_warn():
    with tempfile.TemporaryDirectory() as d:
        main = Path(d).resolve() / "main"
        omi.setup.upgrade.init(main)
        (main / ".omi" / "tasks").mkdir(exist_ok=True)
        task = main / ".omi" / "tasks" / "TASK-001.md"
        task.write_text("---\nid: TASK-001\nstatus: in-progress\nscope: src/**\nrole: omi-agent-engineer\n"
                        "workflow: omi-flow-feature\n---\n## Steps\n", encoding="utf-8")
        git(main, "symbolic-ref", "HEAD", "refs/heads/development")
        git(main, "config", "user.name", "t")
        git(main, "config", "user.email", "t@t")
        git(main, "add", "-A")
        git(main, "commit", "-qm", "init")
        (main / "other.txt").write_text("x", encoding="utf-8")  # untracked, must stay untouched
        (main / ".omi" / "decisions.md").write_text("changed", encoding="utf-8")
        git(main, "add", ".omi/decisions.md")  # staged, must stay staged
        sys.stdout, saved = io.StringIO(), sys.stdout
        try:
            assert omi.project.tasks.step(main, "TASK-001", "next") == 0
        finally:
            sys.stdout = saved
        first = omi.common.core.parse(task.read_text(encoding="utf-8"))["step"]
        assert omi.common.core.git(main, "log", "-1", "--format=%s") == f"chore(TASK-001): step {first} next"
        assert omi.common.core.git(main, "show", "--name-only", "--format=", "HEAD") == ".omi/tasks/TASK-001.md"
        assert "M  .omi/decisions.md" in omi.common.core.git(main, "status", "--porcelain")
        assert "?? other.txt" in omi.common.core.git(main, "status", "--porcelain")
        for action, why in (("done", None), ("skip", "n/a")):
            sys.stdout, saved = io.StringIO(), sys.stdout
            try:
                if action == "done":
                    assert omi.project.tasks.step(main, "TASK-001", "done") == 0
                else:
                    assert omi.project.tasks.step(main, "TASK-001", "next") == 0
                    assert omi.project.tasks.step(main, "TASK-001", "skip", why=why) == 0
            finally:
                sys.stdout = saved
            cur = omi.common.core.parse(task.read_text(encoding="utf-8"))["step"]
            assert omi.common.core.git(main, "log", "-1", "--format=%s") == f"chore(TASK-001): step {cur} {action}"
            assert omi.common.core.git(main, "show", "--name-only", "--format=", "HEAD") == ".omi/tasks/TASK-001.md"
        # nothing changed: no new commit
        head = omi.common.core.git(main, "rev-parse", "HEAD")
        omi.project.tasks.commit_task_file(main, task, "chore: noop")
        assert omi.common.core.git(main, "rev-parse", "HEAD") == head
        assert "M  .omi/decisions.md" in omi.common.core.git(main, "status", "--porcelain")
        # scope sync: widen on development only, the worktree copy follows
        wt = Path(d).resolve() / "wt"
        git(main, "worktree", "add", "-q", str(wt), "-b", "task/TASK-001", "development")
        (wt / ".omi" / "tasks" / "TASK-001.md").write_text(
            task.read_text(encoding="utf-8").replace("## Steps", "## Steps\n- local line"), encoding="utf-8")
        text = task.read_text(encoding="utf-8").replace("scope: src/**", "scope: src/**, docs/**")
        task.write_text(text, encoding="utf-8")
        git(main, "commit", "-qm", "widen", "--", ".omi/tasks/TASK-001.md")
        sys.stdout, saved = io.StringIO(), sys.stdout
        try:
            omi.project.tasks.sync_scope(wt, wt / ".omi" / "tasks" / "TASK-001.md", "TASK-001")
            out = sys.stdout.getvalue()
            omi.project.tasks.sync_scope(wt, wt / ".omi" / "tasks" / "TASK-001.md", "TASK-001")
            again = sys.stdout.getvalue()
        finally:
            sys.stdout = saved
        assert "SCOPE SYNCED: src/**, docs/**" in out and again == out
        synced = (wt / ".omi" / "tasks" / "TASK-001.md").read_text(encoding="utf-8")
        assert "scope: src/**, docs/**" in synced and "- local line" in synced
        # #4: with a worktree the step lands in the worktree's task file, development gets no commit
        head = omi.common.core.git(main, "rev-parse", "HEAD")
        sys.stdout, saved = io.StringIO(), sys.stdout
        try:
            assert omi.project.tasks.step(main, "TASK-001", "next") == 0
        finally:
            sys.stdout = saved
        assert omi.common.core.git(main, "rev-parse", "HEAD") == head
        assert omi.common.core.parse((wt / ".omi" / "tasks" / "TASK-001.md").read_text(encoding="utf-8")).get("step") != \
            omi.common.core.parse(task.read_text(encoding="utf-8")).get("step")
        # sensitive-scope warning
        m = {"scope": "db/migrations/**, src/**", "workflow": "omi-flow-feature"}
        sys.stdout, saved = io.StringIO(), sys.stdout
        try:
            omi.project.tasks.warn_sensitive(m)
            warned = sys.stdout.getvalue()
            sys.stdout.truncate(0)
            omi.project.tasks.warn_sensitive({**m, "workflow": "omi-flow-feature-sensitive"})
            quiet = sys.stdout.getvalue()
        finally:
            sys.stdout = saved
        assert warned == "WARN: scope touches migrations - consider omi-flow-feature-sensitive\n" and not quiet
        for glob, hit in (("src/authors/**", False), ("src/oauth/**", False), ("src/auth/**", True), ("app/secrets/*", True),
                          (".github/workflows/**", True), ("src/**", False)):
            sys.stdout, saved = io.StringIO(), sys.stdout
            try:
                omi.project.tasks.warn_sensitive({"scope": glob, "workflow": "omi-flow-feature"})
                assert bool(sys.stdout.getvalue()) == hit, glob
            finally:
                sys.stdout = saved


def test_tree_logic_lives_in_tree_module():
    for name in ("TYPES", "TYPE_WORKFLOWS", "children_map", "tree_errors", "derived_status", "warn_type_workflow"):
        assert hasattr(tree, name) and not hasattr(tasks, name), name
    assert len(Path(tasks.__file__).read_text(encoding="utf-8").splitlines()) <= 610


def test_tree_table():
    t = lambda typ, **kw: {"status": "planned", "type": typ, **kw}
    allowed = {"milestone": [], "epic": ["milestone"], "fr": ["epic", "milestone"], "nfr": ["epic", "milestone"],
               "incident": ["milestone", "epic"], "change": ["fr", "nfr", "epic", "milestone"],
               "task": ["milestone", "epic", "fr", "nfr", "change"], "bug": ["fr", "nfr", "incident"], "security": ["fr", "nfr", "incident"],
               "spike": ["milestone", "epic", "fr", "nfr"], "chore": ["milestone", "epic", "incident"]}
    for typ, parents in allowed.items():
        assert tree.tree_errors({"A": t(typ)}) == [], typ  # every type may be a root
        for ptyp in tree.TYPES:
            errs = tree.tree_errors({"P": t(ptyp), "A": t(typ, parent="P")})
            assert (errs == []) == (ptyp in parents), (typ, ptyp, errs)
    leaf = tree.tree_errors({"P": t("task"), "A": t("bug", parent="P")})
    assert leaf == ["A: parent P is a leaf type `task` and cannot have children"]
    assert tree.tree_errors({"P": t("fr"), "A": t("milestone", parent="P")}) == ["A: `milestone` cannot be under P (`fr`); `milestone` has no parent"]
    assert tree.tree_errors({"P": t("task"), "A": t("security", parent="P")}) and tree.tree_errors({"P": t("epic"), "A": t("bug", parent="P")})
    assert tasks.rolled_up({"A": t("epic"), "B": t("task", parent="A")})["A"]["status"] == "planned"


def test_type_validation_and_workflow_warning():
    t = lambda **k: {"status": "planned", **k}
    for typ in ("bug", "security", "incident", "change", "spike", "chore"):
        assert omi.project.tree.tree_errors({"A": t(type=typ)}) == []
    def warned(m):
        with patch("sys.stdout", io.StringIO()) as out:
            omi.project.tree.warn_type_workflow(m)
        return out.getvalue()
    assert "type `task` does not match workflow omi-flow-incident" in warned({"type": "task", "workflow": "omi-flow-incident"})
    assert "omi-flow-bugfix" in warned({"type": "bug", "workflow": "omi-flow-feature"})
    for typ, wf in (("bug", "omi-flow-bugfix"), ("security", "omi-flow-feature-sensitive"), ("task", "omi-flow-feature-sensitive"),
                    ("chore", "omi-flow-refactor"), ("task", "omi-flow-feature"), (None, None)):
        assert not warned({"type": typ, "workflow": wf}), (typ, wf)


def test_step_approve_reopen():
    # Exercise the same authoritative-task routing for local and detached state.
    for detached in (False, True):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            with patch("sys.stdout", io.StringIO()):
                omi.setup.upgrade.init(root)
            code = root / "code" if detached else root
            project = omi.state.resolve.Project(root, code, detached)
            task = root / ".omi" / "tasks" / "TASK-109.md"
            commits = []
            real = omi.project.workflows.get_workflow  # accept is an auto gate in omi-flow-feature; this test needs a po gate
            po_gate = lambda r, w: [dict(st, gate="po") if st["id"] == "accept" else st for st in real(r, w)]  # noqa: E731
            with patch("omi.project.workflows.get_workflow", side_effect=po_gate), \
                    patch("omi.project.tasks.commit_task_file", side_effect=lambda *args: commits.append(args)), \
                    patch("omi.common.core.task_worktrees", return_value={}), patch("sys.stdout", io.StringIO()):
                def go(action, why=None):
                    return omi.project.tasks.step(project, "TASK-109", action, why=why)

                def refuses(action, why, message):
                    before, count = task.read_text(encoding="utf-8"), len(commits)
                    try:
                        go(action, why)
                    except SystemExit as exc:
                        assert message in str(exc), str(exc)
                    else:
                        raise AssertionError(f"{action} should fail")
                    assert task.read_text(encoding="utf-8") == before and len(commits) == count

                task.write_text("---\nid: TASK-109\nscope: src/**\nworkflow: omi-flow-feature\nstatus: in-progress\n---\n"
                                "## Acceptance criteria\n- [x] tested\n\n## Steps\n\n## Checkpoint\nDone:\n",
                                encoding="utf-8")
                refuses("approve", "yes", "no step started")
                refuses("reopen", "CI failed", "not complete")
                go("next")
                refuses("approve", "yes", "not a po gate")
                refuses("reopen", "CI failed", "running")
                go("done")
                refuses("reopen", "CI failed", "not complete")
                go("next"), go("done"), go("next")
                refuses("done", None, "verdict is missing")
                task.write_text(task.read_text(encoding="utf-8") + "\n## Usage\n| role | verdict |\n| omi-agent-reviewer | PASS abc1234 |\n", encoding="utf-8")
                go("done"), go("next")
                refuses("approve", None, "--why")
                refuses("approve", " \n ", "--why")
                # Verify the existing CLI --why parser reaches the new action unchanged.
                with patch("omi.state.resolve.resolve", return_value=project), patch("omi.common.core.main_checkout", return_value=root), \
                        patch("sys.stdout.reconfigure", create=True):
                    try:
                        omi.app.cli.dispatch(["step", "TASK-109", "approve", "--why", "Ship it!\nReviewed all criteria."])
                    except SystemExit as exc:
                        assert exc.code == 0
                    else:
                        raise AssertionError("CLI did not execute approve")
                text = task.read_text(encoding="utf-8")
                assert "PO approval accept: Ship it! Reviewed all criteria.\n\n## Checkpoint" in text
                assert omi.project.tasks.po_approved(text, "accept")
                if detached:
                    assert not commits and not code.exists()
                else:
                    assert commits[-1] == (root, task, "chore(TASK-109): step accept approve")
                go("done")
                task.write_text(omi.project.tasks.set_front(task.read_text(encoding="utf-8"), "status", "done"), encoding="utf-8")
                refuses("reopen", " ", "--why")
                go("reopen", "CI red\nfix required")
                text = task.read_text(encoding="utf-8")
                assert omi.common.core.parse(text)["step"] == "build"
                assert omi.common.core.parse(text)["status"] == "in-progress"
                assert re.search(r"^- workflow reopened .*: CI red fix required$", text, re.M)
                assert "PO approval accept: Ship it!" in text  # Preserve the audit trail.
                assert not omi.project.tasks.po_approved(text, "accept")
                assert omi.project.tasks.step_states(text) == {"plan": "done", "build": "started", "review": "failed", "accept": "failed"}
                if detached:
                    assert not commits
                else:
                    assert commits[-1] == (root, task, "chore(TASK-109): step build reopen")
                refuses("reopen", "again", "running")
                go("done"), go("next")
                refuses("done", None, "verdict is missing")  # the PASS from before the reopen is stale
                task.write_text(task.read_text(encoding="utf-8") + "| omi-agent-reviewer | PASS def5678 |\n", encoding="utf-8")
                go("done"), go("next")
                refuses("done", None, "po gate")
                go("approve", "Approved after the CI fix"), go("done"), go("next")
                assert omi.project.tasks.po_approved(task.read_text(encoding="utf-8"), "accept")


def test_reopen_last_write_step():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve()
        task = root / ".omi/tasks/TASK-109.md"
        task.parent.mkdir(parents=True)
        steps = [{"id": sid, "role": role} for sid, role in (
            ("build", "omi-agent-engineer"), ("fix", "omi-agent-engineer"),
            ("review", "omi-agent-reviewer"), ("accept", "coordinator"))]
        text = "---\nid: TASK-109\nstep: accept\n---\n## Steps\n" + "".join(
            f"- {s['id']} done 2026-10-29 10:00\n" for s in steps)
        task.write_text(text, encoding="utf-8")
        project = omi.state.resolve.Project(root, root, True)
        with patch("omi.project.workflows.get_workflow", return_value=steps), \
                patch("omi.project.catalogs.get_role", side_effect=lambda root, role: {"access": "write" if role == "omi-agent-engineer" else "read"}), \
                patch("sys.stdout", io.StringIO()):
            omi.project.tasks.step(project, "TASK-109", "reopen", why="CI failed")
            assert omi.common.core.meta(task)["step"] == "fix"
            assert omi.project.tasks.step_states(task.read_text(encoding="utf-8"))["build"] == "done"
            task.write_text(text, encoding="utf-8")
            for s in steps[:2]:
                s["role"] = "coordinator"
            try:
                omi.project.tasks.step(project, "TASK-109", "reopen", why="CI failed")
            except SystemExit as exc:
                assert "no write step" in str(exc)
            else:
                raise AssertionError("reopened workflow with no write step")
            assert task.read_text(encoding="utf-8") == text


def test_append_note_strips_control_bytes():
    with tempfile.TemporaryDirectory() as d:
        task = Path(d) / "TASK-1.md"
        task.write_text("---\nid: TASK-1\n---\n## Reports\n", encoding="utf-8")
        for heading in ("Reports", "Checkpoint"):
            omi.project.tasks.append_note(task, heading, "a\x00b\x01c\x1bd\x7fe\r\tf\ng")
        raw = task.read_bytes()
        assert not re.search(rb"[\x00-\x08\x0b-\x1f\x7f]", raw) and b"abcde\tf\ng" in raw


def test_note():
    for detached in (False, True):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            with patch("sys.stdout", io.StringIO()):
                omi.setup.upgrade.init(root)
            code = root / "code" if detached else root
            project = omi.state.resolve.Project(root, code, detached)
            task = root / ".omi" / "tasks" / "TASK-109.md"
            task.write_text("---\nid: TASK-109\n---\n## Reports\n", encoding="utf-8")
            with patch("omi.common.core.task_worktrees", return_value={}):
                omi.project.tasks.note(project, "TASK-109", "review", "FAIL", "fix round\nsecond line")
                text = task.read_text(encoding="utf-8")
                assert re.search(r"Coordinator \(review\) FAIL:\n> fix round\n> second line", text) and re.search(r"\d{4}-\d\d-\d\d \d\d:\d\d Coordinator", text)
                for bad in (("TASK-109", None, "FAIL", "x"), ("TASK-109", "review", "FAIL", " "), ("TASK-999", "review", "FAIL", "x"), ("../x", "review", "FAIL", "x")):
                    try:
                        omi.project.tasks.note(project, *bad)
                    except SystemExit as exc:
                        assert "Nothing changed" in str(exc)
                    else:
                        raise AssertionError(bad)
                    assert task.read_text(encoding="utf-8") == text


def test_step_back_to():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve()
        task = root / ".omi/tasks/TASK-138.md"
        task.parent.mkdir(parents=True)
        steps = [{"id": sid, "role": role, "gate": gate} for sid, role, gate in (
            ("plan", "coordinator", "none"), ("architect", "omi-agent-architect", "none"), ("build", "omi-agent-engineer", "none"),
            ("review", "omi-agent-reviewer", "review"), ("accept", "coordinator", "po"))]
        log = "- plan done 2026-10-31 10:00\n- architect done 2026-10-31 10:00\n- build started 2026-10-31 10:00\n"
        text = f"---\nid: TASK-138\nstatus: in-progress\nstep: build\n---\n## Steps\n{log}\n## Checkpoint\nDone:\n"
        task.write_text(text, encoding="utf-8")
        project = omi.state.resolve.Project(root, root, True)
        now = datetime.datetime(2026, 10, 31, 20, 30)
        with patch("omi.project.workflows.get_workflow", return_value=steps), patch("sys.stdout", io.StringIO()):
            def go(to, why="needs a new design"):
                return omi.project.tasks.step(project, "TASK-138", "back", why=why, now=now, to=to)

            for to, why, message in (("plan", "x", "not an agent step"), ("review", "x", "not an agent step"),
                                     ("build", "x", "not an agent step"), ("nope", "x", "not an agent step"), ("architect", " ", "--why")):
                try:
                    go(to, why)
                except SystemExit as exc:
                    assert message in str(exc), str(exc)
                else:
                    raise AssertionError(f"back --to {to} should fail")
                assert task.read_text(encoding="utf-8") == text
            assert go("architect") == 0
            new = task.read_text(encoding="utf-8")
            assert omi.common.core.parse(new)["step"] == "architect"
            assert "- workflow back to architect 2026-10-31 20:30: needs a new design\n- build failed 2026-10-31 20:30\n" \
                   "- architect started 2026-10-31 20:30\n\n## Checkpoint" in new
            assert omi.project.tasks.step_states(new) == {"plan": "done", "architect": "started", "build": "failed"}
            # from the po gate: steps in between fail and the earlier PO approval no longer counts
            task.write_text(text.replace("step: build", "step: accept").replace(
                "- build started 2026-10-31 10:00\n", "- build done 2026-10-31 10:00\n- review done 2026-10-31 10:00\n"
                "- accept started 2026-10-31 10:00\nPO approval accept: ok\n"), encoding="utf-8")
            assert omi.project.tasks.po_approved(task.read_text(encoding="utf-8"), "accept")
            go("architect")
            new = task.read_text(encoding="utf-8")
            assert omi.project.tasks.step_states(new) == {"plan": "done", "architect": "started", "build": "failed",
                                                          "review": "failed", "accept": "failed"}
            assert not omi.project.tasks.po_approved(new, "accept")


def test_round_limit_and_replan():
    def rows(*verdicts):
        return "".join(f"| omi-agent-reviewer | m | high | 1 | 1 | 1 | 1s | - | {v} |\n" for v in verdicts)

    def fails(fn, *words):
        try:
            fn()
        except SystemExit as exc:
            assert all(w in str(exc) for w in words), str(exc)
            return
        raise AssertionError(f"should fail: {words}")

    assert tasks.root_of("VERDICT: FAIL\n- x\nROOT: same") == "same" and tasks.root_of("VERDICT: PASS\nROOT: n/a\n") == "n/a"
    assert tasks.root_of("VERDICT: FAIL\nno root line") is None
    assert tasks.prior_review("\n## Usage\n| role |\n" + rows("FAIL abc1234 root:same"))[1] == "abc1234"
    with tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve()
        task = root / ".omi/tasks/TASK-139.md"
        task.parent.mkdir(parents=True)
        project = omi.state.resolve.Project(root, root, True)
        now = datetime.datetime(2026, 11, 2, 12, 0)
        flow = [("plan", "coordinator", "none"), ("architect", "omi-agent-architect", "none"), ("build", "omi-agent-engineer", "none"),
                ("review", "omi-agent-reviewer", "review"), ("accept", "coordinator", "po")]
        steps = lambda skip=(): [{"id": a, "role": b, "gate": c} for a, b, c in flow if a not in skip]
        roles = lambda root, role: {"access": "write" if role == "omi-agent-engineer" else "read"}

        def put(verdicts, log="", step="review", *, extra=""):
            task.write_text(f"---\nid: TASK-139\nscope: src/**\nstatus: in-progress\nstep: {step}\n---\n## Steps\n- plan done 2026-11-02 10:00\n"
                            f"- architect done 2026-11-02 10:00\n- build done 2026-11-02 10:00\n- review started 2026-11-02 10:00\n{log}\n"
                            f"## Usage\n| role | model | effort | input | output | cache | duration | skills read | verdict |\n|---|---|---|---|---|---|---|---|---|\n"
                            f"{rows(*verdicts)}{extra}", encoding="utf-8")
            return task.read_text(encoding="utf-8")

        def back(**kw):
            return omi.project.tasks.step(project, "TASK-139", "back", now=now, **kw)

        with patch("omi.project.workflows.get_workflow", side_effect=lambda r, w: steps()), \
                patch("omi.project.catalogs.get_role", side_effect=roles), patch("sys.stdout", io.StringIO()) as out:
            # below the limit, QUOTA rows do not count
            put(["FAIL abc1234 root:new", "QUOTA->codex"])
            assert back() == 0 and omi.common.core.parse(task.read_text(encoding="utf-8"))["step"] == "build"
            # at the limit: refused, nothing changed, even for a blank --why
            text = put(["FAIL abc1234", "FAIL abc1234 root:new"])
            fails(back, "ROUND LIMIT: TASK-139 failed 2 review rounds; the Coordinator decides")
            fails(lambda: back(why=" "), "ROUND LIMIT")
            fails(lambda: back(po=" "), "ROUND LIMIT")
            fails(lambda: omi.project.tasks.run_gate(project, "TASK-139", None), "ROUND LIMIT")
            assert task.read_text(encoding="utf-8") == text
            # run gate with the PO's words logs the override and lets exactly one more round through
            omi.project.tasks.run_gate(project, "TASK-139", "do one more, new approach")
            assert "PO round override 3: do one more, new approach\n" in task.read_text(encoding="utf-8")
            omi.project.tasks.run_gate(project, "TASK-139", None)
            assert back() == 0 and omi.common.core.parse(task.read_text(encoding="utf-8"))["step"] == "build"
            # a Coordinator reason (--why) allows exactly one more round and is recorded
            put(["FAIL abc1234", "FAIL abc1234"])
            assert back(why="new approach agreed") == 0 and "Coordinator round override 3: new approach agreed\n" in task.read_text(encoding="utf-8")
            put(["FAIL abc1234", "FAIL abc1234"])
            omi.project.tasks.run_gate(project, "TASK-139", None, "one more")
            assert "Coordinator round override 3: one more\n" in task.read_text(encoding="utf-8")
            omi.project.tasks.run_gate(project, "TASK-139", None)
            override = "PO round override 3: ok\n"
            put(["FAIL abc1234", "FAIL abc1234", "FAIL abc1234"], override)
            fails(back, "failed 3 review rounds")
            assert back(po="again", to="architect", why="redo") == 0 and "PO round override 4: again" in task.read_text(encoding="utf-8")
            # an override line elsewhere, or none for this round, is not a pass; --po below the limit logs nothing
            put(["FAIL abc1234"])
            assert back(po="unneeded") == 0 and "override" not in task.read_text(encoding="utf-8")
            # same root cause from round 2 goes to the architect; round 1 and ROOT: new go to build
            put(["FAIL abc1234 root:same"])
            assert back() == 0 and omi.common.core.parse(task.read_text(encoding="utf-8"))["step"] == "build"
            put(["FAIL abc1234", "FAIL abc1234 root:new"])
            assert back(po="x") == 0 and omi.common.core.parse(task.read_text(encoding="utf-8"))["step"] == "build"
            out.truncate(0)
            put(["FAIL abc1234 root:same", "FAIL abc1234 root:same"])  # at the limit, no override: the re-plan still goes through
            assert back() == 0 and omi.common.core.parse(task.read_text(encoding="utf-8"))["step"] == "architect"
            assert "REPLAN: same root cause" in out.getvalue() and "override" not in task.read_text(encoding="utf-8")
            out.truncate(0)
            put(["FAIL abc1234", "FAIL abc1234 root:same"], override)
            assert back() == 0
            new = task.read_text(encoding="utf-8")
            assert omi.common.core.parse(new)["step"] == "architect" and "REPLAN: same root cause" in out.getvalue()
            assert omi.project.tasks.step_states(new)["review"] == "failed" and "- architect started 2026-11-02 12:00" in new
        # no architect step: the line is printed and a Coordinator --why is required
        with patch("omi.project.workflows.get_workflow", side_effect=lambda r, w: steps(("architect",))), \
                patch("omi.project.catalogs.get_role", side_effect=roles), patch("sys.stdout", io.StringIO()) as out:
            text = put(["FAIL abc1234", "FAIL abc1234 root:same"], override)
            fails(back, "REPLAN: same root cause", "--why")
            assert task.read_text(encoding="utf-8") == text
            assert back(why="ok to patch") == 0 and "REPLAN: same root cause" in out.getvalue()
            new = task.read_text(encoding="utf-8")
            assert omi.common.core.parse(new)["step"] == "build" and "Coordinator replan override review: ok to patch" in new
    with patch.object(sys, "argv", ["omi"]):
        for name in ("reviewer", "security-reviewer"):
            assert "ROOT: same | new | n/a" in (omi.common.core.TEMPLATE / f"dot-omi/agents/omi-agent-{name}.md").read_text(encoding="utf-8")
    assert json.loads((omi.common.core.TEMPLATE / "dot-omi/config.json").read_text(encoding="utf-8"))["max_fix_rounds"] == 2
    for f in (omi.common.core.TEMPLATE / "dot-omi/workflows").glob("omi-flow-*.md"):
        text = f.read_text(encoding="utf-8")
        if "## Review-fail rule" in text and f.stem != "omi-flow-change-request":
            assert "ROUND LIMIT" in text.partition("## Review-fail rule")[2].partition("\n## ")[0], f.name
    for rel in ("AGENTS.md", "dot-claude/skills/omi-task/SKILL.md"):
        assert "ROUND LIMIT" in (omi.common.core.TEMPLATE / rel).read_text(encoding="utf-8") and "REPLAN: same root cause" in (omi.common.core.TEMPLATE / rel).read_text(encoding="utf-8")


def test_warn_skills_empty():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / ".omi" / "skills").mkdir(parents=True)
        (root / ".omi" / "skills" / "CATALOG.md").write_text(
            "- omi-skill-debug-root-cause (quality): Use when a test fails.\n- omi-skill-verify-evidence (quality): Use before DONE.\n",
            encoding="utf-8")

        def warn(m):
            out, saved = io.StringIO(), sys.stdout
            sys.stdout = out
            try:
                omi.project.catalogs.warn_skills_empty(root, m)
            finally:
                sys.stdout = saved
            return out.getvalue()

        assert warn({"type": "bug", "skills": "[]"}) == \
            "WARN: skills empty - consider omi-skill-debug-root-cause, omi-skill-verify-evidence from skills/CATALOG.md\n"
        assert warn({"type": "task"}).startswith("WARN: skills empty - consider omi-skill-verify-evidence")
        assert warn({"type": "bug", "skills": "[omi-skill-verify-evidence]"}) == ""


def test_task_skill_step_commands():
    template = omi.common.core.TEMPLATE / "dot-claude/skills/omi-task/SKILL.md"
    text = template.read_text(encoding="utf-8")
    assert 'step <ID> approve --why "<PO\'s words>"' in text
    assert '--title "<title>" --body-file <file>' in text and "[TASK-NNN] <type>(<area>): <summary>" in text
    assert "## Summary" in text and "## Known issues" in text and "gh pr ready --undo" in text
    assert "--draft" in text and "gh pr ready`" in text and "**Agent:** Coordinator" in text and "--subject" in text
    assert "gh pr edit task/<ID>" in text and "gh pr comment task/<ID> --body-file" in text
    release = (omi.common.core.TEMPLATE / "dot-claude/skills/omi-release/SKILL.md").read_text(encoding="utf-8")
    assert "[RELEASE vX.Y.Z] development -> staging" in release and "-> main" in release
    assert "--fill" not in text.replace("never `--fill`", "") and "--fill" not in release.replace("never `--fill`", "")
    assert 'step <ID> reopen --why "<CI failure reason>"' in text
    assert "review and accept again" in text


def test_workflows():
    def fails(fn, *words):
        try:
            fn()
        except SystemExit as e:
            assert all(w in str(e) for w in words), str(e)
            return str(e)
        raise AssertionError(f"should fail: {words}")

    with tempfile.TemporaryDirectory() as t:
        root = Path(t).resolve()
        wf = root / ".omi" / "workflows"
        saved, sys.stdout = sys.stdout, io.StringIO()
        try:
            omi.setup.upgrade.init(root)
            assert (wf / "CATALOG.md").exists(), "init creates the workflows folder"
            for sid, size in (("omi-skill-a", 100), ("omi-skill-b", 100), ("omi-skill-c", 100), ("omi-skill-big", 9000),
                              ("omi-skill-h1", 7900), ("omi-skill-h2", 7900), ("omi-skill-h3", 7900), ("omi-skill-h4", 7900)):
                d = root / ".omi" / "skills" / "g" / sid
                d.mkdir(parents=True)
                (d / "SKILL.md").write_text(f"---\ndescription: use for {sid}\n---\n" + "x" * size)
            omi.project.catalogs.skills_catalog(root)

            def flow(name, *steps, summary="Use for demos."):
                rows = "".join(f"- {s}\n" for s in steps)
                (wf / f"{name}.md").write_text(f"---\nid: {name}\nsummary: {summary}\nsteps:\n{rows}---\nPlaybook.\n")

            ok = ("id: plan | role: coordinator | skills: | input: idea | output: task file | gate: none | stop: AC written",
                  "id: build | role: omi-agent-engineer | skills: omi-skill-a | input: task | output: diff | gate: none | stop: tests pass",
                  "id: review | role: omi-agent-reviewer | skills: | input: diff | output: verdict | gate: review | stop: PASS",
                  "id: accept | role: coordinator | skills: | input: verdict | output: PO words | gate: po | stop: PO accepts")
            flow("omi-flow-demo", *ok)
            omi.project.workflows.workflows_catalog(root)
            cat = (wf / "CATALOG.md").read_text()
            assert "- omi-flow-demo: Use for demos. [plan > build > review > accept] [~" in cat, cat
            omi.project.workflows.check_all_workflows(root)
            assert [s["gate"] for s in omi.project.workflows.get_workflow(root, "omi-flow-demo")] == ["none", "none", "review", "po"]
            r = subprocess.run([sys.executable, "-m", "omi", "workflows", "--check"], cwd=root, capture_output=True, text=True,
                               env={**os.environ, "PYTHONPATH": str(Path(__file__).parents[1] / "src")})
            assert r.returncode == 0 and f"workflows ok ({len(list(wf.glob('omi-flow-*.md')))} checked)" in r.stdout, r.stdout + r.stderr

            # unknown ids, gates, budgets and size fail the check
            fails(lambda: omi.project.workflows.get_workflow(root, "omi-flow-ghost"), "unknown workflow `omi-flow-ghost`", "omi-flow-demo")
            bad = [("omi-flow-r", ok[1].replace("omi-agent-engineer", "omi-agent-ghost"), "unknown role `omi-agent-ghost`"),
                   ("omi-flow-s", ok[1].replace("omi-skill-a", "omi-skill-ghost"), "unknown skill omi-skill-ghost"),
                   ("omi-flow-g", ok[2].replace("gate: review", "gate: maybe"), "gate `maybe`"),
                   ("omi-flow-n", ok[2].replace("skills: ", "skills: omi-skill-a, omi-skill-b, omi-skill-c, omi-skill-big"),
                    "step review: skill budget", "omi-skill-big is", "per skill"),
                   ("omi-flow-t", ok[2].replace("skills: ", "skills: omi-skill-h1, omi-skill-h2, omi-skill-h3, omi-skill-h4"),
                    "step review: skill budget", "tokens in total", "at most 6000"),
                   ("omi-flow-k", ok[1].replace("omi-skill-a", "omi-skill-big"), "omi-skill-big is", "per skill"),
                   ("omi-flow-m", ok[0].replace(" | stop: AC written", ""), "step plan: missing `stop`")]
            for name, row, *words in bad:
                flow(name, row)
                fails(lambda: omi.project.workflows.get_workflow(root, name), *words)
                (wf / f"{name}.md").unlink()
            (root / ".omi" / "agents" / "omi-agent-reviewer.md").write_text(
                "---\nrole: omi-agent-reviewer\nmodel: sonnet\neffort: low\naccess: read\n"
                "skills: [omi-skill-a, omi-skill-b]\nsummary: s\n---\nbody")
            flow("omi-flow-d", ok[2].replace("skills: ", "skills: omi-skill-c, omi-skill-big"))
            fails(lambda: omi.project.workflows.get_workflow(root, "omi-flow-d"), "omi-skill-big is", "per skill")  # role defaults count per step
            (wf / "omi-flow-d.md").unlink()
            flow("omi-flow-long", *ok, summary="x" * 8000)
            fails(lambda: omi.project.workflows.get_workflow(root, "omi-flow-long"), "per workflow")
            (wf / "omi-flow-long.md").unlink()
            flow("bad-name", *ok)
            fails(lambda: omi.project.workflows.check_all_workflows(root), "must start with `omi-flow-`", "stale")
            (wf / "bad-name.md").unlink()
            omi.project.workflows.check_all_workflows(root)

            # step state
            task = root / ".omi" / "tasks" / "TASK-001.md"
            task.write_text("---\nid: TASK-001\nscope: src/**\nworkflow: omi-flow-demo\nstep:\n---\n## Goal\nG\n\n## Checkpoint\nDone:\n")
            go = lambda action, why=None: omi.project.tasks.step(root, "TASK-001", action, why)  # noqa: E731
            front = lambda: omi.common.core.meta(task)  # noqa: E731
            fails(lambda: go("done"), "no step started")
            assert go("next") == 0 and front()["step"] == "plan"
            fails(lambda: go("next"), "step plan is not done")
            fails(lambda: go("skip"), "--why")
            go("skip", "PO wrote the AC already")
            fails(lambda: go("skip", "again"), "already skipped")
            go("next")
            assert front()["step"] == "build" and omi.project.tasks.checkpoint(task.read_text()) == "Done:"
            # jumping over a step by editing the frontmatter is refused
            good = task.read_text()
            task.write_text(good.replace("step: build", "step: accept"))
            fails(lambda: go("done"), "build", "cannot be jumped over")
            task.write_text(good.replace("step: build", "step: ghost"))
            fails(lambda: go("next"), "`ghost` is not in workflow")
            task.write_text(good)
            go("done")
            go("next")
            fails(lambda: go("skip", "trust me"), "gate review", "cannot be skipped")
            before_review = task.read_text(encoding="utf-8")
            failed_review = before_review + ("\n## Usage\n| role | verdict |\n"
                                              "| omi-agent-reviewer | FAIL abc1234 root:same |\n")
            task.write_text(failed_review, encoding="utf-8")
            fails(lambda: go("done"), "last omi-agent-reviewer verdict is FAIL")
            fails(lambda: omi.project.tasks.step(root, "TASK-001", "done", po=" "), "verdict is FAIL")
            assert task.read_text(encoding="utf-8") == failed_review
            assert omi.project.tasks.step(root, "TASK-001", "done", po="Accept host evidence\nverified on host") == 0
            overridden = task.read_text(encoding="utf-8")
            assert "PO review override review: Accept host evidence verified on host" in overridden
            assert omi.project.tasks.step_states(overridden)["review"] == "done"
            assert "FAIL abc1234 root:same" in overridden  # preserve the review evidence
            task.write_text(before_review, encoding="utf-8")
            fails(lambda: go("done"), "verdict is missing")  # reviewer never ran
            assert task.read_text(encoding="utf-8") == before_review
            passed_review = before_review.replace("\n## Steps", "\n## Usage\n| role | verdict |\n| omi-agent-reviewer | PASS abc1234 |\n\n## Steps")
            task.write_text(passed_review, encoding="utf-8")
            go("done")
            go("next")
            assert front()["step"] == "accept"
            fails(lambda: go("skip", "no time"), "gate po")
            fails(lambda: go("done"), "po gate", "PO approval accept:")
            task.write_text(task.read_text() + "PO approval accept:\n")
            fails(lambda: go("done"), "po gate")  # empty approval text does not count
            task.write_text(task.read_text() + "PO approval accept: ok, ship it\n")
            good_ac = task.read_text()
            task.write_text(good_ac.replace("## Goal", "## Acceptance criteria\n- [x] a\n- [ ] b open\n\n## Goal"))
            fails(lambda: go("done"), "tick", "- [ ] b open")
            task.write_text(good_ac.replace("## Goal", "## Acceptance criteria\n- [x] a\n- [x] b\n\n## Goal"))
            go("done")
            assert go("next") == 0 and front()["step"] == "accept"
            text = task.read_text()
            assert re.search(r"## Steps\n- plan started .+\n- plan skipped .+: PO wrote the AC already\n- build started", text), text
            assert omi.project.tasks.step_states(text) == {"plan": "skipped", "build": "done", "review": "done", "accept": "done"}
            # back: a started review gate fails and the nearest earlier write step restarts
            task.write_text("---\nid: TASK-001\nscope: src/**\nworkflow: omi-flow-demo\nstep: plan\n---\n## Steps\n- plan started 2026-01-01 10:00\n")
            fails(lambda: go("back"), "not a review gate")
            go("done"), go("next")
            fails(lambda: go("back"), "not a review gate")  # build is not a review gate
            go("done"), go("next")
            assert front()["step"] == "review"
            assert go("back") == 0 and front()["step"] == "build"
            assert re.search(r"- review failed .+\n- build started .+\n$", task.read_text()), task.read_text()
            fails(lambda: go("back"), "not a review gate")
            go("done"), go("next")
            assert front()["step"] == "review"  # next from build reaches review again
            task.write_text(task.read_text() + "\n## Usage\n| role | verdict |\n| omi-agent-reviewer | PASS abc1234 |\n")
            go("done")
            fails(lambda: go("back"), "already done")
            # a PASS from an earlier round does not satisfy a restarted review (back)
            task.write_text("---\nid: TASK-001\nscope: src/**\nworkflow: omi-flow-demo\nstep:\n---\n## Usage\n| role | verdict |\n| omi-agent-reviewer | PASS old |\n")
            go("next"), go("done"), go("next"), go("done"), go("next")
            assert front()["step"] == "review"
            fails(lambda: go("done"), "verdict is missing")
            task.write_text(task.read_text() + "| omi-agent-reviewer | PASS new |\n")
            assert go("back") == 0 and front()["step"] == "build"  # a second review round starts after the PASS
            go("done"), go("next")
            fails(lambda: go("done"), "verdict is missing")
            # feature-sensitive: back from security skips the review step and lands on build
            sens = ("id: build | role: omi-agent-engineer | skills: | input: t | output: d | gate: none | stop: ok",
                    "id: review | role: omi-agent-reviewer | skills: | input: d | output: v | gate: review | stop: PASS",
                    "id: security | role: omi-agent-reviewer | skills: | input: d | output: v | gate: review | stop: PASS")
            flow("omi-flow-sens", *sens)
            task.write_text("---\nid: TASK-001\nscope: src/**\nworkflow: omi-flow-sens\nstep:\n---\n## Usage\n| role | verdict |\n")
            go("next"), go("done"), go("next")
            omi.project.tasks.append_note(task, "Usage", "| omi-agent-reviewer | PASS abc1234 |")
            go("done"), go("next")
            assert front()["step"] == "security" and go("back") == 0 and front()["step"] == "build"
            # task skills count for a write step only, never for a read-role step (security)
            tm = {"skills": "omi-skill-a, omi-skill-b"}
            assert omi.project.workflows.step_skill_ids(root, {"role": "omi-agent-reviewer", "skills": ""}, tm) == omi.project.workflows.step_skill_ids(
                root, {"role": "omi-agent-reviewer", "skills": ""}, {})
            assert {"omi-skill-a", "omi-skill-b"} <= set(omi.project.workflows.step_skill_ids(root, {"role": "omi-agent-engineer", "skills": ""}, tm))
            (wf / "omi-flow-sens.md").unlink()

            # unknown workflow on the task, default workflow, unknown task role
            task.write_text("---\nid: TASK-001\nscope: src/**\nworkflow: omi-flow-ghost\n---\n")
            fails(lambda: go("next"), "unknown workflow `omi-flow-ghost`")
            task.write_text("---\nid: TASK-001\nscope: src/**\n---\n")
            go("next")  # default workflow omi-flow-feature now exists
            assert front()["step"] == "plan"
            task.write_text("---\nid: TASK-001\nscope: src/**\nworkflow: omi-flow-demo\nrole: omi-agent-ghost\nstep: plan\n---\n"
                            "## Steps\n- plan done 2026-10-25 10:00\n")
            fails(lambda: go("next"), "unknown role `omi-agent-ghost`")
            fails(lambda: omi.project.tasks.step(root, "TASK-404", "next"), "no task file")
            fails(lambda: omi.project.tasks.step(root, "../TASK-001", "next"), "invalid task id")
            # a PO approval line outside ## Steps does not count
            task.write_text("---\nid: TASK-001\nscope: src/**\nworkflow: omi-flow-demo\nstep: accept\n---\nPO approval accept: sneaky\n\n"
                            "## Steps\n- plan done 2026-10-25 10:00\n- build done 2026-10-25 10:00\n- review done 2026-10-25 10:00\n"
                            "- accept started 2026-10-25 10:00\n\n## Checkpoint\nPO approval accept: x\n")
            fails(lambda: go("done"), "po gate")
            # a task with a worktree keeps its step state in the worktree copy, not the main checkout
            wt = root / "wt"
            (wt / ".omi" / "tasks").mkdir(parents=True)
            wtask = wt / ".omi" / "tasks" / "TASK-001.md"
            wtask.write_text("---\nid: TASK-001\nscope: src/**\nworkflow: omi-flow-demo\nstatus: in-progress\n---\n")
            task.write_text("---\nid: TASK-001\nscope: src/**\nworkflow: omi-flow-demo\n---\n")
            real_wts, omi.common.core.task_worktrees = omi.common.core.task_worktrees, lambda r: {"TASK-001": str(wt)}
            try:
                assert go("next") == 0
                assert omi.common.core.meta(wtask)["step"] == "plan" and "step" not in omi.common.core.meta(task)
                assert omi.project.tasks.tasks(root)["TASK-001"]["step"] == "plan"  # what `omi status` prints
            finally:
                omi.common.core.task_worktrees = real_wts
        finally:
            sys.stdout = saved
    tpl = omi.common.core.TEMPLATE / "dot-omi"
    assert "workflow: omi-flow-feature" in (tpl / "tasks" / "_template.md").read_text()
    with tempfile.TemporaryDirectory() as d, contextlib.redirect_stdout(io.StringIO()):
        repo = Path(d)
        omi.setup.upgrade.init(repo)
        for name in ("omi-flow-feature", "omi-flow-feature-ui", "omi-flow-feature-sensitive"):
            a = tpl / "workflows" / f"{name}.md"
            assert not omi.project.workflows.validate_workflow(repo, a), name
            assert "Review-fail rule" in a.read_text() and "PO gates" in a.read_text()


def test_missing_scope():
    class Out(io.StringIO):
        def reconfigure(self, **kw): pass
    for detached in (False, True):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            folder = root / ".omi" / "tasks"
            folder.mkdir(parents=True)
            project = omi.state.resolve.Project(root, root / "code" if detached else root, detached)
            task = folder / "TASK-001.md"
            (folder / "TASK-002.md").write_text("---\nid: TASK-002\nstatus: planned\nscope: src/**\n---\n", encoding="utf-8")
            flow = [dict(id=sid, role=role, gate="none", input="task", output="result", stop="done", skills="")
                    for sid, role in (("plan", "coordinator"), ("review", "reader"), ("build", "writer"))]
            def role(_, name):
                return {"access": "write" if name == "writer" else "read", "skills": ""}
            with patch("omi.common.core.main_checkout", return_value=root), \
                    patch("omi.state.resolve.resolve", return_value=project), \
                    patch("omi.common.core.task_worktrees", return_value={}), \
                    patch("omi.common.core.git", return_value=None), \
                    patch("omi.project.tasks.commit_task_file"), \
                    patch("omi.project.workflows.get_workflow", return_value=flow), \
                    patch("omi.project.catalogs.get_role", side_effect=role), \
                    patch("omi.project.catalogs.check_skills"), \
                    patch("omi.project.catalogs.warn_skills_empty"), \
                    patch("omi.worker.run.run_cmd", return_value=0) as run, \
                    patch("sys.stdout", Out()) as out:
                for scope_line in ("", "scope:\n", "scope: ,  ,\n"):
                    text = "---\nid: TASK-001\nstatus: planned\n" + scope_line + "---\n"
                    task.write_text(text, encoding="utf-8")
                    out.seek(0)
                    out.truncate()
                    try:
                        omi.app.cli.dispatch(["parallel", "TASK-001", "TASK-002"])
                    except SystemExit as exc:
                        assert "TASK-001 has no scope" in str(exc), str(exc)
                    else:
                        raise AssertionError(out.getvalue())
                    assert "parallel ok" not in out.getvalue()
                    assert tasks.parallel(project, ["TASK-001", "TASK-002"]) == ["TASK-001 has no scope"]
                    assert tasks.step(project, "TASK-001", "next") == 0  # coordinator
                    assert tasks.step(project, "TASK-001", "done") == 0
                    assert tasks.step(project, "TASK-001", "next") == 0  # read role
                    assert tasks.step(project, "TASK-001", "done") == 0
                    before = task.read_text(encoding="utf-8")
                    for invoke in (lambda: tasks.step(project, "TASK-001", "next"),
                                   lambda: omi.app.cli.dispatch(["run", "writer", "TASK-001", "--po", "approved"])):
                        try:
                            invoke()
                        except SystemExit as exc:
                            assert "TASK-001 has no scope" in str(exc), str(exc)
                        else:
                            raise AssertionError("write without scope allowed")
                        assert task.read_text(encoding="utf-8") == before
                    run.assert_not_called()
                    try:
                        omi.app.cli.dispatch(["run", "reader", "TASK-001"])
                    except SystemExit as exc:
                        assert exc.code == 0
                    run.assert_called_once()
                    run.reset_mock()
                task.write_text("---\nid: TASK-001\nstatus: planned\nscope: src/**\n---\n", encoding="utf-8")
                assert tasks.run_gate(project, "TASK-001", None) is None
    assert len(Path(tasks.__file__).read_text(encoding="utf-8").splitlines()) <= 600


def test_parallel():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / ".omi" / "tasks").mkdir(parents=True)

        def task(n, status, scope, depends=""):
            (root / ".omi" / "tasks" / f"TASK-{n}.md").write_text(
                f"---\nstatus: {status}\nscope: {scope}\ndepends: {depends}\n---\n")
        task("001", "planned", "src/a/**, tests/a.py")
        task("002", "planned", "src/b/**")
        task("003", "planned", "src/**")
        task("004", "done", "docs/**")
        task("005", "planned", "docs/x", "TASK-002")
        task("006", "planned", "docs/y", "TASK-005")
        assert omi.project.tasks.parallel(root, ["TASK-001", "TASK-002"]) == []
        out = omi.project.tasks.parallel(root, ["TASK-001", "TASK-003"])
        assert len(out) == 1 and "src/a/**" in out[0] and "src/**" in out[0]
        assert omi.project.tasks.parallel(root, ["TASK-002", "TASK-006"]) == ["TASK-006 depends on TASK-002"]
        assert "status done" in omi.project.tasks.parallel(root, ["TASK-001", "TASK-004"])[0]
        assert not omi.project.tasks.globs_overlap("src/ab/**", "src/a/**") and omi.project.tasks.globs_overlap("src/a*", "src/ab/x")
        assert omi.project.tasks.parallel(root, ["TASK-001", "TASK-002", "TASK-001"]) == ["TASK-001: duplicate id"]
        # TASK-251: three tasks on different modules that all list tests/** and the generated files run together
        for n, mod in (("011", "run"), ("012", "scope"), ("013", "board/data")):
            task(n, "planned", f"src/omi/{mod}.py, tests/**, src/omi/template_shas.json, src/omi/template/dot-omi/workflows/CATALOG.md")
        trio = ["TASK-011", "TASK-012", "TASK-013"]
        assert len(omi.project.tasks.parallel(root, trio)) == 9, "without config every shared path overlaps"
        (root / ".omi" / "config.json").write_text(json.dumps({
            "generated": ["src/omi/template_shas.json", "src/omi/template/dot-omi/*/CATALOG.md"], "parallel_shared": ["tests/**"]}))
        assert omi.project.tasks.parallel(root, trio) == []
        task("014", "planned", "src/omi/run.py, docs/x.md")
        assert omi.project.tasks.parallel(root, ["TASK-011", "TASK-014"]) == [
            "TASK-011 and TASK-014 scopes overlap: src/omi/run.py vs src/omi/run.py"], "a real module clash still blocks"
        (root / ".omi" / "config.json").unlink()
        real, realmc = omi.common.core.task_worktrees, omi.common.core.main_checkout
        omi.common.core.main_checkout = lambda _: root
        class Out(io.StringIO):
            def reconfigure(self, **kw): pass
        out = Out()
        realout = sys.stdout
        try:
            omi.common.core.task_worktrees = lambda r: {}
            sys.stdout = out
            omi.app.cli.main(["parallel", "TASK-001", "TASK-002"])
            assert out.getvalue().strip() == "parallel ok: TASK-001 TASK-002"
            out.truncate(0)
            omi.app.cli.main(["parallel", "TASK-001"])
            assert "parallel <TASK-ID>" in out.getvalue()
            try:
                omi.app.cli.main(["parallel", "TASK-001", "TASK-003"])
                assert False
            except SystemExit as e:
                assert e.code != 0 and "src/a/**" in str(e.code)
        finally:
            sys.stdout = realout
            omi.common.core.task_worktrees, omi.common.core.main_checkout = real, realmc
    assert omi.worker.docker.container_name("role", "TASK-001") != omi.worker.docker.container_name("role", "TASK-002")
    real = omi.common.core.git
    omi.common.core.git = lambda *a: ("worktree /r\nbranch refs/heads/main\n\nworktree /w1\nbranch refs/heads/task/TASK-A\n\n"
                          "worktree /w2\nbranch refs/heads/task/TASK-B\n")
    try:
        assert omi.common.core.task_worktrees(Path("/r")) == {"TASK-A": "/w1", "TASK-B": "/w2"}
    finally:
        omi.common.core.git = real
    with tempfile.TemporaryDirectory() as d:
        a, b = Path(d) / "a.md", Path(d) / "b.md"
        a.write_text("# t\n"), b.write_text("# t\n")
        omi.project.tasks.record_usage(a, "r", "m", None, (1, 2, 3), 4)
        assert "| r | m |" in a.read_text() and b.read_text() == "# t\n"


def test_auto_accept():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve()
        with patch("sys.stdout", io.StringIO()):
            omi.setup.upgrade.init(root)
        task = root / ".omi" / "tasks" / "TASK-110.md"
        with patch("omi.project.tasks.commit_task_file"), patch("omi.common.core.task_worktrees", return_value={}), \
                patch("sys.stdout", io.StringIO()):
            def run(wid, verdict, extra="", steps=""):
                done = "".join(f"- {st['id']} done 2026-10-31 10:00\n" for st in omi.project.workflows.get_workflow(root, wid)[:-1])
                usage = f"\n## Usage\n| role | model | tokens | verdict |\n|---|---|---|---|\n| omi-agent-reviewer | m | 1 | {verdict} |\n{extra}" if verdict else ""
                task.write_text(f"---\nid: TASK-110\nworkflow: {wid}\nstatus: in-progress\nstep: accept\n---\n"
                                "## Acceptance criteria\n- [x] ok\n\n## Steps\n" + done + f"- accept started 2026-10-31 10:03\n{steps}{usage}", encoding="utf-8")
                return omi.project.tasks.step(root, "TASK-110", "done")

            for verdict in ("", "FAIL"):
                try:
                    run("omi-flow-feature", verdict)
                except SystemExit as exc:
                    assert "auto gate" in str(exc), str(exc)
                else:
                    raise AssertionError("auto accept without PASS")
            qa = lambda v: f"| omi-agent-qa-tester | m | 1 | {v} |\n"  # noqa: E731
            for extra in ("", qa("FAIL")):  # feature-ui: a missing or failed qa blocks even with a reviewer PASS
                try:
                    run("omi-flow-feature-ui", "PASS", extra)
                except SystemExit as exc:
                    assert "omi-agent-qa-tester" in str(exc), str(exc)
                else:
                    raise AssertionError("auto accept despite qa")
            assert run("omi-flow-feature-ui", "PASS", qa("PASS")) == 0
            assert run("omi-flow-feature", "PASS") == 0
            assert "Auto accept: review PASS\n- accept done" in task.read_text(encoding="utf-8")
            # a `done --po` review override carries through the auto gate; one for another step or round does not
            override = "- PO review override review: host evidence accepted\n"
            assert run("omi-flow-feature", "FAIL", steps=override) == 0
            assert "Auto accept: review PASS\n- accept done" in task.read_text(encoding="utf-8")
            try:
                run("omi-flow-feature", "FAIL", steps="- PO review override build: nope\n")
            except SystemExit as exc:
                assert "auto gate" in str(exc), str(exc)
            else:
                raise AssertionError("auto accept with an override for another step")
        for wid in ("omi-flow-feature", "omi-flow-feature-ui", "omi-flow-bugfix", "omi-flow-refactor"):
            assert omi.project.workflows.get_workflow(root, wid)[-1]["gate"] == "auto", wid
        assert omi.project.workflows.get_workflow(root, "omi-flow-feature-sensitive")[-1]["gate"] == "auto"


def test_status_outdated_one_hint_and_silent_stale_check():
    def status_text(root):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), patch("omi.setup.install.stale_user_integration", return_value=False), \
                patch("omi.project.improve.open_count", return_value=0), patch("omi.worker.docker.full_volumes", return_value=[]):
            omi.app.cli.status(root)
        return buf.getvalue()

    with tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve()
        with patch("sys.stdout", io.StringIO()):
            omi.setup.upgrade.init(root)
        manifest = json.loads((root / ".omi" / "manifest.json").read_text(encoding="utf-8"))
        rel = next(r for r in manifest["files"] if r.startswith(".omi/agents/"))
        manifest["files"][rel] = omi.setup.upgrade.norm_sha(b"older template")  # the shipped template moved on
        (root / ".omi" / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (root / rel).write_bytes(b"older template")
        (root / ".omi" / "version").write_text("0.0.1\n", encoding="utf-8")
        assert status_text(root).count("upgrade --apply") == 1
        (root / ".omi" / "version").write_text(omi.common.core.version() + "\n", encoding="utf-8")
        assert status_text(root).count("upgrade --apply") == 1  # same version: the stale-file hint is the only one
        other = root / "other.md"
        other.write_bytes(b"older template")
        (root / rel).unlink()
        try:
            (root / rel).symlink_to(other)
        except OSError:
            return  # no symlinks on this host
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            omi.setup.upgrade.stale_template_hint(root)
        assert "skip (symlink)" not in out.getvalue(), out.getvalue()


def test_review_prompts_and_host_test_docs():
    tpl = omi.common.core.TEMPLATE
    for name in ("omi-agent-reviewer", "omi-agent-security-reviewer"):
        text = (tpl / "dot-omi/agents" / f"{name}.md").read_text(encoding="utf-8")
        for word in ("Windows", "Ctrl-C", "file permissions", "secrets in outputs", "NEW-SEVERE", "Known issues"):
            assert word in text, (name, word)
    skill = (tpl / "dot-claude/skills/omi-task/SKILL.md").read_text(encoding="utf-8")
    assert skill.index("omi host-test <ID>") > skill.index("commit on the host") and "HOST TEST FAILED" in skill
    assert "Trust boundary" in (tpl / "AGENTS.md").read_text(encoding="utf-8")
    assert json.loads((tpl / "dot-omi/config.json").read_text(encoding="utf-8"))["host_test"] == ""


def test_review_test_in_worker():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve() / "repo"
        root.mkdir()
        git(root, "init", "-b", "development")
        (root / ".omi").mkdir()
        git(root, "commit", "--allow-empty", "-m", "init")
        wt = Path(d).resolve() / "wt"
        git(root, "worktree", "add", "-b", "task/TASK-1", str(wt))
        task = wt / ".omi" / "tasks" / "TASK-1.md"
        task.parent.mkdir(parents=True)
        task.write_text("---\nid: TASK-1\n---\n## Steps\n- build done 2026-11-03 10:00\n", encoding="utf-8")
        git(wt, "add", "-A")
        git(wt, "commit", "-m", "work")
        sha = omi.common.core.git(wt, "rev-parse", "--short=7", "HEAD")
        cfg = root / ".omi" / "config.json"
        assert not omi.worker.hooks.review_test_in_worker(root)
        cfg.write_text(json.dumps({"test": "make check", "review_test_in_worker": False}), encoding="utf-8")
        assert not omi.worker.hooks.review_test_in_worker(root)
        calls = []

        def checks(rc=0):
            calls.clear()
            with patch.object(omi.worker.hooks, "run_test", lambda *a: calls.append(a) or (rc, "boom\n")), \
                    patch.object(omi.project.scope, "out_of_scope", lambda *a, **k: []), \
                    patch.object(omi.project.catalogs, "check_all_skills", lambda wt: None), \
                    patch("sys.stdout", io.StringIO()) as out:
                return omi.worker.run.deterministic_checks(wt, root, "TASK-1"), out.getvalue()

        # host mode (default): the worker image is not used
        # the host run gets OMI_QUIET=1 (tests/test_omi.py prints only failures and a summary line)
        with patch.object(omi.worker.run, "test_command", lambda *a: [sys.executable, "-c", "import os, sys; sys.exit(os.environ.get('OMI_QUIET') != '1')"]):
            with patch.object(omi.worker.hooks, "run_test", lambda *a: calls.append(a)):
                with patch.object(omi.project.scope, "out_of_scope", lambda *a, **k: []), \
                        patch.object(omi.project.catalogs, "check_all_skills", lambda wt: None):
                    assert omi.worker.run.deterministic_checks(wt, root, "TASK-1") == [] and not calls
        # worker mode: the configured command runs in the image
        cfg.write_text(json.dumps({"test": "make check", "review_test_in_worker": True}), encoding="utf-8")
        assert omi.worker.hooks.review_test_in_worker(root)
        assert checks() == ([], "") and calls[0][2] == "OMI_QUIET=1 make check"
        problems, _ = checks(1)
        assert len(problems) == 1 and problems[0].startswith("tests failed:") and "boom" in problems[0], problems
        # a hook pass recorded for this HEAD: no rerun, reuse is recorded
        text = task.read_text(encoding="utf-8")
        task.write_text(text + f"\n## Reports\n2026-11-08 18:39 hook post-run passed on {sha}:\n> ok\n", encoding="utf-8")
        problems, out = checks(1)
        assert problems == [] and not calls and f"reused: hook post-run on {sha}" in out
        assert f"reused: hook post-run on {sha}" in task.read_text(encoding="utf-8")
        # host-test reuses it too and records the PASS row the gate reads
        cfg.write_text(json.dumps({"host_test": "exit 1", "review_test_in_worker": True}), encoding="utf-8")
        with patch("sys.stdout", io.StringIO()) as out:
            assert omi.worker.run.host_test(omi.state.resolve.Project(root, root), "TASK-1") == 0
        assert "reused: hook post-run on" in out.getvalue()
        tasks.host_test_gate(root, "TASK-1", task.read_text(encoding="utf-8"), sha)
        # a pass on another HEAD, or worker mode off, is not reused
        assert not omi.worker.hooks.hook_passed_on(task.read_text(encoding="utf-8"), "abcdef0")
        cfg.write_text(json.dumps({"test": "make check"}), encoding="utf-8")
        with patch.object(omi.worker.run, "test_command", lambda *a: [sys.executable, "-c", "pass"]):
            assert checks()[0] == [] and not calls
        # hook_note records the commit on a pass only
        omi.worker.hooks.hook_note(task, "post-run", (1, ""), "1234567")
        omi.worker.hooks.hook_note(task, "post-run", (0, ""), "7654321")
        body = task.read_text(encoding="utf-8")
        assert "hook post-run passed on 7654321:" in body and "1234567" not in body
    # omi init: the worker mode is on for stacks the host cannot run, off otherwise
    for marker, want in (("package.json", True), ("docker", True), (None, False)):
        with tempfile.TemporaryDirectory() as d:
            if marker == "docker":
                (Path(d) / marker).mkdir()
            elif marker:
                (Path(d) / marker).write_text("{}")
            with patch("sys.stdout", io.StringIO()):
                omi.setup.upgrade.init(d)
            assert json.loads((Path(d) / ".omi" / "config.json").read_text(encoding="utf-8"))["review_test_in_worker"] is want, marker


def test_host_test():
    row = lambda role, v: f"| {role} | m | high | 1 | 1 | 1 | 1s | - | {v} |\n"
    head = "\n## Usage\n| role | model | effort | input | output | cache | duration | skills read | verdict |\n|---|---|---|---|---|---|---|---|---|\n"
    with tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve() / "repo"
        root.mkdir()
        git(root, "init", "-b", "development")
        (root / ".omi").mkdir()
        git(root, "commit", "--allow-empty", "-m", "init")
        wt = Path(d).resolve() / "wt"
        git(root, "worktree", "add", "-b", "task/TASK-1", str(wt))
        task = wt / ".omi" / "tasks" / "TASK-1.md"
        task.parent.mkdir(parents=True)
        task.write_text("---\nid: TASK-1\n---\n## Steps\n- build done 2026-11-03 10:00\n", encoding="utf-8")
        (wt / "code.py").write_text("x = 1\n", encoding="utf-8")
        git(wt, "add", "-A")
        git(wt, "commit", "-m", "work")
        sha = omi.common.core.git(wt, "rev-parse", "--short=7", "HEAD")
        project = omi.state.resolve.Project(root, root)
        cfg = root / ".omi" / "config.json"
        python = sys.executable.replace("\\", "/")

        def host_test(command):
            cfg.write_text(json.dumps({"host_test": command}), encoding="utf-8")
            with patch("sys.stdout", io.StringIO()) as out:
                return omi.worker.run.host_test(project, "TASK-1"), out.getvalue()

        def gate(text=None):
            tasks.host_test_gate(root, "TASK-1", task.read_text(encoding="utf-8") if text is None else text, sha)

        def refuses(word, text=None):
            try:
                gate(text)
            except SystemExit as exc:
                assert word in str(exc), str(exc)
                return
            raise AssertionError(f"should refuse: {word}")

        # empty host_test: skipped, no row, the reviewer gate is open
        code, out = host_test("")
        assert code == 0 and "skipped" in out and "## Usage" not in task.read_text(encoding="utf-8")
        gate()
        # uncommitted code: refused, no row
        (wt / "code.py").write_text("x = 2\n", encoding="utf-8")
        try:
            host_test("x")
        except SystemExit as exc:
            assert "uncommitted" in str(exc) and "## Usage" not in task.read_text(encoding="utf-8")
        else:
            raise AssertionError("dirty worktree must be refused")
        real_git = omi.common.core.git
        with patch("omi.common.core.git", side_effect=lambda cwd, *a: None if a[0] == "status" else real_git(cwd, *a)):  # status fails: not "clean"
            try:
                host_test("x")
            except SystemExit as exc:
                assert "cannot read the git status" in str(exc) and "## Usage" not in task.read_text(encoding="utf-8")
            else:
                raise AssertionError("a failed git status must be refused")
        git(wt, "commit", "-am", "more")
        sha = omi.common.core.git(wt, "rev-parse", "--short=7", "HEAD")
        # set: the reviewer gate refuses while no host test ran for this commit
        cfg.write_text(json.dumps({"host_test": "x"}), encoding="utf-8")
        refuses("HOST TEST MISSING")
        refuses("HOST TEST MISSING", head + row("host-test", "PASS 0000000"))
        # a pass is recorded and opens the gate
        code, out = host_test(f'"{python}" -c "print(1)"')
        assert code == 0 and f"HOST TEST PASSED {sha}" in out
        assert tasks.usage_rows(task.read_text(encoding="utf-8"))[-1][0::8] == ["host-test", f"PASS {sha}"]
        cfg.write_text(json.dumps({"host_test": "x"}), encoding="utf-8")
        gate()
        # a failure prints the output tail, exits non-zero, closes the gate and counts as a fix round
        code, out = host_test(f'"{python}" -c "import sys;print(\'boom\');sys.exit(3)"')
        assert code == 1 and out.startswith("HOST TEST FAILED") and "boom" in out
        text = task.read_text(encoding="utf-8")
        assert tasks.failed_rounds(text) == 1
        cfg.write_text(json.dumps({"host_test": "x"}), encoding="utf-8")
        # the same failing commit run twice counts once; another sha counts again; review FAIL rows each count
        assert tasks.failed_rounds(text + row("host-test", "FAIL " + sha)) == 1
        assert tasks.failed_rounds(text + row("host-test", "FAIL 0000000")) == 2
        assert tasks.failed_rounds(text + row("omi-agent-reviewer", "FAIL a") * 2) == 3
        refuses("HOST TEST FAILED")
        text = text + row("omi-agent-reviewer", "FAIL abc1234")
        try:
            tasks.round_gate(root, "TASK-1", text, None)
        except SystemExit as exc:
            assert "ROUND LIMIT" in str(exc) and "failed 2 review rounds" in str(exc)
        else:
            raise AssertionError("host-test FAIL must count toward max_fix_rounds")


def test_pattern_line_shape():
    ok = "Pattern: Strategy - two pricing rules vary at runtime - an if/else cannot add a third without edits"
    for bad in ("Pattern: Strategy", "Pattern: Strategy - force", "Pattern: Strategy -  - why", "Pattern:  - force - why"):
        assert omi.project.structure.bad_pattern_lines(bad) == [bad], bad
    assert omi.project.structure.bad_pattern_lines(ok + "\nPattern: A - b - c - d") == []
    with tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve()
        with patch("sys.stdout", io.StringIO()):
            omi.setup.upgrade.init(root)
        task = root / ".omi" / "tasks" / "TASK-111.md"
        with patch("omi.project.tasks.commit_task_file"), patch("omi.common.core.task_worktrees", return_value={}), \
                patch("sys.stdout", io.StringIO()):
            def done(line):
                task.write_text("---\nid: TASK-111\nworkflow: omi-flow-feature\nstatus: in-progress\nstep: build\n---\n"
                                f"## Design\n{line}\n\n## Steps\n- plan done 2026-10-31 10:00\n- build started 2026-10-31 10:01\n", encoding="utf-8")
                return omi.project.tasks.step(root, "TASK-111", "done")

            try:
                done("Pattern: Strategy - only a name")
            except SystemExit as exc:
                assert "malformed `Pattern: Strategy - only a name`" in str(exc) and "Nothing changed" in str(exc), str(exc)
                assert "build done" not in task.read_text(encoding="utf-8")
            else:
                raise AssertionError("malformed Pattern line accepted")
            assert done(ok) == 0 and "build done" in task.read_text(encoding="utf-8")


def test_file_plan_lines():
    """TASK-251: a note after the path is read; unreadable `- edit|create` lines stop the architect step at once, all listed."""
    scope = omi.project.scope
    plan = ("## File plan\n- edit src/a.py (domain)\n- edit src/b.py (domain): add the rule\n- create `src/c.py` (adapter): new\n"
            "- edit src/{d,e}.go (x)\n- edit src/f.py src/g.py\n- create src/h.py\n\n## Next\n- edit not/a/plan.py\n")
    assert scope.file_plan(plan) == {"src/a.py", "src/b.py", "src/c.py", "src/h.py"}
    assert scope.plan_line_errors(plan) == ["- edit src/{d,e}.go (x)", "- edit src/f.py src/g.py"]
    assert scope.module_tests(["src/omi/worker/run.py", "src/x/**", "tests/test_y.py", "web/app.ts"]) == ["tests/test_run.py"]
    with tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve()
        with patch("sys.stdout", io.StringIO()):
            omi.setup.upgrade.init(root)
        task = root / ".omi" / "tasks" / "TASK-112.md"
        with patch("omi.project.tasks.commit_task_file"), patch("omi.common.core.task_worktrees", return_value={}), \
                patch("sys.stdout", io.StringIO()):
            def done(body):
                task.write_text("---\nid: TASK-112\nworkflow: omi-flow-feature-sensitive\nstatus: in-progress\nstep: architect\n---\n"
                                f"{body}\n## Steps\n- plan done 2026-10-31 10:00\n- architect started 2026-10-31 10:01\n", encoding="utf-8")
                return omi.project.tasks.step(root, "TASK-112", "done")
            try:
                done(plan)
            except SystemExit as exc:
                assert "- edit src/{d,e}.go (x)" in str(exc) and "- edit src/f.py src/g.py" in str(exc) and "Nothing changed" in str(exc)
            else:
                raise AssertionError("unreadable File plan lines accepted at the architect step")
            assert done("## File plan\n- edit src/a.py (domain): ok\n") == 0 and "architect done" in task.read_text(encoding="utf-8")


def test_review_stage_steps_and_lanes():
    """TASK-257: staged review steps count verdicts from the stage start, a stage FAIL is one round; lane warnings and task size."""
    W = omi.project.workflows
    with tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve()
        with patch("sys.stdout", io.StringIO()):
            omi.setup.upgrade.init(root)
        steps = W.get_workflow(root, "omi-flow-feature-sensitive")
        assert [s["id"] for s in W.stage_of(steps, "security")] == ["review", "security"]
        assert [s["id"] for s in W.stage_of(steps, "build")] == ["build"] and W.stage_of(steps, "nope") == []
        task = root / ".omi" / "tasks" / "TASK-120.md"
        row = lambda r, v: f"| {r} | m | 1 | {v} |\n"  # noqa: E731
        rev, sec = "omi-agent-reviewer", "omi-agent-security-reviewer"
        task.write_text("---\nid: TASK-120\nworkflow: omi-flow-feature-sensitive\nstatus: in-progress\nscope: src/a.py\nstep: build\n---\n"
                        "## Steps\n- plan done 2026-11-08 09:00\n- architect done 2026-11-08 09:30\n- build started 2026-11-08 10:00\n"
                        "\n## Usage\n| role | model | tokens | verdict |\n|---|---|---|---|\n" + row(sec, "FAIL aaaaaaa"), encoding="utf-8")
        with patch("omi.project.tasks.commit_task_file"), patch("omi.common.core.task_worktrees", return_value={}), patch("sys.stdout", io.StringIO()):
            go = lambda action: omi.project.tasks.step(root, "TASK-120", action)  # noqa: E731
            assert go("done") == 0 and go("next") == 0
            log = task.read_text(encoding="utf-8")
            assert re.search(r"^- review started .* \(verdicts: 0\)$", log, re.M) and re.search(r"^- security staged .* \(verdicts: 1\)$", log, re.M), log
            with task.open("a", encoding="utf-8") as f:  # both reviewers ran together on bbbbbbb
                f.write(row(rev, "PASS bbbbbbb") + row(sec, "PASS bbbbbbb"))
            assert go("done") == 0 and go("next") == 0
            assert re.search(r"^- security started .* \(verdicts: 1\)$", task.read_text(encoding="utf-8"), re.M)
            assert go("done") == 0, "the security PASS from the stage counts for the security step"
    usage = "\n## Usage\n| role | model | tokens | verdict |\n|---|---|---|---|\n"
    text = usage + row(rev, "FAIL abc1234") + row(sec, "FAIL abc1234 root:new")
    assert tasks.failed_rounds(text) == 1, "a stage failing one commit is one round"
    assert tasks.failed_rounds(text + row(rev, "FAIL abc1234")) == 2 and tasks.failed_rounds(text + row(sec, "FAIL def5678")) == 2
    # stage validation: only read-only review steps, listed one after another
    with tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve()
        with patch("sys.stdout", io.StringIO()):
            omi.setup.upgrade.init(root)
        f = root / ".omi" / "workflows" / "omi-flow-zz.md"
        step = lambda sid, role, gate, stage: f"- id: {sid} | role: {role} | skills: | input: i | output: o | gate: {gate} | stop: s | stage: {stage}\n"  # noqa: E731
        for body, problem in ((step("build", "omi-agent-engineer", "none", "x") + step("review", rev, "review", "x"), "only read-only review steps"),
                              (step("review", rev, "review", "x") + step("qa", "omi-agent-qa-tester", "none", "") + step("security", sec, "review", "x"), "one after another"),
                              (step("review", rev, "review", "x") + step("security", sec, "review", "x"), None)):
            f.write_text("---\nid: omi-flow-zz\nsummary: s\nsteps:\n" + body + "---\nx\n", encoding="utf-8")
            errs = W.validate_workflow(root, f)
            assert (problem is None and not errs) or any(problem in e for e in errs), (problem, errs)
    # task size and lane warnings
    assert W.task_size({"scope": "src/a.py, tests/test_a.py, src/b_test.go, web/x.test.ts, test_c.py"}) == 1
    assert W.task_size({"scope": "src/**"}) is None and W.task_size({}) is None
    assert W.task_size({"scope": "src/**", "_text": "\n## File plan\n- edit src/a.py (x): y\n- create tests/test_a.py (t)\n"}) == 1
    for m, warn in (({"type": "bug", "workflow": "omi-flow-bugfix", "scope": "src/a.py, tests/test_a.py"}, "consider the fast lane omi-flow-bugfix-fast"),
                    ({"type": "bug", "workflow": "omi-flow-bugfix-fast", "scope": ".github/workflows/ci.yml"}, "omi-flow-bugfix-fast on sensitive scope (.github)"),
                    ({"type": "bug", "workflow": "omi-flow-bugfix", "scope": "a.py, b.py, c.py, d.py"}, ""),
                    ({"type": "bug", "workflow": "omi-flow-bugfix", "scope": "src/auth.py"}, ""),
                    ({"type": "task", "workflow": "omi-flow-bugfix", "scope": "src/a.py"}, ""),
                    ({"type": "bug", "workflow": "omi-flow-bugfix-fast", "scope": "src/a.py"}, "")):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            W.warn_lane(m)
        assert (warn in out.getvalue()) if warn else out.getvalue() == "", (m, out.getvalue())
    with tempfile.TemporaryDirectory() as d:  # `omi step` warns when the plan step closes
        root = Path(d).resolve()
        with patch("sys.stdout", io.StringIO()):
            omi.setup.upgrade.init(root)
        (root / ".omi" / "tasks" / "TASK-121.md").write_text(
            "---\nid: TASK-121\ntype: bug\nworkflow: omi-flow-bugfix\nstatus: in-progress\nscope: src/a.py\nskills: [omi-skill-lean-implementation]\n"
            "step: plan\n---\n## Steps\n- plan started 2026-11-08 10:00\n", encoding="utf-8")
        with patch("omi.project.tasks.commit_task_file"), patch("omi.common.core.task_worktrees", return_value={}), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            assert omi.project.tasks.step(root, "TASK-121", "done") == 0 and omi.project.tasks.step(root, "TASK-121", "next") == 0
        assert "WARN: bug touching 1 non-test file(s) - consider the fast lane omi-flow-bugfix-fast" in out.getvalue(), out.getvalue()


def test_write_step_role_must_match_task_role():
    """TASK-246: step next, dispatch and skills check refuse a write step whose role differs from the task `role:`."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        with contextlib.redirect_stdout(io.StringIO()):
            omi.setup.upgrade.init(root)
        wf = omi.project.workflows
        wf.check_role(root, {"id": "TASK-1", "role": "omi-agent-engineer"}, "omi-agent-engineer")
        wf.check_role(root, {"id": "TASK-1", "role": "omi-agent-designer-ui"}, "omi-agent-reviewer")  # read role: fine
        wf.check_role(root, {"id": "TASK-1"}, "omi-agent-devops")  # no task role: the step decides
        for bad in ({"id": "TASK-1", "role": "omi-agent-designer-ui"}, {"id": "TASK-1", "role": "omi-agent-nobody"}):
            try:
                wf.check_role(root, bad, "omi-agent-engineer")
                raise AssertionError(f"mismatch allowed: {bad}")
            except SystemExit as exc:
                assert "TASK-1" in str(exc) or "omi-agent-nobody" in str(exc), exc
    assert "depends" in tasks.FRONT_OWNED  # Coordinator-owned: a run never changes it


def main():
    test_write_step_role_must_match_task_role()
    test_review_stage_steps_and_lanes()
    test_file_plan_lines()
    test_pattern_line_shape()
    test_hierarchy()
    test_tree_table()
    test_tree_logic_lives_in_tree_module()
    test_hierarchy_status_and_run()
    test_plan_status()
    test_step_approve_reopen()
    test_auto_accept()
    test_status_outdated_one_hint_and_silent_stale_check()
    test_reopen_last_write_step()
    test_step_back_to()
    test_round_limit_and_replan()
    test_note()
    test_append_note_strips_control_bytes()
    test_host_test()
    test_review_test_in_worker()
    test_review_prompts_and_host_test_docs()
    test_warn_skills_empty()
    test_task_skill_step_commands()
    test_missing_scope()
    test_parallel()
    test_workflows()
    test_roles()
    test_task_flow_commit_scope_sync_warn()
    test_type_validation_and_workflow_warning()


if __name__ == "__main__":
    main()
