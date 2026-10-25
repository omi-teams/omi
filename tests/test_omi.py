import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
import omi  # noqa: E402


def git(cwd, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
                   cwd=cwd, check=True, capture_output=True)


def test_init_guard_status():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve()
        omi.init(root)
        assert (root / ".claude" / "settings.json").exists()
        (root / "AGENTS.md").write_text("custom")
        omi.init(root)
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
            return omi.guard(io.BytesIO(json.dumps(payload).encode()))

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
        assert guard(wt / "src" / "ok.py", "engineer") == 0
        assert guard(wt / ".claude" / "settings.json", "engineer") == 2
        assert guard(root / "src" / "x.py", "engineer") == 2, "engineer writing to main checkout"
        with tempfile.TemporaryDirectory() as other:
            assert guard(Path(other) / "x.py", "engineer") == 2, "engineer writing to a non-git dir"
            assert guard(Path(other) / "x.py") == 0, "no agent identity: as before"
            assert guard(Path(other) / ".claude" / "settings.json") == 2, "user-level config"
        git(root, "branch", "task/TASK-099")
        git(root, "worktree", "add", "-q", str(root / "wt99"), "task/TASK-099")
        assert guard(root / "wt99" / "src" / "x.py") == 2, "task not on development: deny"
        git(root, "worktree", "remove", "--force", str(root / "wt99"))
        (wt / ".omi" / "tasks" / "TASK-001.md").write_text(
            "---\ntitle: A\nstatus: in-progress\nscope: src/**\n---\n## Checkpoint\nNext: wire it\n")

        out = io.StringIO()
        sys.stdout, real = out, sys.stdout
        try:
            omi.status(root)
        finally:
            sys.stdout = real
        text = out.getvalue()
        assert "Next: wire it" in text and "next: TASK-003" in text, text

        def show():
            out = io.StringIO()
            sys.stdout, real = out, sys.stdout
            try:
                omi.status(root)
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


def test_github_rulesets():
    rs = omi.rulesets()
    dev, po = rs["omi-development"], rs["omi-po-only"]
    assert [r["type"] for r in dev["rules"]] == ["deletion", "non_fast_forward"]
    assert dev["bypass_actors"] == []
    assert po["conditions"]["ref_name"]["include"] == ["refs/heads/staging", "refs/heads/main"]
    types = {r["type"]: r for r in po["rules"]}
    assert {"pull_request", "update"} <= set(types) and "required_status_checks" not in types
    po = omi.rulesets(["test (ubuntu-latest)", "test (macos-latest)"])["omi-po-only"]
    types = {r["type"]: r for r in po["rules"]}
    assert types["required_status_checks"]["parameters"]["required_status_checks"] == [
        {"context": "test (ubuntu-latest)"}, {"context": "test (macos-latest)"}]
    assert po["bypass_actors"][0]["actor_id"] == 5

    tags = rs["omi-tags"]
    assert tags["target"] == "tag" and tags["bypass_actors"] == po["bypass_actors"]
    assert tags["conditions"]["ref_name"]["include"] == ["refs/tags/rc-*", "refs/tags/v*"]
    assert sorted(r["type"] for r in tags["rules"]) == ["deletion", "update"]  # no "creation": squad can tag


def test_ci_checks_and_apply():
    real_run, real_gh, real_info = omi.subprocess.run, omi.gh, omi.repo_info
    st = {"runs": [{"name": "test (ubuntu-latest)"}, {"name": "test (windows-latest)"}, {"name": "test (ubuntu-latest)"}],
          "live": None, "puts": []}

    def fake(*a, body=None):
        u = a[-1]
        if body is not None and a[1] == "PUT":
            st["live"] = body
            st["puts"].append(body)
            return None
        if "check-runs" in u:
            return {"check_runs": st["runs"]}
        if u.endswith("/rulesets"):
            return [{"name": "omi-po-only", "id": 1}] if st["live"] else []
        if u.endswith("/rulesets/1"):
            return st["live"]
        if "git/ref" in u:
            return {"object": {"sha": "x"}}
        if body is not None:
            return None
        return {"permissions": {"admin": True}}

    omi.gh, omi.repo_info = fake, lambda: "o/r"
    try:
        assert omi.ci_checks("o/r") == ["test (ubuntu-latest)", "test (windows-latest)"]
        st["runs"] = []
        assert omi.ci_checks("o/r") == []
        omi.gh = lambda *a, **k: (_ for _ in ()).throw(SystemExit("404"))
        assert omi.ci_checks("o/r") == []
        omi.gh = fake
        import contextlib, io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            omi.apply_github()
        assert "no CI check runs" in out.getvalue()
        st["live"] = omi.rulesets()["omi-po-only"]  # no required checks stored
        st["runs"] = [{"name": "test (ubuntu-latest)"}]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            omi.apply_github()
        assert "update ruleset omi-po-only" in out.getvalue() and len(st["puts"]) == 1
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            omi.apply_github()
        assert "unchanged ruleset omi-po-only" in out.getvalue()
        st["runs"] = [{"name": "test (ubuntu-latest)"}, {"name": "test (macos-latest)"}]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            omi.apply_github()
        assert "update ruleset omi-po-only" in out.getvalue()
    finally:
        omi.subprocess.run, omi.gh, omi.repo_info = real_run, real_gh, real_info


def test_same_and_no_gh():
    po = omi.rulesets()["omi-po-only"]
    live = json.loads(json.dumps(po))
    live["id"] = 7
    live["rules"].reverse()
    live["rules"][0].setdefault("parameters", {})
    assert omi.same(live, po)
    live["rules"].pop()
    assert not omi.same(live, po)
    real = omi.shutil.which
    omi.shutil.which = lambda _: None
    try:
        omi.github()
        assert False
    except SystemExit as e:
        assert "gh is not installed" in str(e)
    finally:
        omi.shutil.which = real


def test_github_po():
    realrun, realwhich, realapply = omi.subprocess.run, omi.shutil.which, omi.apply_github
    st = {}

    class R:
        def __init__(s, out="", rc=0): s.stdout, s.returncode = out, rc

    def run(cmd, **kw):
        sub = cmd[1:3]
        if sub == ["auth", "status"]:
            if st["status_fail"]:
                return R("", 1)
            hs = [{"login": u, "active": u == st["active"]} for u in st["accts"]]
            return R(json.dumps({"hosts": {"github.com": hs}}))
        if sub == ["auth", "login"]:
            st["calls"].append("login")
            if st["new"]:
                st["accts"].append(st["new"]); st["active"] = st["new"]
            st["status_fail"] = st["status_fail_after"]
            return R("", st["login_rc"])
        if sub == ["auth", "logout"]:
            st["calls"].append("logout")
            if not st["logout_fail"]:
                st["accts"].remove(cmd[-1])
                if st["active"] == cmd[-1]: st["active"] = ""
            return R("", 1 if st["logout_fail"] else 0)
        if sub == ["auth", "switch"]:
            st["calls"].append("switch")
            if not st["switch_fail"]:
                st["active"] = cmd[-1]
        if sub == ["repo", "view"]:
            st["calls"].append("view")
            return R("o/r PRIVATE" if st["private"] else "o/r PUBLIC")
        return R()

    def go(fail_apply=False, **kw):
        st.update(accts=["squad"], active="squad", new="po", calls=[], status_fail=False,
                  status_fail_after=False, login_rc=0, logout_fail=False, private=False, switch_fail=False)
        st.update(kw)
        def apply():
            st["calls"].append("apply")
            if fail_apply: raise SystemExit("boom")
        omi.apply_github = apply
        try:
            omi.github(po=True)
            return None
        except SystemExit as e:
            return str(e)

    omi.subprocess.run, omi.shutil.which = run, lambda _: "gh"
    try:
        assert go() is None and st["calls"] == ["view", "login", "apply", "logout", "switch"], st["calls"]
        # logout already restored prev: no extra switch
        orig = run
        def run2(cmd, **kw):
            if cmd[1:3] == ["auth", "logout"]:
                r = orig(cmd, **kw); st["active"] = "squad"; return r
            return orig(cmd, **kw)
        omi.subprocess.run = run2
        assert go() is None and "switch" not in st["calls"], st["calls"]
        omi.subprocess.run = run
        assert st["accts"] == ["squad"] and st["active"] == "squad"
        assert go(fail_apply=True) == "boom" and st["calls"] == ["view", "login", "apply", "logout", "switch"]
        assert st["accts"] == ["squad"]
        e = go(new="")  # same-account guard: no logout
        assert "own account" in e and "logout" not in st["calls"] and "apply" not in st["calls"]
        e = go(active="")  # empty prev: abort before login
        assert "no active squad" in e and st["calls"] == []
        e = go(login_rc=1)  # login fails after saving the token: still cleaned up
        assert "login failed" in e and st["calls"] == ["view", "login", "logout", "switch"] and st["accts"] == ["squad"]
        e = go(status_fail_after=True)  # cannot read accounts after login: loud failure
        assert "WARNING" in e and "apply" not in st["calls"]
        e = go(logout_fail=True)  # logout fails: warning + non-zero, switch still attempted
        assert "WARNING" in e and "po" in e and st["calls"] == ["view", "login", "apply", "logout", "switch"]
        assert st["active"] == "squad"
        e = go(private=True)  # private repo: checked with the squad account, no PO login
        assert "private" in e and st["calls"] == ["view"], st["calls"]
        e = go(switch_fail=True)  # active account not restored: warning + non-zero
        assert "WARNING" in e and "not the squad account squad" in e and st["accts"] == ["squad"]
    finally:
        omi.subprocess.run, omi.shutil.which, omi.apply_github = realrun, realwhich, realapply


def test_github_private():
    real = omi.subprocess.run
    class R: stdout, stderr, returncode = "o/r PRIVATE", "", 0
    omi.subprocess.run = lambda *a, **k: R()
    try:
        omi.apply_github()
        assert False
    except SystemExit as e:
        assert "private" in str(e)
    finally:
        omi.subprocess.run = real


def test_worker():
    real = omi.subprocess.run, omi.shutil.which, omi.main_checkout, omi.WINDOWS, omi.os.environ.get(omi.TOKEN_ENV)
    calls = []
    st = {}

    class R:
        def __init__(s, out="", rc=0, err=""): s.stdout, s.returncode, s.stderr = out, rc, err

    def run(cmd, **kw):
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
            return R(" M src/a.py\0?? .gitattributes\0 M .omi/tasks/TASK-001.md\0")
        return R()

    with tempfile.TemporaryDirectory() as d:
        wt = Path(d).resolve()
        (wt / ".git").write_text("gitdir: /x")
        task = wt / ".omi" / "tasks" / "TASK-001.md"
        omi.subprocess.run, omi.shutil.which = run, lambda _: "docker"
        omi.main_checkout, omi.WINDOWS = (lambda _: wt), False  # no docker/ or agents here: template copies
        omi.os.environ[omi.TOKEN_ENV] = "tok-SECRET"
        out = io.StringIO()
        sys.stdout, saved = out, sys.stdout
        try:
            def go(task=task, **kw):
                calls.clear()
                st.update(info_rc=0, build_fail=0)
                st.update(kw)
                try:
                    return omi.worker(wt, task, effort=kw.get("effort"))
                except SystemExit as e:
                    return str(e)

            assert go() == 3, "out-of-scope change"
            assert "OUT OF SCOPE: .gitattributes" in out.getvalue() and "src/a.py" not in out.getvalue()
            argv, kw = next(c for c in calls if c[0][:2] == ["docker", "run"])
            assert not any("tok-SECRET" in a for a in argv), "token in argv"
            assert argv[argv.index("-e") + 1] == omi.TOKEN_ENV and kw["env"][omi.TOKEN_ENV] == "tok-SECRET"
            assert kw["stdin"] is omi.subprocess.DEVNULL
            for f in ("--read-only", "no-new-privileges", "node", f"{wt}:/work", f"{wt / '.git'}:/work/.git:ro"):
                assert f in argv, f
            assert argv[argv.index("--cap-drop") + 1] == "ALL" and not any("docker.sock" in a for a in argv)
            c = argv[argv.index("claude"):]
            assert c[c.index("--model") + 1] == "sonnet" and c[c.index("--effort") + 1] == "medium"
            assert c[c.index("--permission-mode") + 1] == "bypassPermissions"
            assert "/work/.omi/tasks/TASK-001.md" in c[2] and "Checkpoint" in c[c.index("--append-system-prompt") + 1]
            go(effort="high")
            argv = next(c[0] for c in calls if c[0][:2] == ["docker", "run"])
            assert argv[argv.index("--effort") + 1] == "high"
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
            run0 = omi.subprocess.run
            omi.subprocess.run = lambda cmd, **kw: status if "status" in cmd else run0(cmd, **kw)
            assert omi.out_of_scope(wt, "TASK-001") == ["src/.gitattributes"]
            status = R(" M GIT~1/x\0 M src/GITATT~1\0 M a/gitmod~2\0 M GITIGN~1.TXT\0 M x/GITHUB~3\0 M src/GITHUB.py\0 M src/ok.py\0")
            omi.subprocess.run = lambda cmd, **kw: status if "status" in cmd else run0(cmd, **kw)
            assert omi.out_of_scope(wt, "TASK-001") == ["GIT~1/x", "src/GITATT~1", "a/gitmod~2", "GITIGN~1.TXT", "x/GITHUB~3"]
            status = R(" M src/.gitattributes\0 M src/ok.py\0")
            omi.subprocess.run = lambda cmd, **kw: (R("---\nscope: src/.gitattributes, src/ok.py\n---\n") if "show" in cmd
                                                    else status)
            assert omi.out_of_scope(wt, "TASK-001") == []
            real_islink = omi.os.path.islink
            omi.os.path.islink = lambda p: str(p).endswith("ok.py")
            assert omi.out_of_scope(wt, "TASK-001") == ["src/ok.py"]
            omi.os.path.islink = real_islink
            omi.subprocess.run = run0

            def ran():
                return [c[0][:2] for c in calls if c[0][:2] in (["docker", "run"], ["docker", "build"])]
            e = go(info_rc=1)
            assert "Docker is not running" in e and not ran(), (e, calls)
            omi.shutil.which = lambda _: None
            assert "Docker is not running" in go() and not calls
            omi.shutil.which = lambda _: "docker"
            assert "not inside" in go(task=wt.parent / "x.md") and not calls
            del omi.os.environ[omi.TOKEN_ENV]
            e = go()
            assert "no token" in e and not ran(), e
        finally:
            sys.stdout = saved
            omi.subprocess.run, omi.shutil.which, omi.main_checkout, omi.WINDOWS, tok = real
            omi.os.environ.pop(omi.TOKEN_ENV, None)
            if tok is not None:
                omi.os.environ[omi.TOKEN_ENV] = tok


def test_credential_manager():
    import ctypes
    store = {}

    class Fake:
        keep = []

        def CredWriteW(self, pcred, flags):
            c = pcred._obj
            assert c.Type == 1 and c.Persist == 2
            store[c.TargetName] = ctypes.string_at(c.CredentialBlob, c.CredentialBlobSize)
            return 1

        def CredReadW(self, target, typ, flags, pp):
            if target not in store:
                return 0
            buf = ctypes.create_string_buffer(store[target], len(store[target]))
            c = omi.CRED(TargetName=target, CredentialBlobSize=len(store[target]),
                         CredentialBlob=ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
            self.keep += [buf, c]
            pp._obj.contents = c
            return 1

        def CredFree(self, p):
            store["freed"] = True

    real = omi.advapi, omi.WINDOWS, omi.getpass.getpass, omi.os.environ.pop(omi.TOKEN_ENV, None)
    fake = Fake()
    omi.advapi, omi.WINDOWS = (lambda: fake), True
    out = io.StringIO()
    sys.stdout, saved = out, sys.stdout
    try:
        assert omi.token() is None
        omi.getpass.getpass = lambda prompt: " tok-123 \n"
        omi.token_set()
        assert store[omi.CRED_TARGET] == b"tok-123"
        assert omi.token() == "tok-123" and store["freed"]
        assert "tok-123" not in out.getvalue(), "token echoed"
        omi.WINDOWS = False
        omi.token_set()
        assert omi.TOKEN_ENV in out.getvalue()
        omi.os.environ[omi.TOKEN_ENV] = "env-tok"
        assert omi.token() == "env-tok"
    finally:
        sys.stdout = saved
        omi.advapi, omi.WINDOWS, omi.getpass.getpass, tok = real
        omi.os.environ.pop(omi.TOKEN_ENV, None)
        if tok is not None:
            omi.os.environ[omi.TOKEN_ENV] = tok


def test_template_docker():
    d = omi.TEMPLATE / "docker"
    text = (d / "Dockerfile").read_text()
    assert "python3" in text and "@anthropic-ai/claude-code@2." in text and (d / "prove.sh").exists()
    with tempfile.TemporaryDirectory() as t:
        out = io.StringIO()
        sys.stdout, saved = out, sys.stdout
        try:
            omi.init(t)
        finally:
            sys.stdout = saved
        assert (Path(t) / "docker" / "Dockerfile").exists()


if __name__ == "__main__":
    test_worker()
    test_credential_manager()
    test_template_docker()
    test_init_guard_status()
    test_github_rulesets()
    test_ci_checks_and_apply()
    test_same_and_no_gh()
    test_github_po()
    test_github_private()
    print("ok")
