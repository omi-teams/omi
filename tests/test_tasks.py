import io
import re
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
from helpers import omi, git


def test_roles():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        saved, sys.stdout = sys.stdout, io.StringIO()
        try:
            omi.upgrade.init(root)
            omi.catalogs.agents_catalog(root)
        finally:
            sys.stdout = saved
        assert not (root / ".claude" / "agents").exists()
        cat = (root / ".omi" / "agents" / "CATALOG.md").read_text()
        assert "- omi-agent-engineer (write, sonnet/medium):" in cat and "- omi-agent-reviewer (read, sonnet/medium):" in cat
        assert omi.catalogs.get_role(root, "omi-agent-reviewer")["access"] == "read"
        try:
            omi.catalogs.get_role(root, "ghost")
        except SystemExit as e:
            assert "unknown role" in str(e)
        else:
            raise AssertionError("unknown role accepted")
        try:
            omi.catalogs.task_skill_ids(root, {"role": "ghost"})
        except SystemExit as e:
            assert "ghost" in str(e)
        else:
            raise AssertionError("unknown task role accepted")
        assert omi.catalogs.task_skill_ids(root, {"skills": "[a]"}) == ["a"]
        (root / ".omi" / "agents" / "omi-agent-reviewer.md").write_text("---\nrole: omi-agent-reviewer\nmodel: sonnet\neffort: low\naccess: read\n"
                                                           "skills: [x, a]\nsummary: s\n---\nbody")
        assert omi.catalogs.task_skill_ids(root, {"role": "omi-agent-reviewer", "skills": "[a, b]"}) == ["x", "a", "b"]
        (root / ".omi" / "agents" / "reviewer.md").write_text("---\nrole: reviewer\nmodel: sonnet\neffort: low\naccess: read\n"
                                                           "skills: []\nsummary: s\n---\nbody")
        try:
            omi.catalogs.load_roles(root)
        except SystemExit as e:
            assert "must start with `omi-agent-`" in str(e) or "differs from file name" in str(e), str(e)
        else:
            raise AssertionError("role without omi-agent- prefix accepted")
        (root / ".omi" / "agents" / "reviewer.md").unlink()
        assert "tests/test_omi.py" not in omi.run.test_command(root, root)[-1]
    a = omi.tools.codex_cmd("---\n---\nbody", "t.md", "claude-sonnet-5-5", "low")
    assert a[:8] == ["codex", "exec", "-c", "project_doc_max_bytes=0", "-m", "claude-sonnet-5-5", "-c", "model_reasoning_effort=low"] and "/work/t.md" in a[-1]
    assert "git rm" in a[-1] and "rm` may be refused" in a[-1]
    # claude's command never gets the codex option
    assert "project_doc_max_bytes=0" not in omi.tools.engineer_cmd("---\n---\nbody", "t.md", "claude-sonnet-5-5", "low", "")


def test_task_flow_commit_scope_sync_warn():
    with tempfile.TemporaryDirectory() as d:
        main = Path(d).resolve() / "main"
        omi.upgrade.init(main)
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
            assert omi.tasks.step(main, "TASK-001", "next") == 0
        finally:
            sys.stdout = saved
        first = omi.core.parse(task.read_text(encoding="utf-8"))["step"]
        assert omi.core.git(main, "log", "-1", "--format=%s") == f"chore(TASK-001): step {first} next"
        assert omi.core.git(main, "show", "--name-only", "--format=", "HEAD") == ".omi/tasks/TASK-001.md"
        assert "M  .omi/decisions.md" in omi.core.git(main, "status", "--porcelain")
        assert "?? other.txt" in omi.core.git(main, "status", "--porcelain")
        for action, why in (("done", None), ("skip", "n/a")):
            sys.stdout, saved = io.StringIO(), sys.stdout
            try:
                if action == "done":
                    assert omi.tasks.step(main, "TASK-001", "done") == 0
                else:
                    assert omi.tasks.step(main, "TASK-001", "next") == 0
                    assert omi.tasks.step(main, "TASK-001", "skip", why=why) == 0
            finally:
                sys.stdout = saved
            cur = omi.core.parse(task.read_text(encoding="utf-8"))["step"]
            assert omi.core.git(main, "log", "-1", "--format=%s") == f"chore(TASK-001): step {cur} {action}"
            assert omi.core.git(main, "show", "--name-only", "--format=", "HEAD") == ".omi/tasks/TASK-001.md"
        # nothing changed: no new commit
        head = omi.core.git(main, "rev-parse", "HEAD")
        omi.tasks.commit_task_file(main, task, "chore: noop")
        assert omi.core.git(main, "rev-parse", "HEAD") == head
        assert "M  .omi/decisions.md" in omi.core.git(main, "status", "--porcelain")
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
            omi.tasks.sync_scope(wt, wt / ".omi" / "tasks" / "TASK-001.md", "TASK-001")
            out = sys.stdout.getvalue()
            omi.tasks.sync_scope(wt, wt / ".omi" / "tasks" / "TASK-001.md", "TASK-001")
            again = sys.stdout.getvalue()
        finally:
            sys.stdout = saved
        assert "SCOPE SYNCED: src/**, docs/**" in out and again == out
        synced = (wt / ".omi" / "tasks" / "TASK-001.md").read_text(encoding="utf-8")
        assert "scope: src/**, docs/**" in synced and "- local line" in synced
        # #4: with a worktree the step lands in the worktree's task file, development gets no commit
        head = omi.core.git(main, "rev-parse", "HEAD")
        sys.stdout, saved = io.StringIO(), sys.stdout
        try:
            assert omi.tasks.step(main, "TASK-001", "next") == 0
        finally:
            sys.stdout = saved
        assert omi.core.git(main, "rev-parse", "HEAD") == head
        assert omi.core.parse((wt / ".omi" / "tasks" / "TASK-001.md").read_text(encoding="utf-8")).get("step") != \
            omi.core.parse(task.read_text(encoding="utf-8")).get("step")
        # sensitive-scope warning
        m = {"scope": "db/migrations/**, src/**", "workflow": "omi-flow-feature"}
        sys.stdout, saved = io.StringIO(), sys.stdout
        try:
            omi.tasks.warn_sensitive(m)
            warned = sys.stdout.getvalue()
            sys.stdout.truncate(0)
            omi.tasks.warn_sensitive({**m, "workflow": "omi-flow-feature-sensitive"})
            quiet = sys.stdout.getvalue()
        finally:
            sys.stdout = saved
        assert warned == "WARN: scope touches migrations - consider omi-flow-feature-sensitive\n" and not quiet
        for glob, hit in (("src/authors/**", False), ("src/oauth/**", False), ("src/auth/**", True), ("app/secrets/*", True),
                          (".github/workflows/**", True), ("src/**", False)):
            sys.stdout, saved = io.StringIO(), sys.stdout
            try:
                omi.tasks.warn_sensitive({"scope": glob, "workflow": "omi-flow-feature"})
                assert bool(sys.stdout.getvalue()) == hit, glob
            finally:
                sys.stdout = saved


def test_step_approve_reopen():
    # Exercise the same authoritative-task routing for local and detached state.
    for detached in (False, True):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            with patch("sys.stdout", io.StringIO()):
                omi.upgrade.init(root)
            code = root / "code" if detached else root
            project = omi.state.Project(root, code, detached)
            task = root / ".omi" / "tasks" / "TASK-109.md"
            commits = []
            with patch("omi.tasks.commit_task_file", side_effect=lambda *args: commits.append(args)), \
                    patch("omi.core.task_worktrees", return_value={}), patch("sys.stdout", io.StringIO()):
                def go(action, why=None):
                    return omi.tasks.step(project, "TASK-109", action, why=why)

                def refuses(action, why, message):
                    before, count = task.read_text(encoding="utf-8"), len(commits)
                    try:
                        go(action, why)
                    except SystemExit as exc:
                        assert message in str(exc), str(exc)
                    else:
                        raise AssertionError(f"{action} should fail")
                    assert task.read_text(encoding="utf-8") == before and len(commits) == count

                task.write_text("---\nid: TASK-109\nworkflow: omi-flow-feature\nstatus: in-progress\n---\n"
                                "## Acceptance criteria\n- [x] tested\n\n## Steps\n\n## Checkpoint\nDone:\n",
                                encoding="utf-8")
                refuses("approve", "yes", "no step started")
                refuses("reopen", "CI failed", "not complete")
                go("next")
                refuses("approve", "yes", "not a po gate")
                refuses("reopen", "CI failed", "running")
                go("done")
                refuses("reopen", "CI failed", "not complete")
                go("next"), go("done"), go("next"), go("done"), go("next")
                refuses("approve", None, "--why")
                refuses("approve", " \n ", "--why")
                # Verify the existing CLI --why parser reaches the new action unchanged.
                with patch("omi.state.resolve", return_value=project), patch("omi.core.main_checkout", return_value=root), \
                        patch("sys.stdout.reconfigure", create=True):
                    try:
                        omi.cli.dispatch(["step", "TASK-109", "approve", "--why", "Ship it!\nReviewed all criteria."])
                    except SystemExit as exc:
                        assert exc.code == 0
                    else:
                        raise AssertionError("CLI did not execute approve")
                text = task.read_text(encoding="utf-8")
                assert "PO approval accept: Ship it! Reviewed all criteria.\n\n## Checkpoint" in text
                assert omi.tasks.po_approved(text, "accept")
                if detached:
                    assert not commits and not code.exists()
                else:
                    assert commits[-1] == (root, task, "chore(TASK-109): step accept approve")
                go("done")
                task.write_text(omi.tasks.set_front(task.read_text(encoding="utf-8"), "status", "done"), encoding="utf-8")
                refuses("reopen", " ", "--why")
                go("reopen", "CI red\nfix required")
                text = task.read_text(encoding="utf-8")
                assert omi.core.parse(text)["step"] == "build"
                assert omi.core.parse(text)["status"] == "in-progress"
                assert re.search(r"^- workflow reopened .*: CI red fix required$", text, re.M)
                assert "PO approval accept: Ship it!" in text  # Preserve the audit trail.
                assert not omi.tasks.po_approved(text, "accept")
                assert omi.tasks.step_states(text) == {"plan": "done", "build": "started", "review": "failed", "accept": "failed"}
                if detached:
                    assert not commits
                else:
                    assert commits[-1] == (root, task, "chore(TASK-109): step build reopen")
                refuses("reopen", "again", "running")
                go("done"), go("next"), go("done"), go("next")
                refuses("done", None, "po gate")
                go("approve", "Approved after the CI fix"), go("done"), go("next")
                assert omi.tasks.po_approved(task.read_text(encoding="utf-8"), "accept")


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
        project = omi.state.Project(root, root, True)
        with patch("omi.workflows.get_workflow", return_value=steps), \
                patch("omi.catalogs.get_role", side_effect=lambda root, role: {"access": "write" if role == "omi-agent-engineer" else "read"}), \
                patch("sys.stdout", io.StringIO()):
            omi.tasks.step(project, "TASK-109", "reopen", why="CI failed")
            assert omi.core.meta(task)["step"] == "fix"
            assert omi.tasks.step_states(task.read_text(encoding="utf-8"))["build"] == "done"
            task.write_text(text, encoding="utf-8")
            for s in steps[:2]:
                s["role"] = "coordinator"
            try:
                omi.tasks.step(project, "TASK-109", "reopen", why="CI failed")
            except SystemExit as exc:
                assert "no write step" in str(exc)
            else:
                raise AssertionError("reopened workflow with no write step")
            assert task.read_text(encoding="utf-8") == text


def test_task_skill_step_commands():
    repo = Path(__file__).resolve().parents[1]
    template = omi.core.TEMPLATE / "dot-claude/skills/omi-task/SKILL.md"
    text = template.read_text(encoding="utf-8")
    assert text == (repo / ".claude/skills/omi-task/SKILL.md").read_text(encoding="utf-8")
    assert 'step <ID> approve --why "<PO\'s words>"' in text
    assert 'gh pr create --base development --head task/<ID> --title "<type>: <title> (<ID>)" --body "<one-paragraph summary of the change>"' in text
    assert "--fill" not in text
    assert 'step <ID> reopen --why "<CI failure reason>"' in text
    assert "fresh PO approval" in text


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
            omi.upgrade.init(root)
            assert (wf / "CATALOG.md").exists(), "init creates the workflows folder"
            for sid, size in (("omi-skill-a", 100), ("omi-skill-b", 100), ("omi-skill-c", 100), ("omi-skill-big", 9000),
                              ("omi-skill-h1", 7900), ("omi-skill-h2", 7900), ("omi-skill-h3", 7900), ("omi-skill-h4", 7900)):
                d = root / ".omi" / "skills" / "g" / sid
                d.mkdir(parents=True)
                (d / "SKILL.md").write_text(f"---\ndescription: use for {sid}\n---\n" + "x" * size)
            omi.catalogs.skills_catalog(root)

            def flow(name, *steps, summary="Use for demos."):
                rows = "".join(f"- {s}\n" for s in steps)
                (wf / f"{name}.md").write_text(f"---\nid: {name}\nsummary: {summary}\nsteps:\n{rows}---\nPlaybook.\n")

            ok = ("id: plan | role: coordinator | skills: | input: idea | output: task file | gate: none | stop: AC written",
                  "id: build | role: omi-agent-engineer | skills: omi-skill-a | input: task | output: diff | gate: none | stop: tests pass",
                  "id: review | role: omi-agent-reviewer | skills: | input: diff | output: verdict | gate: review | stop: PASS",
                  "id: accept | role: coordinator | skills: | input: verdict | output: PO words | gate: po | stop: PO accepts")
            flow("omi-flow-demo", *ok)
            omi.workflows.workflows_catalog(root)
            cat = (wf / "CATALOG.md").read_text()
            assert "- omi-flow-demo: Use for demos. [plan > build > review > accept] [~" in cat, cat
            omi.workflows.check_all_workflows(root)
            assert [s["gate"] for s in omi.workflows.get_workflow(root, "omi-flow-demo")] == ["none", "none", "review", "po"]
            r = subprocess.run([sys.executable, "-m", "omi", "workflows", "--check"], cwd=root, capture_output=True, text=True,
                               env={**os.environ, "PYTHONPATH": str(Path(__file__).parents[1] / "src")})
            assert r.returncode == 0 and f"workflows ok ({len(list(wf.glob('omi-flow-*.md')))} checked)" in r.stdout, r.stdout + r.stderr

            # unknown ids, gates, budgets and size fail the check
            fails(lambda: omi.workflows.get_workflow(root, "omi-flow-ghost"), "unknown workflow `omi-flow-ghost`", "omi-flow-demo")
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
                fails(lambda: omi.workflows.get_workflow(root, name), *words)
                (wf / f"{name}.md").unlink()
            (root / ".omi" / "agents" / "omi-agent-reviewer.md").write_text(
                "---\nrole: omi-agent-reviewer\nmodel: sonnet\neffort: low\naccess: read\n"
                "skills: [omi-skill-a, omi-skill-b]\nsummary: s\n---\nbody")
            flow("omi-flow-d", ok[2].replace("skills: ", "skills: omi-skill-c, omi-skill-big"))
            fails(lambda: omi.workflows.get_workflow(root, "omi-flow-d"), "omi-skill-big is", "per skill")  # role defaults count per step
            (wf / "omi-flow-d.md").unlink()
            flow("omi-flow-long", *ok, summary="x" * 8000)
            fails(lambda: omi.workflows.get_workflow(root, "omi-flow-long"), "per workflow")
            (wf / "omi-flow-long.md").unlink()
            flow("bad-name", *ok)
            fails(lambda: omi.workflows.check_all_workflows(root), "must start with `omi-flow-`", "stale")
            (wf / "bad-name.md").unlink()
            omi.workflows.check_all_workflows(root)

            # step state
            task = root / ".omi" / "tasks" / "TASK-001.md"
            task.write_text("---\nid: TASK-001\nworkflow: omi-flow-demo\nstep:\n---\n## Goal\nG\n\n## Checkpoint\nDone:\n")
            go = lambda action, why=None: omi.tasks.step(root, "TASK-001", action, why)  # noqa: E731
            front = lambda: omi.core.meta(task)  # noqa: E731
            fails(lambda: go("done"), "no step started")
            assert go("next") == 0 and front()["step"] == "plan"
            fails(lambda: go("next"), "step plan is not done")
            fails(lambda: go("skip"), "--why")
            go("skip", "PO wrote the AC already")
            fails(lambda: go("skip", "again"), "already skipped")
            go("next")
            assert front()["step"] == "build" and omi.tasks.checkpoint(task.read_text()) == "Done:"
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
            assert omi.tasks.step_states(text) == {"plan": "skipped", "build": "done", "review": "done", "accept": "done"}
            # back: a started review gate fails and the nearest earlier write step restarts
            task.write_text("---\nid: TASK-001\nworkflow: omi-flow-demo\nstep: plan\n---\n## Steps\n- plan started 2026-01-01 10:00\n")
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
            go("done")
            fails(lambda: go("back"), "already done")
            # feature-sensitive: back from security skips the review step and lands on build
            sens = ("id: build | role: omi-agent-engineer | skills: | input: t | output: d | gate: none | stop: ok",
                    "id: review | role: omi-agent-reviewer | skills: | input: d | output: v | gate: review | stop: PASS",
                    "id: security | role: omi-agent-reviewer | skills: | input: d | output: v | gate: review | stop: PASS")
            flow("omi-flow-sens", *sens)
            task.write_text("---\nid: TASK-001\nworkflow: omi-flow-sens\nstep:\n---\n")
            go("next"), go("done"), go("next"), go("done"), go("next")
            assert front()["step"] == "security" and go("back") == 0 and front()["step"] == "build"
            # task skills count for a write step only, never for a read-role step (security)
            tm = {"skills": "omi-skill-a, omi-skill-b"}
            assert omi.workflows.step_skill_ids(root, {"role": "omi-agent-reviewer", "skills": ""}, tm) == omi.workflows.step_skill_ids(
                root, {"role": "omi-agent-reviewer", "skills": ""}, {})
            assert {"omi-skill-a", "omi-skill-b"} <= set(omi.workflows.step_skill_ids(root, {"role": "omi-agent-engineer", "skills": ""}, tm))
            (wf / "omi-flow-sens.md").unlink()

            # unknown workflow on the task, default workflow, unknown task role
            task.write_text("---\nid: TASK-001\nworkflow: omi-flow-ghost\n---\n")
            fails(lambda: go("next"), "unknown workflow `omi-flow-ghost`")
            task.write_text("---\nid: TASK-001\n---\n")
            go("next")  # default workflow omi-flow-feature now exists
            assert front()["step"] == "plan"
            task.write_text("---\nid: TASK-001\nworkflow: omi-flow-demo\nrole: omi-agent-ghost\nstep: plan\n---\n"
                            "## Steps\n- plan done 2026-10-25 10:00\n")
            fails(lambda: go("next"), "unknown role `omi-agent-ghost`")
            fails(lambda: omi.tasks.step(root, "TASK-404", "next"), "no task file")
            fails(lambda: omi.tasks.step(root, "../TASK-001", "next"), "invalid task id")
            # a PO approval line outside ## Steps does not count
            task.write_text("---\nid: TASK-001\nworkflow: omi-flow-demo\nstep: accept\n---\nPO approval accept: sneaky\n\n"
                            "## Steps\n- plan done 2026-10-25 10:00\n- build done 2026-10-25 10:00\n- review done 2026-10-25 10:00\n"
                            "- accept started 2026-10-25 10:00\n\n## Checkpoint\nPO approval accept: x\n")
            fails(lambda: go("done"), "po gate")
            # a task with a worktree keeps its step state in the worktree copy, not the main checkout
            wt = root / "wt"
            (wt / ".omi" / "tasks").mkdir(parents=True)
            wtask = wt / ".omi" / "tasks" / "TASK-001.md"
            wtask.write_text("---\nid: TASK-001\nworkflow: omi-flow-demo\nstatus: in-progress\n---\n")
            task.write_text("---\nid: TASK-001\nworkflow: omi-flow-demo\n---\n")
            real_wts, omi.core.task_worktrees = omi.core.task_worktrees, lambda r: {"TASK-001": str(wt)}
            try:
                assert go("next") == 0
                assert omi.core.meta(wtask)["step"] == "plan" and "step" not in omi.core.meta(task)
                assert omi.tasks.tasks(root)["TASK-001"]["step"] == "plan"  # what `omi status` prints
            finally:
                omi.core.task_worktrees = real_wts
        finally:
            sys.stdout = saved
    repo = Path(__file__).parents[1]
    assert (repo / ".omi" / "tasks" / "_template.md").read_text() == (omi.core.TEMPLATE / "dot-omi" / "tasks" / "_template.md").read_text()
    for name in ("omi-flow-feature", "omi-flow-feature-ui", "omi-flow-feature-sensitive"):
        a, b = repo / ".omi" / "workflows" / f"{name}.md", omi.core.TEMPLATE / "dot-omi" / "workflows" / f"{name}.md"
        assert a.read_text() == b.read_text() and not omi.workflows.validate_workflow(repo, a), name
        assert "Review-fail rule" in a.read_text() and "PO gates" in a.read_text()
    assert (repo / ".omi" / "workflows" / "CATALOG.md").read_text() == (omi.core.TEMPLATE / "dot-omi" / "workflows" / "CATALOG.md").read_text()
    assert "workflow: omi-flow-feature" in (repo / ".omi" / "tasks" / "_template.md").read_text()


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
        assert omi.tasks.parallel(root, ["TASK-001", "TASK-002"]) == []
        out = omi.tasks.parallel(root, ["TASK-001", "TASK-003"])
        assert len(out) == 1 and "src/a/**" in out[0] and "src/**" in out[0]
        assert omi.tasks.parallel(root, ["TASK-002", "TASK-006"]) == ["TASK-006 depends on TASK-002"]
        assert "status done" in omi.tasks.parallel(root, ["TASK-001", "TASK-004"])[0]
        assert not omi.tasks.globs_overlap("src/ab/**", "src/a/**") and omi.tasks.globs_overlap("src/a*", "src/ab/x")
        assert omi.tasks.parallel(root, ["TASK-001", "TASK-002", "TASK-001"]) == ["TASK-001: duplicate id"]
        real, realmc = omi.core.task_worktrees, omi.core.main_checkout
        omi.core.main_checkout = lambda _: root
        class Out(io.StringIO):
            def reconfigure(self, **kw): pass
        out = Out()
        realout = sys.stdout
        try:
            omi.core.task_worktrees = lambda r: {}
            sys.stdout = out
            omi.cli.main(["parallel", "TASK-001", "TASK-002"])
            assert out.getvalue().strip() == "parallel ok: TASK-001 TASK-002"
            out.truncate(0)
            omi.cli.main(["parallel", "TASK-001"])
            assert "parallel <TASK-ID>" in out.getvalue()
            try:
                omi.cli.main(["parallel", "TASK-001", "TASK-003"])
                assert False
            except SystemExit as e:
                assert e.code != 0 and "src/a/**" in str(e.code)
        finally:
            sys.stdout = realout
            omi.core.task_worktrees, omi.core.main_checkout = real, realmc
    assert omi.docker.container_name("role", "TASK-001") != omi.docker.container_name("role", "TASK-002")
    real = omi.core.git
    omi.core.git = lambda *a: ("worktree /r\nbranch refs/heads/main\n\nworktree /w1\nbranch refs/heads/task/TASK-A\n\n"
                          "worktree /w2\nbranch refs/heads/task/TASK-B\n")
    try:
        assert omi.core.task_worktrees(Path("/r")) == {"TASK-A": "/w1", "TASK-B": "/w2"}
    finally:
        omi.core.git = real
    with tempfile.TemporaryDirectory() as d:
        a, b = Path(d) / "a.md", Path(d) / "b.md"
        a.write_text("# t\n"), b.write_text("# t\n")
        omi.tasks.record_usage(a, "r", "m", None, (1, 2, 3), 4)
        assert "| r | m |" in a.read_text() and b.read_text() == "# t\n"


def main():
    test_step_approve_reopen()
    test_reopen_last_write_step()
    test_task_skill_step_commands()
    test_parallel()
    test_workflows()
    test_roles()
    test_task_flow_commit_scope_sync_warn()


if __name__ == "__main__":
    main()
