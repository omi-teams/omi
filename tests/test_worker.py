import io
import re
import shutil
import json
import importlib.metadata
import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from helpers import omi, assert_download_cache_env, git, real_egress


def test_download_cache_gitignore():
    for apply in (omi.setup.upgrade.init, lambda root: omi.setup.upgrade.upgrade_cmd(["--apply"], root)):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            ignore = root / ".gitignore"
            apply(root)
            assert ignore.read_text(encoding="utf-8") == "__pycache__/\n.omi-cache/\n"
            for existing in ("", "*.log", ".omi-cache", "/.omi-cache/", ".omi-cache/"):
                ignore.write_text("__pycache__/\n" + existing, encoding="utf-8")
                apply(root)
                expected = ["__pycache__/"] + ([existing] if existing else [])
                if existing in ("", "*.log"):
                    expected.append(".omi-cache/")
                assert ignore.read_text(encoding="utf-8").splitlines() == expected
                before = ignore.read_bytes()
                apply(root)
                assert ignore.read_bytes() == before
            # Git's actual ignore matching covers download cache contents.
            git(root, "init", "-q")
            git(root, "check-ignore", ".omi-cache/go-mod/example/file", ".omi-cache/npm/pkg", ".omi-cache/pip/pkg")
    root = Path(__file__).parents[1]
    assert ".omi-cache/" in (root / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "Cache tải xuống (Go modules, npm, pip) nằm trong `.omi-cache/`" in (root / "README.md").read_text(encoding="utf-8")


def test_download_cache_shared_exclude():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve() / "main"
        root.mkdir()
        git(root, "init", "-q", "-b", "development")
        (root / ".gitignore").write_text("*.log\n", encoding="utf-8")
        task = root / ".omi" / "tasks" / "TASK-087.md"
        task.parent.mkdir(parents=True)
        task.write_text("---\nid: TASK-087\nscope: src/**\n---\n", encoding="utf-8")
        git(root, "add", ".")
        git(root, "commit", "-qm", "base")
        wt = Path(d).resolve() / "task"
        git(root, "worktree", "add", "-qb", "task-087", str(wt))
        exclude = root / ".git" / "info" / "exclude"
        exclude.unlink()
        exclude.parent.rmdir()

        def statuses():
            return [omi.common.core.git(p, "status", "--porcelain", "-uall") for p in (root, wt)]

        before = statuses()
        assert before == ["", ""]
        omi.worker.run.ensure_cache_excluded(wt)
        assert exclude.read_text(encoding="utf-8") == ".omi-cache/\n"
        assert statuses() == before
        for existing in ("*.local", "# preserved\n*.local\n", "*.local\n.omi-cache/\n"):
            exclude.write_text(existing, encoding="utf-8")
            omi.worker.run.ensure_cache_excluded(wt)
            expected = existing if ".omi-cache/" in existing.splitlines() else existing.rstrip("\n") + "\n.omi-cache/\n"
            assert exclude.read_text(encoding="utf-8") == expected
            first = exclude.read_bytes()
            omi.worker.run.ensure_cache_excluded(root)
            assert exclude.read_bytes() == first
            assert statuses() == before

        # Older projects have no tracked cache ignore; the shared exclude hides .git* cache paths.
        exclude.write_text("*.local\n", encoding="utf-8")
        cached = wt / ".omi-cache" / "go-mod" / "example.com" / "m@v1" / ".github" / "workflows" / "x.yml"
        cached.parent.mkdir(parents=True)
        cached.write_text("downloaded\n", encoding="utf-8")
        cache_rel = cached.relative_to(wt).as_posix()
        assert omi.project.scope.out_of_scope(wt, "TASK-087") == [cache_rel]
        omi.worker.run.ensure_cache_excluded(wt)
        assert omi.project.scope.out_of_scope(wt, "TASK-087") == []
        assert omi.project.scope.out_of_scope(wt, "TASK-087", committed=True) == []
        assert statuses() == before
        git(root, "check-ignore", cache_rel)
        git(wt, "check-ignore", cache_rel)
        git(wt, "add", "-f", cache_rel)
        git(wt, "commit", "-qm", "tracked cache")
        assert omi.project.scope.out_of_scope(wt, "TASK-087", committed=True) == [cache_rel]
        cached.write_text("changed tracked cache\n", encoding="utf-8")
        assert omi.project.scope.out_of_scope(wt, "TASK-087") == [cache_rel]


def test_download_cache_scope():
    real = subprocess.run, omi.project.scope.task_scope
    try:
        omi.project.scope.task_scope = lambda *args: ["src/**"]
        def run(argv, **kw):
            if "rev-parse" in argv or "remote" in argv:
                return subprocess.CompletedProcess(argv, 1, "")
            paths = ("?? .omi-cache/go-mod/example/file\0?? .omi-cache/npm/pkg/.github/config\0"
                     "?? .omi-cache/pip/pkg\0!! .omi-cache/npm/ignored\0 M .omi-cache/pip/tracked\0"
                     "?? .omi-cache-other/file\0?? src/ok.py\0?? outside.py\0")
            diff = ".omi-cache/x/.gitattributes\0.omi-cache/go-mod/x\0"
            return subprocess.CompletedProcess(argv, 0, paths if "status" in argv else diff)
        subprocess.run = run
        with tempfile.TemporaryDirectory() as d:
            assert omi.project.scope.out_of_scope(d, "TASK-086") == [
                ".omi-cache/npm/pkg/.github/config", ".omi-cache/pip/tracked", ".omi-cache-other/file", "outside.py"]
            assert omi.project.scope.out_of_scope(d, "TASK-086", committed=True) == [
                ".omi-cache/go-mod/example/file", ".omi-cache/npm/pkg/.github/config", ".omi-cache/pip/pkg",
                ".omi-cache/npm/ignored", ".omi-cache/pip/tracked", ".omi-cache-other/file", "outside.py",
                ".omi-cache/x/.gitattributes", ".omi-cache/go-mod/x"]
    finally:
        subprocess.run, omi.project.scope.task_scope = real


def test_worker():
    real = subprocess.run, shutil.which, omi.common.core.main_checkout, omi.common.core.WINDOWS, os.environ.get(omi.worker.creds.TOKEN_ENV)
    calls = []
    st = {}

    class R:
        def __init__(s, out="", rc=0, err=""): s.stdout, s.returncode, s.stderr = out, rc, err

    def ran_docker(calls):
        return [c for c in calls if c[0][:2] in (["docker", "run"], ["docker", "build"])]

    def run(cmd, **kw):
        if "--git-common-dir" in cmd:
            return R(str(Path(cmd[2]) / "shared.git"))
        if "--show-toplevel" in cmd:
            return R(str(cmd[2]))
        if "remote" in cmd:
            return R(rc=1)
        calls.append((cmd, kw))
        if cmd[:3] == ["docker", "image", "inspect"] and st.get("build_fail"):
            return R(rc=1)
        if cmd[:2] == ["docker", "build"]:
            return R("BUILDLOG", 1 if st.get("build_fail") else 0, "BUILDERR")
        if cmd[:2] == ["docker", "info"]:
            return R(rc=st["info_rc"])
        if "show" in cmd:
            return R("---\nscope: src/**\n---\n")
        if "status" in cmd:
            return R(" M src/a.py\0?? .gitattributes\0?? .github/x.yml\0 M .omi/tasks/TASK-001.md\0")
        return R()

    with tempfile.TemporaryDirectory() as d:
        wt = Path(d).resolve()
        (wt / ".git").write_text("gitdir: /x")
        task = wt / ".omi" / "tasks" / "TASK-001.md"
        subprocess.run, shutil.which = run, lambda _: "docker"
        omi.common.core.main_checkout, omi.common.core.WINDOWS = (lambda _: wt), False  # no docker/ or agents here: template copies
        os.environ[omi.worker.creds.TOKEN_ENV] = "tok-SECRET"
        out = io.StringIO()
        sys.stdout, saved = out, sys.stdout
        try:
            def go(task=task, **kw):
                calls.clear()
                st.update(info_rc=0, build_fail=0)
                st.update(kw)
                try:
                    return omi.worker.run.worker(wt, task, effort=kw.get("effort"))
                except SystemExit as e:
                    return str(e)

            assert go() == 3, "out-of-scope change"
            assert "OUT OF SCOPE: .gitattributes" in out.getvalue() and "src/a.py" not in out.getvalue()
            assert "OUT OF SCOPE: .github/x.yml" in out.getvalue()
            assert omi.project.scope.GIT_HINT in out.getvalue()
            argv, kw = next(c for c in calls if c[0][:2] == ["docker", "run"])
            assert not any("tok-SECRET" in a for a in argv), "token in argv"
            assert argv[argv.index("-e") + 1] == omi.worker.creds.TOKEN_ENV and kw["env"][omi.worker.creds.TOKEN_ENV] == "tok-SECRET"
            assert kw["stdin"] is subprocess.DEVNULL
            for f in ("--read-only", "no-new-privileges", "node", f"{wt}:/work", f"{wt / '.git'}:/work/.git:ro"):
                assert f in argv, f
            assert argv[argv.index("--cap-drop") + 1] == "ALL" and not any("docker.sock" in a for a in argv)
            c = argv[argv.index("claude"):]
            assert c[c.index("--model") + 1] == "claude-sonnet-5-5" and c[c.index("--effort") + 1] == "medium"
            assert c[c.index("--permission-mode") + 1] == "bypassPermissions"
            assert "/work/.omi/tasks/TASK-001.md" in c[2] and "Checkpoint" in c[c.index("--append-system-prompt") + 1]
            name = argv[argv.index("--name") + 1]
            assert re.fullmatch(r"[a-z0-9_.-]+-TASK-001-engineer-claude-sonnet-5\.5-medium-\d{6}", name), name
            lab = [argv[i + 1] for i, a in enumerate(argv) if a == "--label"]
            proj = omi.worker.docker.compose_labels(name, "agent")["com.docker.compose.project"]
            assert f"com.docker.compose.project={proj}" in lab and "com.docker.compose.service=agent" in lab
            for k, v in (("omi-role", "omi-agent-engineer"), ("omi-task", "TASK-001"), ("omi-model", "claude-sonnet-5-5"), ("omi-effort", "medium")):
                assert f"{k}={v}" in lab, lab
            assert any(l.startswith("omi-started=") for l in lab) and "omi-worker=1" in lab
            go(effort="high")
            argv = next(c[0] for c in calls if c[0][:2] == ["docker", "run"])
            assert argv[argv.index("--effort") + 1] == "high"
            # alias map from .omi/config.json; unknown alias fails before docker
            (wt / ".omi").mkdir(exist_ok=True)
            (wt / ".omi" / "config.json").write_text('{"models": {"fast": "claude-haiku-5-5"}}')
            calls.clear(); st.update(info_rc=0, build_fail=0)
            try:
                omi.worker.run.worker(wt, task, model="turbo", effort="low")
            except SystemExit as e:
                assert "turbo" in str(e) and not ran_docker(calls), e
            else:
                raise AssertionError("unknown alias accepted")
            go_model = lambda m: (calls.clear(), omi.worker.run.worker(wt, task, model=m, effort="low"))
            go_model("fast")
            argv = next(c[0] for c in calls if c[0][:2] == ["docker", "run"])
            assert argv[argv.index("--model") + 1] == "claude-haiku-5-5" and "-claude-haiku-5.5-low-" in argv[argv.index("--name") + 1]
            (wt / ".omi" / "config.json").unlink()
            # build log: silent on success, shown (stderr) on failure
            out.truncate(0); out.seek(0)
            go(build_fail=0)
            assert "BUILDLOG" not in out.getvalue()
            err = io.StringIO()
            sys.stderr, saved_err = err, sys.stderr
            try:
                e = go(build_fail=1)
            finally:
                sys.stderr = saved_err
            assert e == "docker build failed." and "BUILDLOG" in err.getvalue() and "BUILDERR" in err.getvalue(), e
            # .git* components flagged unless named exactly; symlinks flagged
            status = R(" M src/.gitattributes\0 M src/ok.py\0")
            run0 = subprocess.run
            subprocess.run = lambda cmd, **kw: status if "status" in cmd else run0(cmd, **kw)
            assert omi.project.scope.out_of_scope(wt, "TASK-001") == ["src/.gitattributes"]
            status = R(" M GIT~1/x\0 M src/GITATT~1\0 M a/gitmod~2\0 M GITIGN~1.TXT\0 M x/GITHUB~3\0 M src/GITHUB.py\0 M src/ok.py\0")
            subprocess.run = lambda cmd, **kw: status if "status" in cmd else run0(cmd, **kw)
            assert omi.project.scope.out_of_scope(wt, "TASK-001") == ["GIT~1/x", "src/GITATT~1", "a/gitmod~2", "GITIGN~1.TXT", "x/GITHUB~3"]
            status = R(" M src/.gitattributes\0 M src/ok.py\0")
            subprocess.run = lambda cmd, **kw: (R("---\nscope: src/.gitattributes, src/ok.py\n---\n") if "show" in cmd
                                                    else status if "status" in cmd else run0(cmd, **kw))
            assert omi.project.scope.out_of_scope(wt, "TASK-001") == []
            real_islink = os.path.islink
            os.path.islink = lambda p: str(p).endswith("ok.py")
            assert omi.project.scope.out_of_scope(wt, "TASK-001") == ["src/ok.py"]
            os.path.islink = real_islink
            subprocess.run = run0

            def ran():
                return [c[0][:2] for c in calls if c[0][:2] in (["docker", "run"], ["docker", "build"])]
            e = go(info_rc=1)
            assert "Docker is not running" in e and not ran(), (e, calls)
            shutil.which = lambda _: None
            assert "Docker is not running" in go() and not calls
            shutil.which = lambda _: "docker"
            assert "not inside" in go(task=wt.parent / "x.md") and not calls
            del os.environ[omi.worker.creds.TOKEN_ENV]
            e = go()
            assert "no token" in e and not ran(), e
        finally:
            sys.stdout = saved
            subprocess.run, shutil.which, omi.common.core.main_checkout, omi.common.core.WINDOWS, tok = real
            os.environ.pop(omi.worker.creds.TOKEN_ENV, None)
            if tok is not None:
                os.environ[omi.worker.creds.TOKEN_ENV] = tok


def test_prove_exit_and_hosts():
    ok = "PASS claude CLI reaches\nPASS codex CLI reaches\nPASS write\n"
    assert omi.worker.docker.prove_rc(ok, 0) == 0 and omi.worker.docker.prove_rc(ok, 5) == 5
    assert omi.worker.docker.prove_rc(ok + "FAIL codex CLI: network error: x\n", 0) == 1
    assert omi.worker.docker.prove_rc("PASS claude CLI x\n", 0) == 1 and omi.worker.docker.prove_rc("", 0) == 1
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / ".omi").mkdir()
        (Path(d) / ".omi" / "config.json").write_text('{"network_allow": ["api.anthropic.com"]}')
        assert omi.worker.docker.allow_for(d, "codex") == ["api.anthropic.com", "api.openai.com"]
        assert omi.worker.docker.allow_for(d, "claude") == ["api.anthropic.com"]
        assert omi.worker.docker.allow_for(d, *omi.worker.docker.TOOL_API_HOST) == ["api.anthropic.com", "api.openai.com"]
    sh = (omi.common.core.TEMPLATE / "docker" / "prove.sh").read_text()
    assert "error sending request" in sh
    # codex prints "stream error: ... last status: 401" on a bad key: that is an auth result, not a network one
    net = next(l for l in sh.splitlines() if "ENOTFOUND" in l)
    assert "stream error" not in net


def test_clip_report():
    short = "DONE\nx\ncommit"
    assert omi.project.tasks.clip_report(short) == ["DONE", "x", "commit"]
    big = ["DONE"] + ["line %d" % i for i in range(1000)] + ["feat: commit msg"]
    out = omi.project.tasks.clip_report("\n".join(big))
    assert out[0] == "DONE" and out[-1] == "feat: commit msg" and "[... truncated ...]" in out
    assert sum(map(len, out)) < 2200 and out[1] == "line 0"


def test_container_names():
    import datetime
    t = datetime.datetime(2026, 1, 1, 14, 32, 5)
    assert omi.worker.docker.container_name("omi", "omi-agent-reviewer", "TASK-055", "claude", "claude-sonnet-5-5", "medium", t) == \
        "omi-TASK-055-reviewer-claude-sonnet-5.5-medium-143205"
    assert omi.worker.docker.container_name("omi", "omi-agent-engineer", "TASK-018", "codex", "gpt-5.1-codex", "high", t) == \
        "omi-TASK-018-engineer-codex-gpt-5.1-codex-high-143205"
    assert omi.worker.docker.container_name("omi", "omi-agent-engineer", "TASK-018", "codex", "gpt-6.1-sol", "high", t) == \
        "omi-TASK-018-engineer-codex-gpt-6.1-sol-high-143205"
    assert omi.worker.docker.container_name("omi", "my role", "prove", now=t) == "omi-prove-my-role-claude-none-none-143205"
    assert omi.worker.docker.container_name("omi", "omi-agent-engineer", "TASK-018", "codex", "gpt-6.1-sol", "high", t, salt="a3") == \
        "omi-TASK-018-engineer-codex-gpt-6.1-sol-high-143205a3"
    # compose project: lowercased run name, chars outside [a-z0-9_-] become '-'
    assert omi.worker.docker.compose_labels("omi-TASK-055-reviewer-claude-sonnet-5.5-medium-143205", "agent") == {
        "com.docker.compose.project": "omi-task-055-reviewer-claude-sonnet-5-5-medium-143205",
        "com.docker.compose.service": "agent"}
    with tempfile.TemporaryDirectory() as d:
        assert omi.worker.tools.resolve_model(d, "opus") == "claude-opus-5-5" and omi.worker.tools.resolve_model(d, "claude-x-1") == "claude-x-1"
        for bad in ("gpt", None):
            try:
                omi.worker.tools.resolve_model(d, bad)
            except SystemExit as e:
                assert bad is None or bad in str(e)
            else:
                raise AssertionError(bad)
    labels = omi.worker.docker.worker_labels("omi-agent-engineer", "TASK-1", "m", "low")
    a = omi.worker.docker.worker_argv(Path("/w"), "img", ["x"], "n", "r", labels)
    assert "omi-model=m" in a and "omi-effort=low" in a and "omi-task=TASK-1" in a and "omi-role=omi-agent-engineer" in a
    # agent container joins the run's compose group (same project as its proxy)
    a = omi.worker.docker.worker_argv(Path("/w"), "img", ["x"], "n", "r", {**labels, **omi.worker.docker.compose_labels("n", "agent")})
    assert "com.docker.compose.project=n" in a and "com.docker.compose.service=agent" in a
    # status lists running workers (docker mocked); nothing when none
    import datetime as dt
    started = (dt.datetime.now() - dt.timedelta(minutes=75)).isoformat(timespec="seconds")
    real_run = subprocess.run
    rows = {"out": f"TASK-9\tomi-agent-engineer\tclaude-opus-5-5\thigh\t{started}\n"}
    subprocess.run = lambda cmd, **kw: type("R", (), {"stdout": rows["out"], "returncode": 0})()
    buf = io.StringIO()
    sys.stdout, saved = buf, sys.stdout
    try:
        omi.worker.docker.print_workers(Path("/nonexistent"))
        shown = buf.getvalue()
        rows["out"] = ""
        buf.truncate(0); buf.seek(0)
        omi.worker.docker.print_workers(Path("/nonexistent"))
        none = buf.getvalue()
    finally:
        sys.stdout = saved
        subprocess.run = real_run
    assert "TASK-9 omi-agent-engineer claude-opus-5-5 high 1h15m" in shown and none == "", (shown, none)
    argv = omi.worker.docker.worker_argv(Path("/w"), "img", ["x"], "n1")
    assert argv[argv.index("--name") + 1] == "n1"
    assert "--name" not in omi.worker.docker.worker_argv(Path("/w"), "img", ["x"])
    a = omi.worker.docker.worker_argv(Path("/w"), "img", ["x"], "n1", "my-repo")
    assert a[a.index("omi-repo=my-repo") - 1] == "--label"


def test_worker_cache_tmpfs_and_full_volumes():
    a = omi.worker.docker.worker_argv(Path("/w"), "img", ["x"])
    assert "/cache:rw,exec,nosuid,uid=1000,gid=1000,size=2048m" in a and "/tmp:rw,noexec,nosuid,size=512m" in a
    assert "/home/node:rw,noexec,nosuid,uid=1000,gid=1000,size=512m" in a
    assert_download_cache_env(a)
    assert "size=64m" in " ".join(omi.worker.docker.worker_argv(Path("/w"), "img", ["x"], cache_mb=64))
    with tempfile.TemporaryDirectory() as d:
        assert omi.worker.docker.worker_sizes(d) == {"cache_mb": 2048, "tmp_mb": 512}
        (Path(d) / ".omi").mkdir()
        (Path(d) / ".omi" / "config.json").write_text('{"worker": {"cache_mb": 4096}}', encoding="utf-8")
        assert omi.worker.docker.worker_sizes(d) == {"cache_mb": 4096, "tmp_mb": 512}
        for worker in (None, [], "invalid", 1, True, {"cache_mb": 0}, {"tmp_mb": False}):
            (Path(d) / ".omi" / "config.json").write_text(json.dumps({"worker": worker}), encoding="utf-8")
            try:
                omi.worker.docker.worker_sizes(d)
                raise AssertionError(f"invalid worker accepted: {worker!r}")
            except SystemExit as e:
                assert str(e) == '"worker.cache_mb" and "worker.tmp_mb" in .omi/config.json must be positive integers. Nothing changed.'
        real = subprocess.run

        home_used = 10

        def fake(argv, **kw):
            assert kw["timeout"] == 10
            out = {"ps": "c1\n", "exec": "Filesystem 1024-blocks Used Available Capacity Mounted on\n"
                   f"tmpfs 100 95 5 95% /cache\ntmpfs 100 {home_used} {100 - home_used} {home_used}% /home/node\n"}[argv[1]]
            return subprocess.CompletedProcess(argv, 0, out, "")
        subprocess.run = fake
        try:
            for home_used in (10, 90, 92):
                lines = omi.worker.docker.full_volumes(Path(d))
                mounts = "/cache 95%, /home/node 92%" if home_used == 92 else "/cache 95%"
                assert lines == [f"c1: {mounts} full; raise worker.cache_mb / worker.tmp_mb in .omi/config.json"], lines
            for stage in ("ps", "exec"):
                for error in (OSError, subprocess.TimeoutExpired):
                    def unavailable(argv, **kw):
                        assert kw["timeout"] == 10
                        if argv[1] == stage:
                            if error is OSError:
                                raise OSError("docker unavailable")
                            raise subprocess.TimeoutExpired(argv, 10)
                        return fake(argv, **kw)
                    subprocess.run = unavailable
                    assert omi.worker.docker.full_volumes(Path(d)) == []
        finally:
            subprocess.run = real


def test_network_allowlist():
    import importlib.util
    spec = importlib.util.spec_from_file_location("omi_proxy", omi.common.core.TEMPLATE / "docker" / "proxy.py")
    px = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(px)
    al = ["api.anthropic.com", "*.example.org", "host.io:8443"]
    for host, port, want in (("api.anthropic.com", 443, True), ("API.Anthropic.com.", 443, True), ("example.com", 443, False),
                             ("evil-api.anthropic.com", 443, False), ("api.anthropic.com", 80, False),
                             ("a.example.org", 443, True), ("example.org", 443, False), ("x.notexample.org", 443, False),
                             ("host.io", 8443, True), ("host.io", 443, False), ("1.1.1.1", 443, False)):
        assert px.allowed(host, port, al) is want, (host, port)
    # protocol: CONNECT only, 403 names host and key, BLOCKED logged, no headers logged
    import socket, threading
    echo = socket.socket(); echo.bind(("127.0.0.1", 0)); echo.listen(1)
    px.ALLOW[:] = [f"127.0.0.1:{echo.getsockname()[1]}"]
    threading.Thread(target=lambda: (lambda c: c.sendall(c.recv(10)))(echo.accept()[0]), daemon=True).start()
    srv = px.Server(("127.0.0.1", 0), px.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    def ask(req, extra=b""):
        c = socket.create_connection(srv.server_address, 5)
        c.sendall(req)
        data = c.recv(4096)
        if extra:
            c.sendall(extra)
            data += c.recv(100)
        c.close()
        return data.decode()

    buf = io.StringIO()
    sys.stdout, saved = buf, sys.stdout
    try:
        assert ask(b"GET http://example.com/ HTTP/1.1\r\nAuthorization: SECRET\r\n\r\n").startswith("HTTP/1.1 405")
        blocked = ask(b"CONNECT example.com:443 HTTP/1.1\r\nAuthorization: SECRET\r\n\r\n")
        quiet = [ask(f"CONNECT {h}:443 HTTP/1.1\r\n\r\n".encode()) for h in ("ab.chatgpt.com", "x.oaiusercontent.com", "statsig.anthropic.com", "sentry.io")]
        badhost = ask(b"CONNECT ex_ample$.com:443 HTTP/1.1\r\n\r\n")
        ok = ask(f"CONNECT {px.ALLOW[0]} HTTP/1.1\r\n\r\n".encode(), b"hello")
    finally:
        sys.stdout = saved
        srv.shutdown()
    assert blocked.startswith("HTTP/1.1 403") and 'omi blocked example.com: add it to "network_allow" in .omi/config.json' in blocked
    assert ok.startswith("HTTP/1.1 200") and ok.endswith("hello"), ok
    assert all(q.startswith("HTTP/1.1 403") for q in quiet) and "BLOCKED sentry.io" not in buf.getvalue() and "BLOCKED ab.chatgpt" not in buf.getvalue()
    assert badhost.startswith("HTTP/1.1 400") and "ex_ample" not in buf.getvalue()
    assert "BLOCKED example.com:443" in buf.getvalue() and "SECRET" not in buf.getvalue()
    # config
    with tempfile.TemporaryDirectory() as d:
        assert omi.worker.docker.network_allow(d) == ["api.anthropic.com"]
        (Path(d) / ".omi").mkdir()
        (Path(d) / ".omi" / "config.json").write_text('{"network_allow": ["api.anthropic.com", "*.x.io:8443"]}')
        assert omi.worker.docker.network_allow(d) == ["api.anthropic.com", "*.x.io:8443"]
        (Path(d) / ".omi" / "config.json").write_text('{"network_allow": ["bad host"]}')
        try:
            omi.worker.docker.network_allow(d)
        except SystemExit as e:
            assert "bad host" in str(e)
        else:
            raise AssertionError("bad entry accepted")
        for bad in ('{"network_allow": "api.anthropic.com"}', '{"network_allow": [1]}', "{not json"):
            (Path(d) / ".omi" / "config.json").write_text(bad)
            try:
                omi.worker.docker.network_allow(d)
            except SystemExit as e:
                assert "Nothing changed." in str(e)
            else:
                raise AssertionError(bad)
    # argv: restricted network and proxy env; without a network nothing is added
    a = omi.worker.docker.worker_argv(Path("/w"), "img", ["x"], "n", network="omi-net-n", proxy="n-proxy")
    assert a[a.index("--network") + 1] == "omi-net-n" and "HTTPS_PROXY=http://n-proxy:3128" in a
    assert "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1" in a and "--network" not in omi.worker.docker.worker_argv(Path("/w"), "img", ["x"])
    # egress: order, hardening, no token, cleanup and the blocked-host message
    calls = []

    class R:
        def __init__(s, out="", rc=0, err=""): s.stdout, s.returncode, s.stderr = out, rc, err

    def run(cmd, **kw):
        calls.append(cmd)
        return R("omi-proxy ready\nBLOCKED example.com:443\nBLOCKED example.com:443\n" if cmd[:2] == ["docker", "logs"] else "")

    real = subprocess.run
    subprocess.run = run
    buf = io.StringIO()
    sys.stdout, saved = buf, sys.stdout
    try:
        # worst real name: a long codex model ID at xhigh effort
        long = omi.worker.docker.container_name("my-repo", "omi-agent-engineer", "TASK-052", "codex", "gpt-5.1-codex-mini-high-preview-2026-10-26", "xhigh")
        with real_egress(Path("/My Repo"), long, "img", ["api.anthropic.com"]) as (net, proxy):
            assert (net, proxy) == (f"omi-net-{long}", "omi-proxy") and len(f"{long}-proxy") > 63
            host = omi.worker.docker.worker_argv(Path("/w"), "img", ["x"], long, network=net, proxy=proxy)
            assert "HTTPS_PROXY=http://omi-proxy:3128" in host
            inside = list(calls)
    finally:
        sys.stdout = saved
        subprocess.run = real
    assert [c[1:3] for c in inside][:1] == [["network", "create"]] and inside[0][3] == "--internal"
    create = next(c for c in inside if c[1] == "create")
    assert create[-3:] == ["python3", "/proxy.py", "api.anthropic.com"] and "--read-only" in create and "--cap-drop" in create
    assert not any("TOKEN" in a or ":/work" in a for a in create) and "omi-repo=my-repo" in create
    assert f"com.docker.compose.project={omi.worker.docker.compose_labels(long, 'proxy')['com.docker.compose.project']}" in create
    assert "com.docker.compose.service=proxy" in create
    assert [c[1] for c in inside if c[1] in ("create", "start")] == ["create", "start"]
    assert next(c for c in inside if c[1:3] == ["network", "connect"])[3:5] == ["--alias", "omi-proxy"]
    assert any(c[1:3] == ["network", "connect"] for c in inside)
    assert calls[-2][1:3] == ["rm", "-f"] and calls[-1][1:3] == ["network", "rm"]
    assert buf.getvalue().count("NETWORK BLOCKED: example.com:443 - add to \"network_allow\" in .omi/config.json") == 1
    # failure reports the stderr of the failing command; blocked lines are capped
    def run2(cmd, **kw):
        r = R("omi-proxy ready\n" + "".join(f"BLOCKED h{i}.com:443\n" for i in range(8)) if cmd[1] == "logs" else "")
        if cmd[1:3] == ["network", "connect"]:
            r.returncode, r.stderr = 1, "connect boom"
        return r

    subprocess.run = run2
    buf = io.StringIO()
    sys.stdout, saved = buf, sys.stdout
    try:
        try:
            with real_egress(Path("/My Repo"), "n", "img", ["a.com"]):
                pass
        except SystemExit as e:
            assert "connect boom" in str(e)
        else:
            raise AssertionError("failure hidden")
    finally:
        sys.stdout = saved
        subprocess.run = real
    assert buf.getvalue().count("NETWORK BLOCKED") == 5 and "and 3 more" in buf.getvalue()
    # prove.sh checks both an allowed and a blocked host
    sh = (omi.common.core.TEMPLATE / "docker" / "prove.sh").read_text()
    assert "api.anthropic.com" in sh and "example.com" in sh and "1.1.1.1" in sh and "network_allow" in sh
    # a name already in use: NameTaken, and only what this run created is removed (never another run's proxy)
    conflicts = {"network": "network with name omi-net-n already exists", "proxy": 'The container name "/n-proxy" is already in use'}
    for taken in ("network", "proxy", "port"):
        seen = []

        def run3(cmd, **kw):
            seen.append(cmd)
            if (cmd[1:3] == ["network", "create"]) if taken == "network" else (cmd[1] == "create"):
                return R(rc=1, err=conflicts.get(taken, "Bind for 0.0.0.0:8080 failed: port is already in use"))
            return R("omi-proxy ready\n" if cmd[1] == "logs" else "")

        subprocess.run = run3
        try:
            try:
                with real_egress(Path("/My Repo"), "n", "img", ["a.com"]):
                    pass
            except omi.worker.docker.NameTaken:
                assert taken != "port", "a port conflict must not count as a taken name"
            except SystemExit as e:
                assert taken == "port" and "cannot" in str(e), e
            else:
                raise AssertionError("taken name accepted")
        finally:
            subprocess.run = real
        cmds = [c[1:3] for c in seen]
        if taken != "port":
            assert ["rm", "-f"] not in cmds and (["network", "rm"] in cmds) == (taken == "proxy"), (taken, cmds)
    # only Docker's own message for this exact name counts
    assert omi.worker.docker.name_taken('Conflict. The container name "/x" is already in use', "x")
    assert omi.worker.docker.name_taken("network with name omi-net-x already exists", "omi-net-x")
    assert not omi.worker.docker.name_taken('Conflict. The container name "/x" is already in use', "y")
    assert not omi.worker.docker.name_taken("Bind failed: port already in use", "x")


def test_clean_and_old_images():
    real, realmc = subprocess.run, omi.common.core.main_checkout
    calls = []

    class R:
        def __init__(s, out="", rc=0): s.stdout, s.returncode, s.stderr = out, rc, ""

    with tempfile.TemporaryDirectory() as d:
        main = Path(d) / "My Repo"
        main.mkdir()
        cur = omi.worker.docker.image_tag(main)[1]
        repo = omi.worker.docker.image_repo(main)
        assert repo == "omi-worker-my-repo"

        def run(cmd, **kw):
            calls.append(cmd)
            if cmd[:2] == ["docker", "ps"]:
                return R("c1\nc2\n" if "label=omi-repo=my-repo" in cmd else "other\n")
            if cmd[:2] == ["docker", "images"]:
                return R(f"{cur}\n{repo}:old1\n{repo}:old2\n" + ("" if "label=omi-repo=my-repo" in cmd else "omi-worker-other:x\n"))
            if cmd[:3] == ["docker", "image", "inspect"]:
                return R(rc=1)
            if cmd[:3] == ["docker", "network", "ls"]:
                return R("n1\n" if "label=omi-repo=my-repo" in cmd else "other\n")
            return R()

        subprocess.run, omi.common.core.main_checkout = run, lambda _: main
        try:
            omi.worker.docker.clean()
            assert ["docker", "rm", "-f", "c1", "c2"] in calls and not any("other" in c for c in calls if c[:2] == ["docker", "rm"])
            assert ["docker", "network", "rm", "n1"] in calls
            assert ["docker", "rmi", f"{repo}:old1"] in calls and ["docker", "rmi", f"{repo}:old2"] in calls
            assert ["docker", "rmi", cur] not in calls and ["docker", "rmi", "omi-worker-other:x"] not in calls
            ps = next(c for c in calls if c[:2] == ["docker", "ps"])
            assert "label=omi-worker=1" in ps and "label=omi-repo=my-repo" in ps and not any(a.startswith("name=") for a in ps)
            calls.clear()
            omi.worker.docker.clean(all_images=True)
            assert ["docker", "rmi", cur] in calls and ["docker", "rmi", "omi-worker-other:x"] not in calls
            calls.clear()
            assert omi.worker.docker.ensure_image(main) == cur
            assert ["docker", "rmi", f"{repo}:old1"] in calls and ["docker", "rmi", cur] not in calls
        finally:
            subprocess.run, omi.common.core.main_checkout = real, realmc


def test_pr_comment():
    pr = omi.worker.pr
    h = pr.header("build", "omi-agent-engineer (claude/sonnet/medium)", "DONE", "2026-10-30 13:40")
    assert h == ("**Step:** build · **Agent:** omi-agent-engineer (claude/sonnet/medium) · "
                 "**Time:** 2026-10-30 13:40 · **Verdict:** DONE")
    calls, state = [], {"remote": "origin", "pr": "OPEN", "gh": "gh"}

    def run(cmd, **kw):
        calls.append((cmd, kw.get("input")))
        out = state["pr"] if "view" in cmd else ""
        return type("R", (), {"stdout": out, "stderr": "boom", "returncode": 1 if state.get("fail") and "comment" in cmd else 0})()

    real = subprocess.run, shutil.which, omi.common.core.git
    subprocess.run, shutil.which, omi.common.core.git = run, lambda _: state["gh"], lambda wt, *a: state["remote"]
    try:
        assert pr.post_report("/wt", "TASK-1", "build", "r", "claude", "sonnet", "low", "DONE", "line1\nline2")
        cmd, text = calls[-1]
        assert cmd[:4] == ["gh", "pr", "comment", "task/TASK-1"] and text.startswith("**Step:** build · **Agent:** r (claude/sonnet/low) · **Time:** ")
        assert text.endswith("**Verdict:** DONE\n\nline1\nline2")
        assert pr.post_hook("/wt", "TASK-1", "post-run", (0, "a\nlast")) and calls[-1][1].endswith("\n\nlast")
        assert "**Step:** hook post-run · **Agent:** Coordinator" in calls[-1][1] and "**Verdict:** pass" in calls[-1][1]
        for key, val in (("remote", ""), ("pr", "")):  # no remote / no open PR: skipped, no comment
            saved, state[key] = state[key], val
            n = len(calls)
            assert not pr.post("/wt", "TASK-1", "x") and not any("comment" in c for c, _ in calls[n:])
            state[key] = saved
        state["fail"] = True
        out, sys.stdout = sys.stdout, io.StringIO()
        try:
            assert not pr.post("/wt", "TASK-1", "x")
            assert "WARNING" in sys.stdout.getvalue()
        finally:
            sys.stdout = out
    finally:
        subprocess.run, shutil.which, omi.common.core.git = real


def main():
    test_pr_comment()
    test_worker_cache_tmpfs_and_full_volumes()
    test_download_cache_gitignore()
    test_download_cache_scope()
    test_download_cache_shared_exclude()
    test_worker()
    test_container_names()
    test_clip_report()
    test_network_allowlist()
    test_prove_exit_and_hosts()
    test_clean_and_old_images()


if __name__ == "__main__":
    main()
