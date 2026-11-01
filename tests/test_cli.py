import io
import re
import shutil
import shlex
import json
import contextlib
import os
import tomllib
import subprocess
import sys
import tempfile
from pathlib import Path
from helpers import omi, git, detached_project, detached_cli, state_remote
from unittest.mock import patch
from omi.project import improve
from omi.state import resolve as state


def test_cli_correctness():
    for base, dot in ((omi.common.core.TEMPLATE, "dot-"),):
        template = (base / f"{dot}omi/tasks/_template.md").read_text(encoding="utf-8")
        assert omi.project.scope.GIT_HINT in template and "edit only on development" in template
        skill = (base / f"{dot}claude/skills/omi-task/SKILL.md").read_text(encoding="utf-8")
        assert "push `development` right away (`git push`)" in skill
        assert "development only" not in skill and "the worktree copy is ignored" not in skill
        assert "`omi run` copies the new scope into the worktree copy" in skill
    # #6 the configured test command runs through a shell
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / ".omi").mkdir()
        python = sys.executable.replace("\\", "/")
        command = f'"{python}" -c "import os,sys;sys.exit(0 if os.environ[\'FOO\']==\'1\' else 1)"'
        cfg = root / ".omi" / "config.json"
        cfg.write_text(json.dumps({"test": command}), encoding="utf-8")
        argv = omi.worker.run.test_command(root, root)
        shell = "cmd" if isinstance(argv, str) else argv[0]
        command = ('set "FOO=1" && ' if shell == "cmd" else "FOO=1 ") + command
        cfg.write_text(json.dumps({"test": command}), encoding="utf-8")
        argv = omi.worker.run.test_command(root, root)
        assert argv == (f'cmd /d /s /c "{command}"' if shell == "cmd" else [shell, "-c", command])
        assert subprocess.run(argv, cwd=d).returncode == 0
        assert omi.worker.run.test_prompt_line(root, root) == command
        # a program that cannot start: message, no traceback
        real = omi.worker.run.test_command, omi.project.scope.out_of_scope, omi.project.catalogs.check_all_skills
        omi.worker.run.test_command, omi.project.scope.out_of_scope, omi.project.catalogs.check_all_skills = (
            lambda *a: [str(root / "no-such-prog")], lambda *a, **k: [], lambda wt: None)
        try:
            problems = omi.worker.run.deterministic_checks(root, root, "TASK-001")
        finally:
            omi.worker.run.test_command, omi.project.scope.out_of_scope, omi.project.catalogs.check_all_skills = real
        assert len(problems) == 1 and problems[0].startswith("test command failed to start: "), problems
        # a nonexistent program in the configured command: shell exit 127/9009
        cfg.write_text(json.dumps({"test": "no-such-prog-omi-xyz --run"}), encoding="utf-8")
        omi.project.scope.out_of_scope, omi.project.catalogs.check_all_skills = lambda *a, **k: [], lambda wt: None
        try:
            problems = omi.worker.run.deterministic_checks(root, root, "TASK-001")
        finally:
            omi.project.scope.out_of_scope, omi.project.catalogs.check_all_skills = real[1], real[2]
        assert len(problems) == 1 and problems[0].startswith("test command failed to start: "), problems
        # #14 status hint on an empty `test`
        (root / ".omi" / "config.json").write_text('{"test": ""}')
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            omi.app.cli.status(root)
        assert "no `test` command in .omi/config.json" in buf.getvalue()
        (root / ".omi" / "config.json").write_text('{"test": "true"}')
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            omi.app.cli.status(root)
        assert "no `test` command" not in buf.getvalue()
        cfg.write_text('{"test":', encoding="utf-8")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            omi.app.cli.status(root)
        assert "no `test` command" not in buf.getvalue()
    # #8 PO approval with or without a leading `- `
    assert omi.project.tasks.po_approved("x\n## Steps\n- PO approval accept: ok\n", "accept")
    assert omi.project.tasks.po_approved("x\n## Steps\nPO approval accept: ok\n", "accept")
    assert not omi.project.tasks.po_approved("x\n## Steps\n- PO approval accept:\n", "accept")
    # #4 hint for .git* paths
    assert "exact scope entry (no globs), e.g. .github/workflows/ci.yml" in omi.project.scope.git_hint([".github/x.yml"])
    assert omi.project.scope.git_hint(["src/a.py"]) == ""
    # #10 scope comes from development, not from the worktree copy
    real_git = omi.common.core.git
    omi.common.core.git = lambda cwd, *a: "---\nscope: a/**\n---\n" if "show" in a else None
    try:
        assert omi.project.scope.task_scope("/nowhere", "TASK-001") == ["a/**"]
    finally:
        omi.common.core.git = real_git
    with tempfile.TemporaryDirectory() as d:
        wt = Path(d)
        task = wt / ".omi" / "tasks" / "TASK-001.md"
        task.parent.mkdir(parents=True)
        task.write_text("---\nscope: **\n---\n", encoding="utf-8")
        real = omi.common.core.git, subprocess.run
        calls = []

        def development_scope(cwd, *args):
            if args[0] in ("rev-parse", "remote"):
                return None
            assert args == ("show", "development:.omi/tasks/TASK-001.md")
            calls.append(args)
            return "---\nscope: src/**\n---\n"

        def changed(cmd, **kw):
            assert "status" in cmd
            return subprocess.CompletedProcess(cmd, 0, " M src/a.py\0?? docs/outside.md\0", "")

        try:
            omi.common.core.git, subprocess.run = development_scope, changed
            assert omi.project.scope.out_of_scope(wt, "TASK-001") == ["docs/outside.md"]
            assert calls
        finally:
            omi.common.core.git, subprocess.run = real
    # review gate: `done` refuses after a FAIL verdict
    with tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve()
        omi.setup.upgrade.init(root)
        task = root / ".omi" / "tasks" / "TASK-001.md"
        task.parent.mkdir(parents=True, exist_ok=True)
        row = lambda v: f"| omi-agent-reviewer | sonnet | low | 1 | 1 | 1 | 5s | - | {v} |\n"
        base = ("---\nid: TASK-001\nworkflow: omi-flow-feature\nstep: review\n---\n## Steps\n- plan done 2026-01-01 00:00\n"
                "- build done 2026-01-01 00:00\n- review started 2026-01-01 00:00\n\n## Usage\n" + omi.project.tasks.USAGE_HEAD
                + "\n|---|---|---|---|---|---|---|---|---|\n")
        task.write_text(base + row("FAIL abc1234"))
        try:
            omi.project.tasks.step(root, "TASK-001", "done")
            raise AssertionError("done passed after FAIL")
        except SystemExit as e:
            assert "FAIL" in str(e) and "omi step TASK-001 back" in str(e), e
        task.write_text(base + row("FAIL abc1234") + row("PASS def5678"))
        assert omi.project.tasks.step(root, "TASK-001", "done") == 0


def test_cli_characterization():
    """Pins exit code and key output of every USAGE command through `python -m omi` (no internals, no gh/docker on PATH)."""
    src = str(Path(__file__).resolve().parents[1] / "src")
    want = tomllib.loads(Path(src).parent.joinpath("pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    git = Path(shutil.which("git"))
    gitbin = tempfile.TemporaryDirectory()  # PATH holds only git: on CI gh and docker share git's folder
    try:
        (Path(gitbin.name) / git.name).symlink_to(git)
        path = gitbin.name
    except OSError:  # Windows without symlink rights: git's own folder holds git alone there
        path = str(git.parent)
    env = {**os.environ, "PYTHONPATH": src, "PATH": path, "OMI_STATE": str(Path(gitbin.name) / "state"),
           "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}

    def cli(cwd, *args, stdin=""):
        r = subprocess.run([sys.executable, "-m", "omi", *args], cwd=cwd, env=env, input=stdin, capture_output=True,
                           encoding="utf-8", errors="replace")
        # omi prints OS path separators; normalise so every path match below holds on Windows too
        return r.returncode, r.stdout.replace("\\", "/"), r.stderr.replace("\\", "/")

    def task(root, tid, extra):
        (root / ".omi" / "tasks" / f"{tid}.md").write_text(f"---\nid: {tid}\ntitle: T{tid[-1]}\nstatus: planned\n{extra}---\n"
                                                          "## Goal\nx\n## Checkpoint\nDone: nothing\n", encoding="utf-8")
    with tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve() / "r"
        root.mkdir()
        env["HOME"] = env["USERPROFILE"] = str(Path(d) / "user")
        rc, usage, err = cli(root)
        assert rc == 0 and usage.startswith("usage: omi <command>\n") and not err
        assert [l.split()[0] for l in usage.splitlines()[1:]] == [
            "attach", "install-user", "init", "upgrade", "version", "status", "improve", "sync", "board", "guard", "github", "clean", "skills", "skills", "token", "plans",
            "references", "rules", "agents", "workflows", "step", "note", "run", "hook", "parallel", "worker", "worker"]
        # unknown commands and incomplete arguments fall through to the usage text
        for args in (["help"], ["bogus"], ["step", "TASK-001"], ["run", "omi-agent-engineer", "--model"], ["parallel", "X"],
                     ["hook", "pre-run"], ["token"], ["worker"]):
            assert cli(root, *args) == (0, usage, ""), args
        for args in (["version"], ["--version"]):
            assert cli(root, *args) == (0, f"omi {want}\nlatest: python -m omi upgrade --check\n", ""), args
        assert cli(root, "install-user") == (0, "installed omi user integration\n", "")
        assert cli(root, "install-user") == (0, "installed omi user integration\n", "")
        assert cli(root, "install-user", "--remove") == (0, "removed omi user integration\n", "")
        assert cli(root, "install-user", "--remove") == (0, "omi user integration not installed\n", "")
        assert cli(root, "install-user", "bad") == (1, "", "OMI: usage: omi install-user [--remove]\n")
        assert cli(root, "session-start") == (0, "", "")
        assert cli(root, "sync") == (1, "", "OMI: omi sync requires a detached project (omi attach)\n")
        rc, out, err = cli(root, "init", ".")
        assert rc == 0 and "create AGENTS.md\n" in out and f"stamp  .omi/version ({want})\n" in out, (out, err)
        assert "\ntools: git ok, gh MISSING, docker MISSING" in out and out.endswith("next: open Claude Code or Codex here and type omi-idea\n")
        rc, out, _ = cli(root, "init", ".")
        assert rc == 0 and "skip   AGENTS.md (exists)\n" in out and "create " not in out
        rc, out, _ = cli(root, "status")
        assert rc == 0 and f"\nomi {want} (project {want})\n" in out and "upgrade --apply" not in out
        assert out.endswith("no tasks yet - run omi-idea\n"), out
        rc, out, _ = cli(root, "upgrade", "--apply")
        assert rc == 0 and out.endswith(f"upgrade {want}: 0 created, 0 updated, 0 kept (see *.omi-new)\n"), out
        assert cli(root, "upgrade", "--to", "bogus") == (1, "", "usage: omi upgrade [--check | --to vX.Y.Z]\n")
        for args in (["skills"], ["rules"], ["plans"], ["references"], ["agents"], ["workflows"]):
            rc, out, err = cli(root, *args)
            assert rc == 0 and not err and re.fullmatch(rf"wrote \.omi/{args[0]}/CATALOG\.md \(\d+ \w+\)\n", out), (args, out)
        for args, name in ((["skills", "--check"], "skills"), (["workflows", "--check"], "workflows")):
            rc, out, err = cli(root, *args)
            assert rc == 0 and not err and re.fullmatch(rf"{name} ok \(\d+ checked\)\n", out), (args, out, err)
        gh = (1, "", "gh is not installed (https://cli.github.com); omi github needs it.\n")
        assert cli(root, "github") == gh and cli(root, "github", "--po") == gh
        assert cli(root, "token", "set", "--tool", "x") == (1, "", "usage: omi token set [--tool claude|codex]\n")
        if sys.platform != "win32":  # Windows prompts for the secret
            assert cli(root, "token", "set") == (0, "no credential store support here; export CLAUDE_CODE_OAUTH_TOKEN in the shell that runs omi.\n", "")
            assert cli(root, "token", "set", "--tool", "codex")[1] == "no credential store support here; export OPENAI_API_KEY in the shell that runs omi.\n"
        hook = (1, "", "usage: omi hook pre-run|post-run|pre-merge <TASK-ID> (the task needs a worktree). Nothing changed.\n")
        assert cli(root, "hook", "pre-run", "TASK-001") == hook and cli(root, "hook", "bogus", "TASK-001") == hook
        assert cli(root, "run", "omi-agent-engineer", "TASK-001") == (
            1, "", "no worktree for TASK-001: create it first (git worktree add). Nothing changed.\n")
        assert cli(root, "worker", "x") == (1, "", "usage: omi worker <wt> <task-file> [--model M] [--effort E]\n")
        rc, out, err = cli(root, "worker", "x", "--prove")
        assert rc == 1 and not out and err.endswith(" is not a git worktree. Nothing changed.\n"), err
        # guard: exit 0 allows, 2 blocks with the reason on stderr
        assert cli(root, "guard", stdin="{}") == (0, "", "")
        payload = lambda p, **kw: json.dumps({"tool_input": {"file_path": str(p)}, **kw})
        rc, out, err = cli(root, "guard", stdin=payload(root / ".claude" / "settings.json"))
        assert rc == 2 and err.endswith("settings.json is Claude Code config; only a task whose scope names it may change it.\n"), err
        outside = Path(d).resolve() / "elsewhere" / "x.py"
        assert cli(root, "guard", stdin=payload(outside)) == (0, "", "")
        rc, out, err = cli(root, "guard", stdin=payload(outside, agent_type="omi-agent-engineer"))
        assert rc == 2 and err.startswith("OMI: ") and err.endswith("x.py is outside the task worktree.\n"), err
        # tasks: status, parallel, skills check, step
        assert cli(root, "step", "bad!", "next") == (1, "", "invalid task id `bad!`: use letters, digits, `-` and `_`. Nothing changed.\n")
        rc, out, err = cli(root, "step", "TASK-001", "next")
        assert rc == 1 and err.startswith("no task file ") and err.endswith("TASK-001.md. Nothing changed.\n"), err
        assert cli(root, "parallel", "TASK-001", "TASK-002") == (1, "", "TASK-001: no task file\nTASK-002: no task file\n")
        task(root, "TASK-001", "scope: a/**\nrole: omi-agent-engineer\nskills: []\n")
        task(root, "TASK-002", "depends: TASK-001\nscope: b/**\n")
        task(root, "TASK-003", "scope: a/x.py\n")
        rc, out, _ = cli(root, "status")
        assert rc == 0 and out.endswith("done: 0/3\n[Chưa bắt đầu] TASK-001 T1\n[Chưa bắt đầu] TASK-002 T2\n[Chưa bắt đầu] TASK-003 T3\nnext: TASK-001\n"), out
        assert cli(root, "parallel", "TASK-001", "TASK-002") == (1, "", "TASK-002 depends on TASK-001\n")
        assert cli(root, "parallel", "TASK-001", "TASK-003") == (1, "", "TASK-001 and TASK-003 scopes overlap: a/** vs a/x.py\n")
        assert cli(root, "parallel", "TASK-001", "TASK-001") == (1, "", "TASK-001: duplicate id\n")
        assert cli(root, "parallel", "TASK-003", "TASK-002") == (0, "parallel ok: TASK-003 TASK-002\n", "")
        assert cli(root, "skills", "check", str(Path(".omi") / "tasks" / "TASK-001.md")) == (0, "skills ok\n", "")
        steps = (
            (["next"], 0, "TASK-001: step plan (coordinator, gate none): input PO idea; output task file with scope and acceptance criteria; "
                          "stop when task file complete and PO picked it\n"),
            (["next"], 1, "TASK-001: step plan is not done; run `omi step TASK-001 done` or `skip --why`. Nothing changed.\n"),
            (["done"], 0, "TASK-001: step plan done\n"),
            (["skip", "--why", "x"], 1, "TASK-001: step plan is already done; run `omi step TASK-001 next`. Nothing changed.\n"),
            (["next"], 0, "TASK-001: step build (omi-agent-engineer, gate none): input task file, worktree; output diff, tests passing, "
                          "Checkpoint updated; stop when every criterion has a passing test\n"),
            (["skip", "--why", "baseline"], 0, "TASK-001: step build skipped\n"),
            (["next"], 0, "TASK-001: step review (omi-agent-reviewer, gate review): input task file, diff; output VERDICT PASS or FAIL; "
                          "stop when VERDICT PASS\n"),
            (["bogus"], 1, "usage: omi step <TASK-ID> next|done|back|skip|approve|reopen --why <reason>\n"),
            (["back"], 0, "TASK-001: step review failed; back to build (omi-agent-engineer), then `omi step TASK-001 done` and `next`\n"),
            (["back", "--to", "plan", "--why", "x"], 1, "TASK-001: `plan` is not an agent step before build in workflow omi-flow-feature. Nothing changed.\n"),
            (["back", "--to"], 1, "usage: omi step TASK-001 back --to <step> --why <reason>. Nothing changed.\n"),
            (["next", "--to", "plan"], 1, "usage: omi step TASK-001 back --to <step> --why <reason>. Nothing changed.\n"))
        for args, code, msg in steps:
            rc, out, err = cli(root, "step", "TASK-001", *args)
            assert (rc, out if code == 0 else err) == (code, msg) and not (err if code == 0 else out), (args, rc, out, err)
        text = (root / ".omi" / "tasks" / "TASK-001.md").read_text(encoding="utf-8")
        assert "\nstep: build\n" in text and re.search(r"\n## Steps\n- plan started [\d-]+ [\d:]+\n- plan done ", text), text
        rc, out, _ = cli(root, "status")
        assert rc == 0 and "[Chưa bắt đầu] TASK-001 T1\n" in out
        assert cli(root, "step", "TASK-001", "done")[0] == 0 and cli(root, "step", "TASK-001", "next")[0] == 0
        assert cli(root, "step", "TASK-001", "back", "--to", "build", "--why", "re-plan", "the API") == (
            0, "TASK-001: step review failed; back to build (omi-agent-engineer), then `omi step TASK-001 done` and `next`\n", "")
        assert cli(root, "step", "TASK-001", "done")[0] == 0 and cli(root, "step", "TASK-001", "next")[0] == 0 and cli(root, "step", "TASK-001", "done")[0] == 0
        assert cli(root, "step", "TASK-001", "next")[0] == 0
        assert cli(root, "step", "TASK-001", "back", "--why", "late", "reason", "--to", "build")[0] == 0
        text = (root / ".omi" / "tasks" / "TASK-001.md").read_text(encoding="utf-8")
        assert "workflow back to build" in text and ": late reason\n" in text and "--to" not in text.split("## Steps")[1]
        text = (root / ".omi" / "tasks" / "TASK-001.md").read_text(encoding="utf-8")
        assert "\nstep: build\n" in text and re.search(r"^- workflow back to build [\d-]+ [\d:]+: re-plan the API\n- review failed ", text, re.M), text
        assert cli(root, "attach") == (1, "", f"OMI: {root.as_posix()} has no origin remote\n")
        rc, out, err = cli(root, "attach", "--state")
        assert (rc, out, err) == (1, "", "OMI: usage: omi attach [<repo path>] [--state <git url>]\n")
        subprocess.run([str(git), "-C", str(root), "remote", "add", "origin", "https://example.org/team/r.git"], check=True)
        rc, out, err = cli(root, "attach")
        assert rc == 0 and "attached: " in out and "private remote: git -C " in out and not err, (rc, out, err)
        rc, out, err = cli(root, "attach", ".")
        assert rc == 0 and out.startswith("already attached: ") and not err, (rc, out, err)
        assert cli(root, "sync") == (0, "state pull skipped: no remote\nstate push skipped: no remote\nstate synced\n", "")
        assert cli(root, "sync", "extra") == (1, "", "OMI: usage: omi sync\n")


def test_status_phase_and_step_lines() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        omi.setup.upgrade.init(root)
        task = root / ".omi/tasks/TASK-001.md"
        base = ("---\nid: TASK-001\ntitle: Ship board\nstatus: in-progress\nworkflow: omi-flow-feature\n"
                "tool: codex\nmodel: sonnet\neffort: medium\nstep: {step}\n---\n"
                "## Usage\n" + omi.project.tasks.USAGE_HEAD + "\n|---|---|---|---|---|---|---|---|---|\n"
                "| omi-agent-reviewer | sonnet | medium | 1 | 1 | 1 | 1s | - | FAIL |\n")
        steps = omi.project.workflows.get_workflow(root, "omi-flow-feature")
        task.write_text(base.format(step="review"), encoding="utf-8")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            omi.app.cli.status(root)
        lines = output.getvalue().splitlines()
        first = next(i for i, line in enumerate(lines) if "TASK-001 Ship board" in line)
        assert lines[first] == "[Đang review] TASK-001 Ship board"
        index = next(i for i, step in enumerate(steps, 1) if step["id"] == "review")
        assert lines[first + 1] == f"  bước {index}/{len(steps)} review · vòng 2 · codex sonnet/medium"
        assert lines[first + 2] == "  " + omi.project.tasks.step_strip({"step": "review", "status": "in-progress"}, steps)
        task.write_text(base.format(step="unknown"), encoding="utf-8")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            omi.app.cli.status(root)
        assert f"bước ?/{len(steps)} unknown · codex sonnet/medium" in output.getvalue()
        assert "bước 0/" not in output.getvalue()



def register_omi(project: Path) -> Path:
    root = project.parent / "omi"
    root.mkdir()
    (root / "project.json").write_text('{"remote": "https://github.com/omi-teams/omi"}', encoding="utf-8")
    (root / ".omi" / "tasks").mkdir(parents=True)
    return root


def test_improve_creation_and_workflows() -> None:
    with detached_project() as (code, project, wt, task):
        target = register_omi(project)
        # Existing omi task numbers, including done tasks, determine the next id.
        (target / ".omi/tasks/TASK-123.md").write_text("---\nid: TASK-123\nstatus: done\n---\n", encoding="utf-8")
        home, remote, other = state_remote(project)
        unrelated = project / "pending.txt"
        unrelated.write_text("leave staged", encoding="utf-8")
        git(home, "add", str(unrelated))
        for index, (kind, workflow) in enumerate((("bug", "omi-flow-bugfix"), ("security", "omi-flow-feature-sensitive"),
                                                 ("idea", "omi-flow-feature")), 124):
            summary = f"Fix {kind}: preserve # and 'quotes'"
            with patch.dict(os.environ, {"OMI_AGENT": "omi-agent-reviewer"}):
                args = ["improve", summary] + ([] if kind == "bug" else ["--kind", kind])
                out = detached_cli(wt, *args)
            tid = f"TASK-{index}"
            assert tid in out.splitlines(), out
            created = target / f".omi/tasks/{tid}.md"
            assert b"\r" not in created.read_bytes(), "new improvement tasks must use LF line endings"
            text = created.read_text(encoding="utf-8")
            front = omi.common.core.parse(text)
            assert front["id"] == tid and front["status"] == "planned" and front["workflow"] == workflow
            assert f"title: {summary}\n" in text
            assert "Source project: sample\nSource task: TASK-097\nSource agent: omi-agent-reviewer" in text
            assert omi.common.core.git(home, "show", "--pretty=format:", "--name-only", "HEAD") == f"projects/omi/.omi/tasks/{tid}.md"
            assert omi.common.core.git(home, "rev-parse", "HEAD") == omi.common.core.git(remote, "rev-parse", "main")
        assert omi.common.core.git(home, "diff", "--cached", "--name-only") == "projects/sample/pending.txt"


def test_improve_duplicate() -> None:
    with detached_project() as (code, project, wt, task):
        target = register_omi(project)
        state_remote(project)
        assert "TASK-001" in detached_cli(wt, "improve", "Same # finding")
        head = omi.common.core.git(project, "rev-parse", "HEAD")
        assert detached_cli(wt, "improve", "Same # finding", "--kind", "idea").strip() == "TASK-001"
        assert omi.common.core.git(project, "rev-parse", "HEAD") == head
        first = target / ".omi/tasks/TASK-001.md"
        first.write_text(first.read_text(encoding="utf-8").replace("status: planned", "status: done"), encoding="utf-8")
        assert "TASK-002" in detached_cli(wt, "improve", "Same # finding")


def test_improve_fallback_and_validation() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        summary = "Keep 'quoted' $(text) # intact"
        out = io.StringIO()
        with patch.object(state, "resolve", return_value=state.Project(root, root)), \
                patch.object(state, "registry", return_value={}), \
                patch.object(omi.common.core, "git", return_value=None), \
                patch("subprocess.run", side_effect=AssertionError("unexpected subprocess/network")), \
                patch.dict(os.environ, {"OMI_TASK": "TASK-149", "OMI_AGENT": "Coordinator"}), \
                contextlib.redirect_stdout(out):
            improve.improve([summary, "--from", "other project", "--kind", "idea"], root)
            for args in (["bad\ntext"], ["ok", "--from", ""], ["ok", "--kind", "invalid"], ["ok", "--from"]):
                try:
                    improve.improve(args, root)
                    assert False, args
                except (state.StateError, SystemExit):
                    pass
        text = out.getvalue()
        command = text[text.index("gh issue create"):].strip()
        words = shlex.split(command)
        assert words[:5] == ["gh", "issue", "create", "--repo", "omi-teams/omi"]
        assert words[words.index("--title") + 1] == summary
        body = words[words.index("--body") + 1]
        assert "Source project: other project\nSource task: TASK-149\nSource agent: Coordinator" in body
        assert "Kind: idea" in body and summary in text
        assert not list(root.iterdir())


def test_improve_status_count() -> None:
    with detached_project() as (code, project, wt, task):
        target = register_omi(project)
        state_remote(project)
        detached_cli(wt, "improve", "open from sample")
        detached_cli(wt, "improve", "open from elsewhere", "--from", "elsewhere")
        detached_cli(wt, "improve", "closed from sample")
        closed = target / ".omi/tasks/TASK-003.md"
        closed.write_text(closed.read_text(encoding="utf-8").replace("status: planned", "status: done"), encoding="utf-8")
        (project / ".omi/version").write_text("0.0.1", encoding="utf-8")
        out = detached_cli(wt, "status")
        assert "omi improvements filed: 1 open" in out and "upgrade --apply" in out
        # Status in a project without the shared omi registration still prints zero.
        with patch.object(improve, "omi_project", return_value=None):
            assert "omi improvements filed: 0 open" in detached_cli(wt, "status")


def main():
    test_improve_creation_and_workflows()
    test_improve_duplicate()
    test_improve_fallback_and_validation()
    test_improve_status_count()
    test_status_phase_and_step_lines()
    test_cli_correctness()
    test_cli_characterization()


if __name__ == "__main__":
    main()
