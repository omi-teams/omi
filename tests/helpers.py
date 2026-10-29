"""Shared fakes and fixtures for the test files; importing it sets up the test environment."""
import io
import json
import contextlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
import omi  # noqa: E402

os.environ["CODEX_HOME"] = tempfile.mkdtemp()  # no host ChatGPT login unless a test writes one
os.environ["CLAUDE_CONFIG_DIR"] = tempfile.mkdtemp()  # no host Claude Code login unless a test writes one

real_egress = omi.worker.docker.egress  # other tests run workers with docker mocked: no proxy


@contextlib.contextmanager
def no_egress(main, name, image, allow):
    yield f"omi-net-{name}", f"{name}-proxy"


omi.worker.docker.egress = no_egress


def git(cwd, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
                   cwd=cwd, check=True, capture_output=True)


class FakePopen:
    """`docker run` as a Popen whose stderr is read line by line; it asks the (mocked) subprocess.run for the result.
    Every other command goes to the real Popen."""
    real = subprocess.Popen

    def __new__(cls, cmd, **kw):
        if cmd[:2] != ["docker", "run"]:
            return cls.real(cmd, **kw)
        self = object.__new__(cls)
        r = subprocess.run(cmd, **kw)
        dec = lambda b: b.decode(kw.get("encoding") or "cp1252", kw.get("errors") or "strict") if isinstance(b, bytes) else b  # Windows locale
        self.stdout, self.stderr, self.returncode = io.StringIO(dec(r.stdout)), io.StringIO(dec(r.stderr)), r.returncode
        return self

    def __enter__(self): return self
    def __exit__(self, *a): pass
    def wait(self): return self.returncode


subprocess.Popen = FakePopen


def assert_download_cache_env(argv):
    env = [arg for i, arg in enumerate(argv) if i and argv[i - 1] == "-e"]
    for kv in ("XDG_CACHE_HOME=/cache", "GOCACHE=/cache/go-build", "GOTMPDIR=/cache",
               "GOMODCACHE=/work/.omi-cache/go-mod", "npm_config_cache=/work/.omi-cache/npm",
               "PIP_CACHE_DIR=/work/.omi-cache/pip", "GOFLAGS=-modcacherw"):
        assert kv in env, (kv, env)


@contextlib.contextmanager
def detached_project():
    """A real code repo/worktree and a separate registry, never touching host state."""
    from unittest.mock import patch
    with tempfile.TemporaryDirectory() as d:
        base = Path(d).resolve()
        code, home = base / "code", base / "state"
        project = home / "projects" / "sample"
        code.mkdir()
        git(code, "init", "-q", "-b", "development")
        (code / "app.py").write_text("value = 1\n", encoding="utf-8")
        git(code, "add", "app.py")
        git(code, "commit", "-qm", "initial code")
        git(code, "remote", "add", "origin", "git@EXAMPLE.org:team/sample.git")
        with patch.dict(os.environ, {"OMI_STATE": str(home), "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")}):
            with contextlib.redirect_stdout(io.StringIO()):
                omi.setup.upgrade.init(project, detached=True)
            git(home, "init", "-q", "-b", "main")
            (project / "project.json").write_text(json.dumps({"remote": "https://example.org/team/sample"}), encoding="utf-8")
            cfg = project / ".omi" / "config.json"
            data = json.loads(cfg.read_text(encoding="utf-8"))
            data["test"] = "python3 -c 'print(123)'"
            cfg.write_text(json.dumps(data), encoding="utf-8")
            task = project / ".omi" / "tasks" / "TASK-097.md"
            task.write_text("---\nid: TASK-097\ntitle: Detached test\nstatus: in-progress\n"
                            "scope: app.py\nrole: omi-agent-engineer\nworkflow: omi-flow-feature\n"
                            "skills: omi-skill-lean-implementation\nrefs: postgres-conventions\n---\n## Acceptance criteria\n- [x] test\n\n## Checkpoint\nDone:\n",
                            encoding="utf-8")
            wt = base / "code.wt" / "TASK-097"
            git(code, "worktree", "add", "-qb", "task/TASK-097", str(wt))
            yield code, project, wt, task


def detached_cli(cwd, *args):
    from unittest.mock import patch
    out = io.StringIO()
    out.reconfigure = lambda **kw: None
    with contextlib.chdir(cwd), contextlib.redirect_stdout(out), patch.dict(os.environ, {
            "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}):
        try:
            omi.app.cli.main(list(args))
        except SystemExit as e:
            assert e.code in (None, 0), (e, out.getvalue())
    return out.getvalue()


def state_remote(project):
    home = project.parents[1]
    remote = home.parent / "remote.git"
    git(home.parent, "init", "--bare", "-q", str(remote))
    # Keep receive-pack from leaving background GC racing temporary cleanup.
    git(remote, "config", "receive.autogc", "false")
    git(remote, "config", "gc.auto", "0")
    git(home, "add", ".")
    git(home, "commit", "-qm", "initial state")
    git(home, "remote", "add", "origin", str(remote))
    git(home, "push", "-qu", "origin", "main")
    other = home.parent / "other"
    git(home.parent, "clone", "-q", "-b", "main", str(remote), str(other))
    return home, remote, other
