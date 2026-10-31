import io
import shutil
import json
import contextlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
from helpers import omi, detached_cli, detached_project, git


def test_detached_resolution():
    from unittest.mock import patch
    for url in ("https://EXAMPLE.org/team/sample.git/", "ssh://git@example.org/team/sample.git",
                "git@EXAMPLE.org:team/sample", "example.org/team/sample"):
        assert omi.state.resolve.normalise_url(url) == "example.org/team/sample"
    assert omi.state.resolve.normalise_url("https://example.org/Team/Sample.git") == "example.org/Team/Sample"
    with detached_project() as (code, project, wt, task):
        for cwd in (code, wt, wt / "subdir"):
            cwd.mkdir(exist_ok=True)
            found = omi.state.resolve.resolve(cwd)
            assert found == omi.state.resolve.Project(project, code, True)
            assert omi.state.resolve.resolve(found) is found
            assert omi.state.resolve.task_file(found, task.stem) == task
        with patch.dict(os.environ), patch.object(Path, "home", return_value=project.parent):
            os.environ.pop("OMI_STATE", None)
            default = project.parent / ".omi" / "state"
            assert omi.state.resolve.state_home() == default
            assert not omi.state.resolve.resolve(code).detached
            registered = default / "projects" / "other-name"
            registered.mkdir(parents=True)
            shutil.copyfile(project / "project.json", registered / "project.json")
            assert omi.state.resolve.resolve(wt) == omi.state.resolve.Project(registered, code, True)
        with patch.dict(os.environ, {"OMI_STATE": str(project / "missing")}):
            assert omi.state.resolve.resolve(wt) == omi.state.resolve.Project(wt, code)
        manifest = project / "project.json"
        manifest.write_text('{"remote":"https://example.org/elsewhere.git"}', encoding="utf-8")
        assert not omi.state.resolve.resolve(code).detached
        manifest.write_text('{"remote":"example.org/team/sample"}', encoding="utf-8")
        duplicate = project.parent / "duplicate"
        duplicate.mkdir()
        shutil.copyfile(manifest, duplicate / "project.json")
        try:
            omi.state.resolve.resolve(code)
        except ValueError as e:
            assert "multiple detached projects" in str(e)
        else:
            raise AssertionError("ambiguous registry accepted")
        (duplicate / "project.json").write_text("[]", encoding="utf-8")
        try:
            omi.state.resolve.resolve(code)
        except ValueError as e:
            assert "expected a remote string" in str(e)
        else:
            raise AssertionError("invalid registry accepted")


def test_detached_commands_and_steps():
    from unittest.mock import patch
    with detached_project() as (code, project, wt, task):
        head = omi.common.core.git(code, "rev-parse", "HEAD")
        with patch.object(omi.worker.docker, "running_workers", return_value=[]), \
                patch.object(omi.worker.docker, "full_volumes", return_value=[]):
            out = detached_cli(wt, "status")
        assert "branch: task/TASK-097" in out and "Detached test" in out
        reported_wt = next(line.strip().removeprefix("worktree: ") for line in out.splitlines()
                           if line.strip().startswith("worktree: "))
        assert Path(reported_wt) == wt  # Git uses forward slashes on Windows too.
        assert "skills ok" in detached_cli(code, "skills", "check", ".omi/tasks/TASK-097.md")
        for cmd in ("plans", "rules", "references", "skills", "agents", "workflows"):
            assert str(project) in detached_cli(wt, cmd)
        detached_cli(code, "skills", "--check")
        detached_cli(code, "workflows", "--check")
        for step in ("plan", "build", "review", "accept"):
            detached_cli(wt, "step", task.stem, "next")
            assert omi.common.core.meta(task)["step"] == step
            if step == "accept":
                omi.project.tasks.append_note(task, "Steps", "PO approval accept: approved in test")
            detached_cli(code, "step", task.stem, "done")
        assert "complete" in detached_cli(wt, "step", task.stem, "next")
        assert omi.project.tasks.step_states(task.read_text(encoding="utf-8")) == dict.fromkeys(
            ("plan", "build", "review", "accept"), "done")
        assert omi.common.core.git(code, "rev-parse", "HEAD") == head
        assert omi.common.core.git(code, "status", "--porcelain") == ""
        assert omi.common.core.git(wt, "status", "--porcelain") == ""
        assert not (code / ".omi").exists() and not (wt / ".omi").exists()


def test_detached_project_commands():
    from unittest.mock import patch
    with detached_project() as (code, project, wt, task):
        detached_cli(wt, "init")
        assert not (project / ".git").exists()
        assert omi.common.core.main_checkout(project) == project.parents[1]
        detached_cli(code, "upgrade", "--apply")
        assert not (project / "AGENTS.md").exists() and not (project / ".claude").exists()
        assert (project / ".omi" / "version").read_text(encoding="utf-8").strip() == omi.common.core.version()
        def github_call(po):
            assert Path.cwd() == code and not po
        with patch.object(omi.project.github, "github", side_effect=github_call) as github:
            detached_cli(wt, "github")
            github.assert_called_once_with(False)
        # Both cleanup and status identify workers by the detached project, not its shared state repo.
        real_run, calls = subprocess.run, []
        def execute(argv, **kw):
            if argv[0] != "docker":
                return real_run(argv, **kw)
            calls.append(argv)
            return subprocess.CompletedProcess(argv, 0, "", "")
        with patch.object(subprocess, "run", side_effect=execute):
            detached_cli(wt, "clean")
            detached_cli(wt, "status")
        assert any("label=omi-repo=sample" in argv for argv in calls if argv[:2] == ["docker", "ps"])
        assert not any("label=omi-repo=state" in argv for argv in calls)
        task2 = task.with_name("TASK-098.md")
        task2.write_text("---\nid: TASK-098\nstatus: planned\nscope: other.py\n---\n", encoding="utf-8")
        assert "parallel ok" in detached_cli(wt, "parallel", task.stem, task2.stem)
        assert omi.common.core.git(code, "status", "--porcelain") == ""
        assert omi.common.core.git(wt, "status", "--porcelain") == ""


def test_detached_scope_and_guard():
    with detached_project() as (code, project, wt, task):
        assert omi.project.scope.task_scope(wt, task.stem) == ["app.py"]
        (wt / "app.py").write_text("value = 2\n", encoding="utf-8")
        (wt / "outside.py").write_text("bad\n", encoding="utf-8")
        assert omi.project.scope.out_of_scope(wt, task.stem) == ["outside.py"]
        git(wt, "add", "app.py", "outside.py")
        git(wt, "commit", "-qm", "scope fixture")
        assert omi.project.scope.out_of_scope(wt, task.stem, committed=True) == ["outside.py"]
        assert omi.project.tasks.drift(wt, task.stem) == "ahead of development: 1, uncommitted: no"
        def guard(path):
            return omi.project.scope.guard(io.StringIO(json.dumps({"cwd": str(wt), "agent_type": "omi-agent-engineer",
                                                          "tool_input": {"file_path": str(path)}})))
        assert guard(wt / "app.py") == 0
        assert guard(wt / "outside.py") == 2
        assert guard(task) == 2
        assert guard(code / ".claude/settings.json") == 2
        assert guard(wt / ".claude/settings.json") == 2
        with tempfile.TemporaryDirectory() as other:
            git(other, "init", "-q", "-b", "task/TASK-1")
            for target in (Path(other) / "app.py", Path(other) / ".claude/settings.json"):
                assert omi.project.scope.guard(io.StringIO(json.dumps({
                    "cwd": str(wt), "tool_input": {"file_path": str(target)}}))) == 2
        with tempfile.TemporaryDirectory() as home:
            assert omi.project.scope.guard(io.StringIO(json.dumps({
                "cwd": str(wt), "tool_input": {"file_path": str(Path(home) / ".claude/settings.json")}}))) == 2
        # A counterfeit task in the code worktree cannot widen detached scope.
        fake = wt / ".omi" / "tasks" / task.name
        fake.parent.mkdir(parents=True)
        fake.write_text("---\nscope: **\n---\n", encoding="utf-8")
        assert omi.project.scope.task_scope(wt, task.stem) == ["app.py"]
        assert omi.project.scope.out_of_scope(wt, task.stem) == [".omi/tasks/TASK-097.md"]
        assert guard(fake) == 2
        task.write_text(task.read_text(encoding="utf-8").replace(
            "scope: app.py", "scope: app.py, .claude/settings.json"), encoding="utf-8")
        assert guard(wt / ".claude/settings.json") == 0


def test_detached_run_and_hooks():
    from unittest.mock import patch
    real_run = subprocess.run
    with detached_project() as (code, project, wt, task):
        calls = []
        def execute(argv, **kw):
            if argv[0] != "docker":
                return real_run(argv, **kw)
            calls.append((argv, kw))
            if argv[:2] == ["docker", "run"]:
                if argv[-2:] == ["sh", "-s"]:
                    return subprocess.CompletedProcess(argv, 0, b"state hook\n", b"")
                result = ({"result": "DONE detached", "usage": {}} if "claude" in argv else
                          {"type": "item.completed", "item": {"type": "agent_message", "text": "DONE detached"}})
                return subprocess.CompletedProcess(argv, 0, json.dumps(result), "")
            return subprocess.CompletedProcess(argv, 0, "", "")
        with patch.object(subprocess, "run", side_effect=execute), \
                patch.object(omi.worker.docker, "need_docker"), \
                patch.object(omi.worker.creds, "claude_auth", return_value=(omi.worker.creds.TOKEN_ENV, "fake", None)), \
                patch.object(omi.worker.creds, "tool_secret", return_value=(omi.worker.creds.CODEX_ENV, "fake", None)):
            for tool in ("claude", "codex"):
                detached_cli(code, "run", "omi-agent-engineer", task.stem, "--tool", tool)
                argv = next(a for a, _ in reversed(calls) if a[:2] == ["docker", "run"] and tool in a)
                assert f"{project}:/state:ro" in argv and f"{wt}:/work" in argv
                prompt = argv[argv.index("-p") + 1] if tool == "claude" else argv[-1]
                assert "Task file: /state/.omi/tasks/TASK-097.md" in prompt
                assert "/state/.omi/skills/" in prompt and "read-only" in prompt
                assert "/state/.omi/rules/python.md" in prompt
                assert "/state/.omi/references/postgres-conventions.md" in prompt
                assert (project / ".omi" / "skills" / "CATALOG.md").is_file()
                assert "Do not edit the task or catalogs" in prompt
                system = argv[argv.index("--append-system-prompt") + 1] if tool == "claude" else prompt
                assert "replace instructions to edit the task" in system
                assert "Tests: python3 -c 'print(123)'" in prompt
                assert str(project) not in prompt
            # The shared repo stores the project prefix.
            committed = omi.common.core.git(project, "show", f"HEAD:projects/sample/.omi/tasks/{task.name}")
            assert "DONE detached" in committed and "## Usage" in committed
            detached_cli(wt, "hook", "post-run", task.stem)
            argv, kwargs = next((a, k) for a, k in reversed(calls) if a[:2] == ["docker", "run"])
            assert f"{project}:/state:ro" in argv and f"{wt}:/work:ro" in argv
            assert "OMI_PROJECT_STATE=/state" in argv
            assert kwargs["input"] == (project / ".omi" / "hooks" / "post-run.sh").read_bytes().replace(b"\r\n", b"\n")
            report = task.read_text(encoding="utf-8")
            assert "DONE detached" in report and "hook post-run passed" in report and "## Usage" in report
            # Read roles validate the detached catalogs and code tests before launching.
            with patch.object(omi.project.catalogs, "check_all_skills", wraps=omi.project.catalogs.check_all_skills) as check, \
                    patch.object(omi.worker.run, "test_command", return_value=[sys.executable, "-c", "print('code tests')"]):
                detached_cli(wt, "run", "omi-agent-reviewer", task.stem)
                check.assert_called_once_with(project)
            argv = next(a for a, _ in reversed(calls) if a[:2] == ["docker", "run"] and "claude" in a)
            assert f"{wt}:/work:ro" in argv and f"{project}:/state:ro" in argv
        assert omi.common.core.git(code, "status", "--porcelain") == ""
        assert omi.common.core.git(wt, "status", "--porcelain") == ""


def test_detached_default_hook_config():
    """The shipped hook must read detached config while running tests in the code worktree."""
    with detached_project() as (code, project, wt, task):
        hook = project / ".omi" / "hooks" / "post-run.sh"
        local_cfg = wt / ".omi" / "config.json"
        local_cfg.parent.mkdir()
        local_cfg.write_text(json.dumps({"test": "exit 9"}), encoding="utf-8")
        for root in (project, project / "state with spaces"):
            cfg = root / ".omi" / "config.json"
            cfg.parent.mkdir(parents=True, exist_ok=True)
            cfg.write_text(json.dumps({"test": "test -f app.py && exit 7"}), encoding="utf-8")
            result = subprocess.run([omi.worker.run.host_bash() or "sh", str(hook)], cwd=wt,
                                    env={**os.environ, "OMI_PROJECT_STATE": root.as_posix()},
                                    capture_output=True, encoding="utf-8", errors="replace")
            assert result.returncode == 7, ("detached hook ignored state config or code cwd", result.stdout, result.stderr)
        for value in (None, ""):
            env = {k: v for k, v in os.environ.items() if k != "OMI_PROJECT_STATE"}
            if value is not None:
                env["OMI_PROJECT_STATE"] = value
            result = subprocess.run([omi.worker.run.host_bash() or "sh", str(hook)], cwd=wt, env=env,
                                    capture_output=True, encoding="utf-8", errors="replace")
            assert result.returncode == 9, ("in-repo hook ignored local config", result.stdout, result.stderr)


def test_user_session_start():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        for detached in (False, True):
            project = omi.state.resolve.Project(root, root, detached)
            output = io.StringIO()
            output.reconfigure = lambda **kw: None
            with patch("omi.state.resolve.resolve", return_value=project), patch("omi.app.cli.status") as status, contextlib.redirect_stdout(output):
                omi.app.cli.dispatch(["session-start"])
            assert status.call_count == int(detached)
            assert output.getvalue() == (omi.setup.install.coordinator_rules() + "\n" + f"omi state: {root}\n" if detached else "")
    with detached_project() as (code, project, wt, task):
        output = detached_cli(code, "session-start")
        assert "You are the **Coordinator**" in output and "omi state:" in output and "branch:" in output
        assert "TASK-097" in output


def main():
    test_user_session_start()
    test_detached_resolution()
    test_detached_commands_and_steps()
    test_detached_project_commands()
    test_detached_scope_and_guard()
    test_detached_run_and_hooks()
    test_detached_default_hook_config()


if __name__ == "__main__":
    main()
