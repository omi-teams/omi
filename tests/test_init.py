import io
import shlex
import json
import os
import contextlib
import importlib.metadata
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
from helpers import omi, git


def test_step_settings_format_and_docs():
    assert omi.worker.run.parse_step_settings("") == {}
    assert omi.worker.run.parse_step_settings("architect=codex/opus/high, review=claude//") == {
        "architect": {"tool": "codex", "model": "opus", "effort": "high"},
        "review": {"tool": "claude", "model": "", "effort": ""},
    }
    assert omi.worker.run.parse_step_settings("build=//") == {"build": {"tool": "", "model": "", "effort": ""}}
    for value in ("review", "review=claude/opus", "=claude//", "review=claude///", "review=claude//,",
                  "review=claude//, review=codex//", "review=claude/o pus/high"):
        try:
            omi.worker.run.parse_step_settings(value)
            raise AssertionError(f"accepted malformed entry: {value}")
        except SystemExit as exc:
            assert "expected <step>=<tool>/<model>/<effort>, ..." in str(exc)
    root = Path(__file__).parents[1]
    for path in (root / ".omi/tasks/_template.md", omi.common.core.TEMPLATE / "dot-omi/tasks/_template.md"):
        lines = path.read_text(encoding="utf-8").splitlines()
        assert len([line for line in lines if line.startswith("step_settings:  #")]) == 1
    for path in (root / "AGENTS.md", omi.common.core.TEMPLATE / "AGENTS.md"):
        line = next(line for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("Tool per run:"))
        assert line.index("defaults") < line.index("role file") < line.index("task `tool/model/effort`") < line.index("step_settings:") < line.index("omi run --tool/--model/--effort")
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "Thiết lập theo bước: `step_settings:" in readme
    assert "`codex_models` mặc định rỗng" not in readme and "codex-default" not in readme
    assert "gpt-6-luna" in readme and "gpt-6.1-sol" in readme and "gpt-6-astra" in readme


def test_init_symlink_manifest():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "project"
        with contextlib.redirect_stdout(io.StringIO()):
            omi.setup.upgrade.init(root)
        outside = Path(d) / "outside.json"
        outside.write_bytes(b'{"keep": 1}\n')
        try:
            for rel in (".omi/manifest.json", ".omi/version"):
                (root / rel).unlink()
                (root / rel).symlink_to(outside)
        except OSError:
            print("skip init symlink manifest: symlink creation unavailable")
            return
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            omi.setup.upgrade.init(root)
        assert outside.read_bytes() == b'{"keep": 1}\n'
        assert "skip (symlink): .omi/manifest.json" in out.getvalue()
        assert "skip (symlink): .omi/version" in out.getvalue()


def test_init_symlink_destinations():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "project"
        (root / ".git").mkdir(parents=True)
        outside = Path(d) / "outside"
        outside.mkdir()
        missing = outside / "agents.md"
        existing = outside / "settings.json"
        existing.write_bytes(b"keep existing contents\n")
        (root / ".claude").mkdir()
        try:
            (root / "AGENTS.md").symlink_to(missing)
            (root / "docker").symlink_to(outside, target_is_directory=True)
            (root / ".claude" / "settings.json").symlink_to(existing)
        except OSError:
            print("skip init symlink destinations: symlink creation unavailable")
            return
        with contextlib.redirect_stdout(io.StringIO()) as out:
            omi.setup.upgrade.init(root)
        assert not missing.exists()
        assert list(outside.iterdir()) == [existing]
        assert existing.read_bytes() == b"keep existing contents\n"
        files = omi.setup.upgrade.read_manifest(root)
        for rel in ("AGENTS.md", "docker/Dockerfile", "docker/prove.sh", "docker/proxy.py", ".claude/settings.json"):
            assert f"skip (symlink): {rel}" in out.getvalue()
            assert rel not in files
        assert (root / "AGENTS.md").is_symlink()


def test_invalid_manifest_recovery():
    invalid = ("{broken", "[]", "null", '"manifest"', "42", "true",
               '{"files": null}', '{"files": []}', '{"files": "hashes"}', '{"files": 42}', '{"files": true}')
    for operation in (omi.setup.upgrade.init, omi.setup.upgrade.upgrade_apply):
        for contents in invalid:
            with tempfile.TemporaryDirectory() as d:
                root = Path(d)
                (root / ".git").mkdir()
                manifest = root / ".omi" / "manifest.json"
                manifest.parent.mkdir()
                manifest.write_text(contents, encoding="utf-8")
                with contextlib.redirect_stdout(io.StringIO()) as out:
                    assert omi.setup.upgrade.read_manifest(root) == {}
                assert len(out.getvalue().splitlines()) == 1
                assert "warning:" in out.getvalue() and "manifest" in out.getvalue()
                edited = root / "AGENTS.md"
                edited.write_text("local edits\n", encoding="utf-8")
                with contextlib.redirect_stdout(io.StringIO()) as out:
                    operation(root)
                assert out.getvalue().count("warning:") == 1
                assert edited.read_text(encoding="utf-8") == "local edits\n"
                files = json.loads(manifest.read_text(encoding="utf-8"))["files"]
                assert "AGENTS.md" not in files
                assert files["docker/Dockerfile"] == omi.setup.upgrade.template_shas()["docker/Dockerfile"]
                if operation is omi.setup.upgrade.upgrade_apply:
                    assert (root / "AGENTS.md.omi-new").read_bytes() == (omi.common.core.TEMPLATE / "AGENTS.md").read_bytes()


def test_init_fresh_project():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve()
        (root / ".gitignore").write_text("*.log")
        omi.setup.upgrade.init(root)
        for kind in ("skills", "agents", "workflows", "references"):
            assert (root / ".omi" / kind / "CATALOG.md").exists(), kind
        assert (root / ".gitignore").read_text().splitlines() == ["*.log", "__pycache__/", ".omi-cache/"]
        omi.setup.upgrade.init(root)
        assert (root / ".gitignore").read_text().splitlines() == ["*.log", "__pycache__/", ".omi-cache/"]
        assert (root / ".gitattributes").read_text() == "* text=auto eol=lf\n"
        (root / ".gitattributes").write_text("custom\n")
        omi.setup.upgrade.init(root)
        assert (root / ".gitattributes").read_text() == "custom\n"
        assert '"test"' in (root / ".omi" / "config.json").read_text()
    with tempfile.TemporaryDirectory() as d:
        omi.setup.upgrade.init(d)
        assert (Path(d) / ".gitignore").read_text() == "__pycache__/\n.omi-cache/\n"
        (Path(d) / "tests").mkdir()
        (Path(d) / "tests" / "test_a.py").write_text("raise SystemExit(3)")
        real = importlib.util.find_spec
        importlib.util.find_spec = lambda n: None
        try:
            cmd = omi.worker.run.test_command(d, d)
        finally:
            importlib.util.find_spec = real
        assert "pytest" not in cmd
        assert subprocess.run(cmd, cwd=d).returncode == 1
        (Path(d) / "tests" / "test_a.py").write_text("")
        assert subprocess.run(cmd, cwd=d).returncode == 0
        (Path(d) / "tests" / "test_b.py").write_text("import os,signal;os.kill(os.getpid(),signal.SIGKILL)")
        assert subprocess.run(cmd, cwd=d).returncode == 1, "a child killed by a signal must fail the run"
        (Path(d) / "tests" / "test_b.py").unlink()
        line = omi.worker.run.test_prompt_line(d, d)
        assert shlex.split(line) == [("python3" if a == sys.executable else a) for a in cmd], line
    with tempfile.TemporaryDirectory() as d:
        for existing in ("__pycache__", "/__pycache__/", "__pycache__/"):
            (Path(d) / ".gitignore").write_text(existing + "\n")
            omi.setup.upgrade.init(d)
            assert (Path(d) / ".gitignore").read_text() == existing + "\n.omi-cache/\n", existing


def test_guard_non_omi_projects():
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        repo = base / "ordinary"
        repo.mkdir()
        git(repo, "init", "-q", "-b", "main")
        (repo / "README.md").write_text("ordinary repo\n", encoding="utf-8")
        git(repo, "add", "README.md")
        git(repo, "commit", "-qm", "fixture")
        with patch.dict(os.environ, {"OMI_STATE": str(base / "state")}):
            def guard(path, cwd=repo):
                for agent in (None, "omi-agent-engineer"):
                    output = io.StringIO()
                    with contextlib.redirect_stderr(output):
                        result = omi.project.scope.guard(io.StringIO(json.dumps({
                            "cwd": str(cwd), "agent_type": agent, "tool_input": {"file_path": str(path)}})))
                    assert (result, output.getvalue()) == (0, "")

            guard(repo / ".claude/settings.json")
            guard(".claude/settings.local.json")
            wt = base / "ordinary-task"
            git(repo, "worktree", "add", "-qb", "task/TASK-1", str(wt))
            guard(wt / "src/new.py")
            guard(wt / ".claude/settings.json")
            guard(repo / "src/new.py")  # An unrelated task/* worktree is not an omi task.
            guard(repo / ".claude/settings.json")


def test_guard_user_settings_outside_repository():
    with tempfile.TemporaryDirectory() as d:
        home = Path(d)
        (home / ".omi").mkdir()  # install-user's manifest directory is not an omi repository.
        with patch.object(Path, "home", return_value=home), \
                patch.dict(os.environ, {"OMI_STATE": str(home / "state")}):
            output = io.StringIO()
            with contextlib.redirect_stderr(output):
                result = omi.project.scope.guard(io.StringIO(json.dumps({
                    "cwd": str(home), "tool_input": {"file_path": str(Path.home() / ".claude/settings.json")}})))
            assert (result, output.getvalue()) == (0, "")


def test_init_guard_status():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve()
        omi.setup.upgrade.init(root)
        assert (root / ".claude" / "settings.json").exists()
        assert (root / "AGENTS.md").exists() and not (root / "CLAUDE.md").exists()
        (root / "AGENTS.md").write_text("custom")
        omi.setup.upgrade.init(root)
        assert (root / "AGENTS.md").read_text() == "custom", "init must not overwrite"

        tasks = root / ".omi" / "tasks"
        (tasks / "TASK-001.md").write_text("---\ntitle: A\nstatus: in-progress\nscope: src/**\n---\n")
        (tasks / "TASK-002.md").write_text("---\ntitle: B\nstatus: planned\ndepends: TASK-001\n---\n")
        (tasks / "TASK-003.md").write_text("---\ntitle: C\nstatus: planned\n---\n")
        git(root, "add", "-A")
        git(root, "commit", "-qm", "init")
        git(root, "branch", "development")

        def guard(path, agent=None):
            payload = {"tool_input": {"file_path": str(path)}, "cwd": str(root), "hook_event_name": "PreToolUse",
                       "tool_name": "Write", **({"agent_id": "a1b2c3", "agent_type": agent} if agent else {})}
            return omi.project.scope.guard(io.BytesIO(json.dumps(payload).encode()))

        assert guard(root / "README.md") == 0, "no task running: main checkout is free"

        wt = root / "wt"
        git(root, "worktree", "add", "-q", str(wt), "-b", "task/TASK-001")
        (wt / ".omi" / "tasks" / "TASK-001.md").write_text(
            "---\ntitle: A\nstatus: in-progress\nscope: src/**\n---\n## Checkpoint\nNext: wire it\n")
        assert guard(wt / "src" / "new" / "deep.py") == 0
        assert guard(wt / ".omi" / "tasks" / "TASK-001.md") == 0
        assert guard(wt / "README.md") == 2
        assert guard(wt / ".omi" / "tasks" / "TASK-002.md") == 2
        assert guard(root / "src" / "x.py") == 2, "engineer escaping to main checkout"
        assert guard(root / ".omi" / "tasks" / "TASK-002.md") == 0, "coordinator state"
        assert guard(root / "docs" / "product.md") == 0

        # scope is read from development: widening the worktree copy changes nothing
        (wt / ".omi" / "tasks" / "TASK-001.md").write_text(
            "---\ntitle: A\nstatus: in-progress\nscope: **\n---\n## Checkpoint\nNext: wire it\n")
        assert guard(wt / "README.md") == 2, "self-widened scope"
        assert guard(wt / "src" / "ok.py", "omi-agent-engineer") == 0
        assert guard(wt / ".claude" / "settings.json", "omi-agent-engineer") == 2
        assert guard(root / "src" / "x.py", "omi-agent-engineer") == 2, "engineer writing to main checkout"
        with tempfile.TemporaryDirectory() as other:
            assert guard(Path(other) / "x.py", "omi-agent-engineer") == 2, "engineer writing to a non-git dir"
            assert guard(Path(other) / "x.py") == 0, "no agent identity: as before"
            assert guard(Path(other) / ".claude" / "settings.json") == 0, "user-level config outside omi"
            # A running omi task must not impose its guard on a different repository.
            git(other, "init", "-q", "-b", "task/TASK-1")
            assert guard(Path(other) / "x.py") == 0
            assert guard(Path(other) / ".claude" / "settings.json") == 0
        git(root, "branch", "task/TASK-099")
        git(root, "worktree", "add", "-q", str(root / "wt99"), "task/TASK-099")
        assert guard(root / "wt99" / "src" / "x.py") == 2, "task not on development: deny"
        git(root, "worktree", "remove", "--force", str(root / "wt99"))
        (wt / ".omi" / "tasks" / "TASK-001.md").write_text(
            "---\ntitle: A\nstatus: in-progress\nscope: src/**\n---\n## Checkpoint\nNext: wire it\n")

        out = io.StringIO()
        sys.stdout, real = out, sys.stdout
        try:
            omi.app.cli.status(root)
        finally:
            sys.stdout = real
        text = out.getvalue()
        assert "Next: wire it" in text and "next: TASK-003" in text, text
        assert "(step:" not in text
        (wt / ".omi" / "tasks" / "TASK-001.md").write_text(
            "---\ntitle: A\nstatus: in-progress\nstep: build\nscope: src/**\n---\n## Checkpoint\nNext: wire it\n")
        out.truncate(0); out.seek(0)
        sys.stdout = out
        try:
            omi.app.cli.status(root)
        finally:
            sys.stdout = real
        assert "TASK-001 A (step: build)" in out.getvalue(), out.getvalue()

        def show():
            out = io.StringIO()
            sys.stdout, real = out, sys.stdout
            try:
                omi.app.cli.status(root)
            finally:
                sys.stdout = real
            return out.getvalue()

        text = show()
        assert "ahead of development: 0, uncommitted: yes" in text and "stale" not in text, text
        git(wt, "commit", "-qam", "checkpoint")  # clean: checkpoint is the newest commit
        text = show()
        assert "ahead of development: 1, uncommitted: no" in text and "stale" not in text, text
        (wt / "src").mkdir()
        (wt / "src" / "a.py").write_text("x = 1")
        git(wt, "add", "-A")
        git(wt, "commit", "-qm", "code")  # stale: commit after the checkpoint
        text = show()
        assert "ahead of development: 2" in text and "checkpoint stale" in text, text

        git(root, "worktree", "remove", "--force", str(wt))
        assert guard(root / "README.md") == 0
        assert guard(root / ".claude" / "settings.json") == 2, "main checkout config, no worktree"
        assert guard(root / ".CLAUDE" / "Settings.json") == 2, "case-insensitive"


def test_template_docker():
    d = omi.common.core.TEMPLATE / "docker"
    text = (d / "Dockerfile").read_text()
    assert "python3" in text and "@anthropic-ai/claude-code@2." in text and (d / "prove.sh").exists()
    pins = json.loads((omi.common.core.TEMPLATE / "dot-omi" / "config.json").read_text())["cli_versions"]
    assert f"@openai/codex@{pins['codex']}" in text and f"claude-code@{pins['claude']}" in text
    assert pins["codex"] in (omi.common.core.TEMPLATE.parents[2] / "README.md").read_text(encoding="utf-8")
    assert "api.openai.com" not in json.loads((omi.common.core.TEMPLATE / "dot-omi" / "config.json").read_text())["network_allow"]
    assert "ca-certificates" in text
    prove = (d / "prove.sh").read_text()
    assert "codex exec" in prove and "OPENAI_API_KEY=sk-prove-invalid" in prove
    with tempfile.TemporaryDirectory() as t:
        out = io.StringIO()
        sys.stdout, saved = out, sys.stdout
        try:
            omi.setup.upgrade.init(t)
        finally:
            sys.stdout = saved
        assert (Path(t) / "docker" / "Dockerfile").exists()


def main():
    test_guard_non_omi_projects()
    test_guard_user_settings_outside_repository()
    test_step_settings_format_and_docs()
    test_template_docker()
    test_init_fresh_project()
    test_init_symlink_manifest()
    test_init_symlink_destinations()
    test_invalid_manifest_recovery()
    test_init_guard_status()


if __name__ == "__main__":
    main()
