import io
import shutil
import json
import contextlib
import subprocess
from helpers import omi


def test_github_rulesets():
    rs = omi.project.github.rulesets()
    dev, po = rs["omi-development"], rs["omi-po-only"]
    assert [r["type"] for r in dev["rules"]] == ["deletion", "non_fast_forward"]
    assert dev["bypass_actors"] == []
    assert po["conditions"]["ref_name"]["include"] == ["refs/heads/staging", "refs/heads/main"]
    types = {r["type"]: r for r in po["rules"]}
    assert {"pull_request", "update"} <= set(types) and "required_status_checks" not in types
    po = omi.project.github.rulesets(["test (ubuntu-latest)", "test (macos-latest)"])["omi-po-only"]
    types = {r["type"]: r for r in po["rules"]}
    assert types["required_status_checks"]["parameters"]["required_status_checks"] == [
        {"context": "test (ubuntu-latest)"}, {"context": "test (macos-latest)"}]
    assert po["bypass_actors"][0]["actor_id"] == 5

    tags = rs["omi-tags"]
    assert tags["target"] == "tag" and tags["bypass_actors"] == po["bypass_actors"]
    assert tags["conditions"]["ref_name"]["include"] == ["refs/tags/rc-*", "refs/tags/v*"]
    assert sorted(r["type"] for r in tags["rules"]) == ["deletion", "update"]  # no "creation": squad can tag


def test_ci_checks_and_apply():
    real_run, real_gh, real_info = subprocess.run, omi.project.github.gh, omi.project.github.repo_info
    done = lambda n: {"name": n, "status": "completed"}
    st = {"runs": [done("test (ubuntu-latest)"), done("test (windows-latest)"), done("test (ubuntu-latest)")],
          "live": None, "puts": [], "newer": []}

    def fake(*a, body=None):
        u = a[-1]
        if body is not None and a[1] == "PUT":
            st["live"] = body
            st["puts"].append(body)
            return None
        if "/commits?" in u:
            return [{"sha": "new"}, {"sha": "old"}]
        if "check-runs" in u:
            return {"check_runs": st["newer"] if "/new/" in u else st["runs"]}
        if u.endswith("/rulesets"):
            return [{"name": "omi-po-only", "id": 1}] if st["live"] else []
        if u.endswith("/rulesets/1"):
            return st["live"]
        if "git/ref" in u:
            return {"object": {"sha": "x"}}
        if body is not None:
            return None
        return {"permissions": {"admin": True}}

    omi.project.github.gh, omi.project.github.repo_info = fake, lambda: "o/r"
    try:
        assert omi.project.github.ci_checks("o/r") == ["test (ubuntu-latest)", "test (windows-latest)"]
        st["runs"] = []
        assert omi.project.github.ci_checks("o/r") == []
        omi.project.github.gh = lambda *a, **k: (_ for _ in ()).throw(omi.project.github.GhError("gh api x failed: HTTP 404", 404))
        assert omi.project.github.ci_checks("o/r") == []
        omi.project.github.gh = lambda *a, **k: (_ for _ in ()).throw(omi.project.github.GhError("gh api x failed: HTTP 500", 500))
        try:
            omi.project.github.ci_checks("o/r")
            assert False, "non-404 error must abort"
        except SystemExit as e:
            assert "500" in str(e)
        # real gh(): "404" in repo/sha must not count as a 404 status
        class R:
            returncode, stdout, stderr = 1, "", "gh: Server Error (HTTP 500)"
        subprocess.run = lambda *a, **k: R()
        omi.project.github.gh = real_gh
        try:
            omi.project.github.ci_checks("app404/r404")
            assert False, "HTTP 500 must abort even if the path contains 404"
        except SystemExit as e:
            assert "required checks left untouched" in str(e)
        R.stderr = "gh: Not Found (HTTP 404)"
        assert omi.project.github.ci_checks("o/r") == []
        subprocess.run = real_run
        omi.project.github.gh = fake
        st["newer"] = [{"name": "test (new)", "status": "queued"}]  # fresh commit, CI not finished
        st["runs"] = [done("test (ubuntu-latest)")]
        assert omi.project.github.ci_checks("o/r") == ["test (ubuntu-latest)"], "walks back past the unfinished commit"
        st["newer"] = [done("test (new)")]
        assert omi.project.github.ci_checks("o/r") == ["test (new)"]
        st["newer"] = []
        st["runs"] = []
        omi.project.github.gh = fake
        import contextlib, io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            omi.project.github.apply_github()
        assert "no CI check runs" in out.getvalue()
        st["live"] = omi.project.github.rulesets()["omi-po-only"]  # no required checks stored
        st["runs"] = [done("test (ubuntu-latest)")]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            omi.project.github.apply_github()
        assert "update ruleset omi-po-only" in out.getvalue() and len(st["puts"]) == 1
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            omi.project.github.apply_github()
        assert "unchanged ruleset omi-po-only" in out.getvalue()
        st["runs"] = [done("test (ubuntu-latest)"), done("test (macos-latest)")]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            omi.project.github.apply_github()
        assert "update ruleset omi-po-only" in out.getvalue()
    finally:
        subprocess.run, omi.project.github.gh, omi.project.github.repo_info = real_run, real_gh, real_info


def test_same_and_no_gh():
    po = omi.project.github.rulesets()["omi-po-only"]
    live = json.loads(json.dumps(po))
    live["id"] = 7
    live["rules"].reverse()
    live["rules"][0].setdefault("parameters", {})
    assert omi.project.github.same(live, po)
    live["rules"].pop()
    assert not omi.project.github.same(live, po)
    real = shutil.which
    shutil.which = lambda _: None
    try:
        omi.project.github.github()
        assert False
    except SystemExit as e:
        assert "gh is not installed" in str(e)
    finally:
        shutil.which = real


def test_github_po():
    realrun, realwhich, realapply = subprocess.run, shutil.which, omi.project.github.apply_github
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
        omi.project.github.apply_github = apply
        try:
            omi.project.github.github(po=True)
            return None
        except SystemExit as e:
            return str(e)

    subprocess.run, shutil.which = run, lambda _: "gh"
    try:
        assert go() is None and st["calls"] == ["view", "login", "apply", "logout", "switch"], st["calls"]
        # logout already restored prev: no extra switch
        orig = run
        def run2(cmd, **kw):
            if cmd[1:3] == ["auth", "logout"]:
                r = orig(cmd, **kw); st["active"] = "squad"; return r
            return orig(cmd, **kw)
        subprocess.run = run2
        assert go() is None and "switch" not in st["calls"], st["calls"]
        subprocess.run = run
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
        subprocess.run, shutil.which, omi.project.github.apply_github = realrun, realwhich, realapply


def test_github_private():
    real = subprocess.run
    class R: stdout, stderr, returncode = "o/r PRIVATE", "", 0
    subprocess.run = lambda *a, **k: R()
    try:
        omi.project.github.apply_github()
        assert False
    except SystemExit as e:
        assert "private" in str(e)
    finally:
        subprocess.run = real


def main():
    test_github_rulesets()
    test_ci_checks_and_apply()
    test_same_and_no_gh()
    test_github_po()
    test_github_private()


if __name__ == "__main__":
    main()
