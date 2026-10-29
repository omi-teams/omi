import io
import json
import contextlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
from helpers import omi, detached_cli, detached_project, git, state_remote


def test_attach_registration():
    from unittest.mock import patch
    with tempfile.TemporaryDirectory() as d:
        base = Path(d).resolve()
        code, home = base / "code", base / "state"
        code.mkdir()
        git(code, "init", "-q", "-b", "main")
        (code / "app.py").write_text("value = 1\n", encoding="utf-8")
        git(code, "add", ".")
        git(code, "commit", "-qm", "initial")
        git(code, "remote", "add", "origin", "git@EXAMPLE.org:team/sample.git")
        env = {"OMI_STATE": str(home), "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        before = {p.relative_to(code): p.read_bytes() for p in code.rglob("*") if p.is_file()}
        with patch.dict(os.environ, env):
            output = detached_cli(code, "attach")
            assert "private remote: git -C " in output
            project = home / "projects" / "sample"
            assert json.loads((project / "project.json").read_text(encoding="utf-8")) == {"remote": "git@EXAMPLE.org:team/sample.git"}
            assert not (project / "AGENTS.md").exists() and not (project / ".claude").exists()
            assert not (project / ".git").exists()
            wanted = {rel for rel in omi.upgrade.template_map() if rel != "AGENTS.md" and not rel.startswith(".claude/")}
            assert wanted <= {p.relative_to(project).as_posix() for p in project.rglob("*") if p.is_file()}
            assert (project / ".omi/hooks/post-run.sh").is_file() and (project / "docker/Dockerfile").is_file()
            assert omi.core.git(home, "status", "--porcelain") == ""
            assert omi.core.git(home, "log", "-1", "--format=%s") == "omi: attach sample"
            head = omi.core.git(home, "rev-parse", "HEAD")
            git(code, "remote", "set-url", "origin", "https://example.org/team/sample")
            assert "already attached:" in detached_cli(code, "attach", str(code))
            assert omi.core.git(home, "rev-parse", "HEAD") == head
            git(code, "remote", "set-url", "origin", "https://other.org/team/sample")
            try:
                detached_cli(code, "attach")
            except AssertionError as exc:
                assert "project already exists" in str(exc)
            else:
                raise AssertionError("project name collision accepted")
            git(code, "remote", "set-url", "origin", "git@EXAMPLE.org:team/sample.git")
        assert before == {p.relative_to(code): p.read_bytes() for p in code.rglob("*") if p.is_file()}
        with patch.dict(os.environ, env):
            with patch.dict(os.environ, {"OMI_STATE": str(code / "state")}):
                try:
                    omi.upgrade.attach([] if Path.cwd() == code else [str(code)])
                except omi.state.StateError as exc:
                    assert "outside the code repo" in str(exc)
                else:
                    raise AssertionError("state inside code accepted")
            # Existing staged work in state must not enter the attach commit.
            (home / "unrelated").write_text("keep staged\n", encoding="utf-8")
            git(home, "add", "unrelated")
            git(code, "remote", "set-url", "origin", "https://example.org/team/second.git")
            detached_cli(code, "attach")
            assert omi.core.git(home, "diff", "--cached", "--name-only") == "unrelated"
            assert "unrelated" not in omi.core.git(home, "ls-tree", "--name-only", "HEAD")


def test_detached_in_repo_warning():
    for paths, expected in (
        ((".omi/legacy.txt", ".omi/nested/other.txt"), ".omi/"),
        (("AGENTS.md",), "AGENTS.md"),
        ((".claude/settings.json",), ".claude/"),
        ((".omi/legacy.txt", "AGENTS.md", ".claude/settings.json"), ".omi/, AGENTS.md, .claude/"),
    ):
        with detached_project() as (code, project, wt, task):
            for rel in paths:
                path = code / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("legacy content\n", encoding="utf-8")
            git(code, "add", "--", *paths)
            git(code, "remote", "set-url", "origin", "https://example.org/team/second.git")
            before = {p.relative_to(code): p.read_bytes() for p in code.rglob("*")
                      if p.is_file() and ".git" not in p.relative_to(code).parts}
            staged = omi.core.git(code, "diff", "--cached")
            warning = "WARN: in-repo omi files ignored (detached): " + expected
            for cwd, args in ((code, ("attach",)), (wt, ("attach", str(wt))),
                              (code, ("status",)), (wt, ("status",))):
                output = detached_cli(cwd, *args)
                assert [line for line in output.splitlines() if line.startswith("WARN:")] == [warning], output
            assert staged == omi.core.git(code, "diff", "--cached")
            assert before == {p.relative_to(code): p.read_bytes() for p in code.rglob("*")
                              if p.is_file() and ".git" not in p.relative_to(code).parts}
            second = project.parent / "second"
            assert not (second / ".omi/legacy.txt").exists()
            assert not (second / "AGENTS.md").exists() and not (second / ".claude").exists()


def test_detached_in_repo_no_warning():
    with detached_project() as (code, project, wt, task):
        for files in ((), (".omi/local.txt", "AGENTS.md", ".claude/local.txt")):
            for rel in files:
                path = code / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("untracked\n", encoding="utf-8")
            # Similarly named tracked files must not match the top-level paths.
            for rel in ("AGENTS.md.bak", ".omi-extra/file", "nested/.claude/file"):
                path = code / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("tracked\n", encoding="utf-8")
                git(code, "add", "--", rel)
            git(code, "remote", "set-url", "origin", "https://example.org/team/second.git")
            for args in (("attach",), ("attach",), ("status",)):
                assert "WARN: in-repo omi files ignored" not in detached_cli(code, *args)


def test_in_repo_status_unchanged():
    with detached_project() as (code, project, wt, task):
        with patch.dict(os.environ, {"OMI_STATE": str(project.parent.parent / "unused")}):
            before = detached_cli(code, "status")
            for rel in (".omi/legacy.txt", "AGENTS.md", ".claude/legacy.txt"):
                path = code / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("legacy content\n", encoding="utf-8")
                git(code, "add", "--", rel)
            assert detached_cli(code, "status") == before


def test_attach_push_success():
    with detached_project() as (code, project, wt, task):
        home, remote, other = state_remote(project)
        previous = omi.core.git(home, "rev-parse", "HEAD")
        git(code, "remote", "set-url", "origin", "https://example.org/team/second.git")
        output = detached_cli(code, "attach")
        head = omi.core.git(home, "rev-parse", "HEAD")
        assert head != previous and "STATE NOT PUSHED" not in output
        assert omi.core.git(remote, "rev-parse", "refs/heads/main") == head
        assert omi.core.git(home, "status", "--porcelain") == ""


def test_attach_push_failure():
    with detached_project() as (code, project, wt, task):
        home, remote, other = state_remote(project)
        previous = omi.core.git(home, "rev-parse", "HEAD")
        git(home, "remote", "set-url", "origin", str(home.parent / "missing.git"))
        git(code, "remote", "set-url", "origin", "https://example.org/team/second.git")
        output = detached_cli(code, "attach")
        assert output.count("STATE NOT PUSHED: run omi sync") == 1
        assert omi.core.git(home, "rev-parse", "HEAD^") == previous
        assert omi.core.git(home, "log", "-1", "--format=%s") == "omi: attach second"
        assert (home / "projects/second/project.json").is_file()
        assert omi.core.git(home, "status", "--porcelain") == ""
        assert omi.core.git(remote, "rev-parse", "refs/heads/main") == previous
        git(home, "remote", "set-url", "origin", str(remote))
        assert "state synced" in detached_cli(code, "sync")
        assert omi.core.git(remote, "rev-parse", "refs/heads/main") == omi.core.git(home, "rev-parse", "HEAD")


def test_attach_development_created():
    for registered in (False, True):
        with detached_project() as (code, project, wt, task):
            git(code, "branch", "-m", "development", "main")
            git(code, "update-ref", "refs/remotes/origin/development", "HEAD")
            if not registered:
                git(code, "remote", "set-url", "origin", "https://example.org/team/second.git")
            head = omi.core.git(code, "rev-parse", "HEAD")
            before = {p.relative_to(code): p.read_bytes() for p in code.rglob("*")
                      if p.is_file() and ".git" not in p.relative_to(code).parts}
            output = detached_cli(code, "attach")
            assert output.splitlines().count("created development tracking origin/development") == 1
            assert omi.core.git(code, "rev-parse", "development") == head
            assert omi.core.git(code, "for-each-ref", "--format=%(upstream:short)", "refs/heads/development") == "origin/development"
            assert omi.core.git(code, "symbolic-ref", "--short", "HEAD") == "main"
            assert omi.core.git(code, "rev-parse", "HEAD") == head
            assert before == {p.relative_to(code): p.read_bytes() for p in code.rglob("*")
                              if p.is_file() and ".git" not in p.relative_to(code).parts}
            assert "created development" not in detached_cli(code, "attach")


def test_attach_development_present():
    with detached_project() as (code, project, wt, task):
        head = omi.core.git(code, "rev-parse", "HEAD")
        git(code, "checkout", "-qb", "main")
        git(code, "commit", "--allow-empty", "-qm", "remote development")
        git(code, "update-ref", "refs/remotes/origin/development", "HEAD")
        git(code, "config", "branch.development.remote", "origin")
        git(code, "config", "branch.development.merge", "refs/heads/main")
        git(code, "remote", "set-url", "origin", "https://example.org/team/second.git")
        before = {p.relative_to(code): p.read_bytes() for p in code.rglob("*") if p.is_file()}
        assert "created development" not in detached_cli(code, "attach")
        assert omi.core.git(code, "rev-parse", "development") == head
        assert omi.core.git(code, "config", "branch.development.merge") == "refs/heads/main"
        assert before == {p.relative_to(code): p.read_bytes() for p in code.rglob("*") if p.is_file()}


def test_attach_commit_failure_cleanup():
    from unittest.mock import patch
    for existing_commit in (False, True):
        with detached_project() as (code, project, wt, task):
            home = project.parent.parent
            if existing_commit:
                git(home, "add", ".")
                git(home, "commit", "-qm", "existing state")
            (home / "unrelated").write_text("keep staged\n", encoding="utf-8")
            git(home, "add", "unrelated")
            staged = omi.core.git(home, "diff", "--cached", "--name-only")
            git(code, "remote", "set-url", "origin", "https://example.org/team/second.git")
            before = {p.relative_to(code): p.read_bytes() for p in code.rglob("*") if p.is_file()}
            empty_config = home.parent / "empty.gitconfig"
            empty_config.write_text("", encoding="utf-8")
            # Windows drops empty env values, so remove identities and disable host config.
            failure_env = {key: value for key, value in os.environ.items()
                           if not key.startswith(("GIT_AUTHOR_", "GIT_COMMITTER_", "GIT_CONFIG_"))}
            failure_env.update({"GIT_CONFIG_GLOBAL": str(empty_config), "GIT_CONFIG_NOSYSTEM": "1",
                                "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "user.useConfigOnly",
                                "GIT_CONFIG_VALUE_0": "true"})
            result = subprocess.run([sys.executable, "-m", "omi", "attach"], cwd=code, env=failure_env,
                                    capture_output=True, encoding="utf-8", errors="replace")
            assert result.returncode == 1 and "OMI: git" in result.stderr, result
            assert "identity" in result.stderr.lower() and "Traceback" not in result.stderr, result.stderr
            assert not (home / "projects/second").exists()
            assert omi.core.git(home, "diff", "--cached", "--name-only") == staged
            with patch.dict(os.environ, {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                                         "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}):
                assert "attached:" in detached_cli(code, "attach")
            assert omi.core.git(home, "diff", "--cached", "--name-only") == staged
            assert before == {p.relative_to(code): p.read_bytes() for p in code.rglob("*") if p.is_file()}


def test_attach_init_failure_cleanup():
    from unittest.mock import patch
    with detached_project() as (code, project, wt, task):
        home = project.parent.parent
        git(code, "remote", "set-url", "origin", "https://example.org/team/second.git")
        real_init = omi.upgrade.init

        def failing_init(target, *, detached=False):
            real_init(target, detached=detached)
            raise OSError("template initialization failed")

        with patch.object(omi.upgrade, "init", side_effect=failing_init), contextlib.redirect_stdout(io.StringIO()):
            try:
                omi.upgrade.attach([str(code)])
            except OSError as exc:
                assert str(exc) == "template initialization failed"
            else:
                raise AssertionError("init failure ignored")
        assert not (home / "projects/second").exists()
        assert omi.core.git(home, "diff", "--cached", "--name-only") == ""
        with patch.dict(os.environ, {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                                     "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}):
            assert "attached:" in detached_cli(code, "attach")


def test_malformed_origin_cli():
    with detached_project() as (code, project, wt, task):
        remote = "https://[invalid"
        git(code, "remote", "set-url", "origin", remote)
        before = {p.relative_to(code): p.read_bytes() for p in code.rglob("*") if p.is_file()}
        for args in (["status"], ["attach"], ["attach", str(code)]):
            result = subprocess.run([sys.executable, "-m", "omi", *args], cwd=code,
                                    capture_output=True, encoding="utf-8", errors="replace")
            assert result.returncode == 1 and not result.stdout, result
            assert len(result.stderr.splitlines()) == 1 and result.stderr.startswith("OMI: "), result.stderr
            assert "invalid origin" in result.stderr and str(code) in result.stderr and remote in result.stderr, result.stderr
            assert "Traceback" not in result.stderr, result.stderr
        assert before == {p.relative_to(code): p.read_bytes() for p in code.rglob("*") if p.is_file()}


def test_attach_clone_portability():
    from unittest.mock import patch
    with tempfile.TemporaryDirectory() as d:
        base = Path(d).resolve()
        remote, code, home = base / "private.git", base / "code", base / "state"
        remote.mkdir()
        git(remote, "init", "--bare", "-q", "-b", "main")
        # Keep receive-pack from leaving background GC racing temporary cleanup.
        git(remote, "config", "receive.autogc", "false")
        git(remote, "config", "gc.auto", "0")
        code.mkdir()
        git(code, "init", "-q", "-b", "main")
        (code / "app.py").write_text("value = 1\n", encoding="utf-8")
        git(code, "add", ".")
        git(code, "commit", "-qm", "initial")
        git(code, "remote", "add", "origin", "https://example.org/team/sample.git")
        env = {"OMI_STATE": str(home), "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        with patch.dict(os.environ, env):
            assert "attached:" in detached_cli(code, "attach", "--state", str(remote))
            assert omi.core.git(home, "remote", "get-url", "origin") == str(remote)
            assert omi.core.git(home, "rev-parse", "--abbrev-ref", "@{upstream}") == "origin/main"
            assert omi.core.git(remote, "rev-parse", "refs/heads/main") == omi.core.git(home, "rev-parse", "HEAD")
            second_home, fresh = base / "second-state", base / "fresh-code"
            git(base, "clone", "-q", str(remote), str(second_home))
            git(base, "clone", "-q", str(code), str(fresh))
            git(fresh, "remote", "set-url", "origin", "git@EXAMPLE.org:team/sample.git")
            with patch.dict(os.environ, {"OMI_STATE": str(second_home)}):
                assert omi.state.resolve(fresh) == omi.state.Project(second_home / "projects/sample", fresh, True)
                assert "already attached:" in detached_cli(fresh, "attach")
            # With no override, initialization uses ~/.omi/state.
            with patch.dict(os.environ), patch.object(Path, "home", return_value=base / "user"):
                os.environ.pop("OMI_STATE", None)
                assert "private remote:" in detached_cli(code, "attach")
                assert (base / "user/.omi/state/projects/sample/project.json").is_file()


def test_invalid_registry_cli():
    with detached_project() as (code, project, wt, task):
        manifest = project / "project.json"
        commands = [[], ["help"], ["version"], ["--version"], ["init"], ["attach"], ["upgrade", "--apply"],
                    ["status"], ["guard"], ["github"], ["clean"], ["skills"], ["rules"], ["plans"], ["references"],
                    ["agents"], ["workflows"], ["step", "TASK-097", "next"], ["run", "omi-agent-engineer", "TASK-097"],
                    ["hook", "post-run", "TASK-097"], ["parallel", "A", "B"], ["worker", "x"], ["token", "set"],
                    ["template-shas", "x", "v1.0.0"], ["session-start"], ["install-user"], ["install-user", "--remove"]]
        duplicate = project.parent / "duplicate/project.json"
        duplicate.parent.mkdir()
        for data in (b"{", b"[]", b'{"remote":""}', b'{"remote":"https://[invalid"}', b'\xff', b'{"remote":"https://example.org/team/sample.git"}'):
            duplicate.write_bytes(data)
            for args in commands:
                out = io.StringIO()
                with contextlib.chdir(code), contextlib.redirect_stdout(out):
                    try:
                        omi.cli.main(args)
                    except SystemExit as exc:
                        message = str(exc.code)
                        assert len(message.splitlines()) == 1 and message.startswith("OMI: "), (args, message)
                        assert str(duplicate) in message, (args, message)
                    else:
                        raise AssertionError(f"invalid registry accepted by {args}")
                assert not out.getvalue(), (args, out.getvalue())
            result = subprocess.run([sys.executable, "-m", "omi", "status"], cwd=code,
                                    capture_output=True, encoding="utf-8", errors="replace")
            assert result.returncode == 1 and result.stdout == "", result
            assert len(result.stderr.splitlines()) == 1 and result.stderr.startswith("OMI: "), result.stderr
            assert str(duplicate) in result.stderr and "Traceback" not in result.stderr, result.stderr
            if data.startswith(b'{"remote":"https:') and b"invalid" not in data:
                assert str(manifest) in result.stderr


def test_state_sync():
    """Real bare remote: refresh, selective commits, leftovers and failed pushes."""
    from unittest.mock import patch
    with detached_project() as (code, project, wt, task):
        home, remote, other = state_remote(project)
        peer_task = other / task.relative_to(home)
        peer_task.write_text(peer_task.read_text(encoding="utf-8").replace("Detached test", "Remote title"), encoding="utf-8")
        git(other, "add", ".")
        git(other, "commit", "-qm", "remote update")
        git(other, "push", "-q")
        assert "Remote title" in detached_cli(code, "status")
        unrelated = home / "unrelated.txt"
        unrelated.write_text("staged elsewhere", encoding="utf-8")
        git(home, "add", "unrelated.txt")
        leftover = project / ".omi" / "decisions.md"
        leftover.write_text("manual decision", encoding="utf-8")
        detached_cli(wt, "step", task.stem, "next")
        assert omi.core.git(home, "show", "--format=", "--name-only", "HEAD") == task.relative_to(home).as_posix()
        assert omi.core.git(home, "log", "-1", "--format=%s") == "chore(sample): step state"
        assert omi.core.git(home, "diff", "--cached", "--name-only") == "unrelated.txt"
        assert omi.core.git(home, "rev-parse", "HEAD") == omi.core.git(other, "ls-remote", "origin", "refs/heads/main").split()[0]
        # A failed push leaves the command's local commit intact.
        git(home, "remote", "set-url", "origin", str(remote.parent / "missing.git"))
        out = detached_cli(code, "step", task.stem, "done")
        assert "STATE NOT PUSHED: run omi sync" in out
        kept = omi.core.git(home, "rev-parse", "HEAD")
        assert "state pull skipped:" in detached_cli(code, "status")
        assert omi.core.git(home, "rev-parse", "HEAD") == kept
        try:
            detached_cli(code, "sync")
        except AssertionError as exc:
            assert "STATE NOT PUSHED: run omi sync" in str(exc), exc
        else:
            raise AssertionError("sync must fail when push fails")
        git(home, "remote", "set-url", "origin", str(remote))
        unrelated.write_text("updated elsewhere", encoding="utf-8")
        leftover.write_text("updated decision", encoding="utf-8")
        assert "state synced" in detached_cli(code, "sync")
        assert omi.core.git(home, "status", "--porcelain") == ""
        assert omi.core.git(home, "rev-parse", "HEAD") == omi.core.git(other, "ls-remote", "origin", "refs/heads/main").split()[0]
        assert set(omi.core.git(home, "show", "--format=", "--name-only", "HEAD").splitlines()) == {
            "unrelated.txt", leftover.relative_to(home).as_posix()}
        # Manual task start/done and plan/decision edits are picked up together.
        task.write_text(task.read_text(encoding="utf-8").replace("status: in-progress", "status: done"), encoding="utf-8")
        plan = project / ".omi" / "plans" / "PLAN-099.md"
        plan.write_text("plan update", encoding="utf-8")
        leftover.write_text("decision update", encoding="utf-8")
        assert "state synced" in detached_cli(code, "sync")
        assert omi.core.git(home, "status", "--porcelain") == ""
        # Both staged and unstaged deletions are committed by sync.
        git(home, "rm", "--", plan.relative_to(home).as_posix())
        leftover.unlink()
        assert "state synced" in detached_cli(code, "sync")
        assert omi.core.git(home, "status", "--porcelain") == ""
        # Offline exceptions and a repository without a remote both remain readable.
        real_git = omi.state_sync.git
        def offline(root, *args):
            if args[0] == "pull":
                raise omi.state.StateError("offline")
            return real_git(root, *args)
        with patch.object(omi.state_sync, "git", side_effect=offline):
            assert "state pull skipped: offline" in detached_cli(code, "status")
        git(home, "remote", "remove", "origin")
        assert "state pull skipped: no remote" in detached_cli(code, "status")
        assert "state synced" in detached_cli(code, "sync")
        git(home, "remote", "add", "origin", str(remote))
        assert "state synced" in detached_cli(code, "sync")
        assert omi.core.git(home, "rev-parse", "--abbrev-ref", "@{upstream}") == "origin/main"


def test_state_sync_conflict():
    """Rebase conflicts list files and stop before committing or pushing leftovers."""
    with detached_project() as (code, project, wt, task):
        home, remote, other = state_remote(project)
        peer_task = other / task.relative_to(home)
        for root, path, title in ((home, task, "Local"), (other, peer_task, "Peer")):
            path.write_text(path.read_text(encoding="utf-8").replace("Detached test", title), encoding="utf-8")
            git(root, "add", ".")
            git(root, "commit", "-qm", title)
        git(other, "push", "-q")
        remote_head = omi.core.git(other, "rev-parse", "HEAD")
        leftover = home / "uncommitted.txt"
        leftover.write_text("keep untouched", encoding="utf-8")
        for attempt in range(2):
            try:
                detached_cli(code, "sync")
            except AssertionError as exc:
                assert "state rebase conflict:" in str(exc) and "TASK-097.md" in str(exc), exc
            else:
                raise AssertionError("conflict accepted")
            assert omi.core.git(other, "ls-remote", "origin", "refs/heads/main").split()[0] == remote_head
            assert leftover.read_text(encoding="utf-8") == "keep untouched"
            assert omi.core.git(home, "ls-files", "--", "uncommitted.txt") == ""
        assert omi.core.git(home, "diff", "--name-only", "--diff-filter=U") == task.relative_to(home).as_posix()


def main():
    test_detached_in_repo_warning()
    test_detached_in_repo_no_warning()
    test_in_repo_status_unchanged()
    test_state_sync()
    test_state_sync_conflict()
    test_attach_registration()
    test_attach_push_success()
    test_attach_push_failure()
    test_attach_development_created()
    test_attach_development_present()
    test_attach_commit_failure_cleanup()
    test_attach_init_failure_cleanup()
    test_malformed_origin_cli()
    test_attach_clone_portability()
    test_invalid_registry_cli()


if __name__ == "__main__":
    main()
