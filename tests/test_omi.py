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
    assert {"pull_request", "update", "required_status_checks"} <= set(types)
    assert types["required_status_checks"]["parameters"]["required_status_checks"] == [{"context": "test"}]
    assert po["bypass_actors"][0]["actor_id"] == 5

    tags = rs["omi-tags"]
    assert tags["target"] == "tag" and tags["bypass_actors"] == po["bypass_actors"]
    assert tags["conditions"]["ref_name"]["include"] == ["refs/tags/rc-*", "refs/tags/v*"]
    assert sorted(r["type"] for r in tags["rules"]) == ["deletion", "update"]  # no "creation": squad can tag


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
            st["active"] = cmd[-1]
        return R()

    def go(fail_apply=False, **kw):
        st.update(accts=["squad"], active="squad", new="po", calls=[], status_fail=False,
                  status_fail_after=False, login_rc=0, logout_fail=False)
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
        assert go() is None and st["calls"] == ["login", "apply", "logout", "switch"], st["calls"]
        assert st["accts"] == ["squad"] and st["active"] == "squad"
        assert go(fail_apply=True) == "boom" and st["calls"] == ["login", "apply", "logout", "switch"]
        assert st["accts"] == ["squad"]
        e = go(new="")  # same-account guard: no logout
        assert "own account" in e and "logout" not in st["calls"] and "apply" not in st["calls"]
        e = go(active="")  # empty prev: abort before login
        assert "no active squad" in e and st["calls"] == []
        e = go(login_rc=1)  # login fails after saving the token: still cleaned up
        assert "login failed" in e and st["calls"] == ["login", "logout", "switch"] and st["accts"] == ["squad"]
        e = go(status_fail_after=True)  # cannot read accounts after login: loud failure
        assert "WARNING" in e and "apply" not in st["calls"]
        e = go(logout_fail=True)  # logout fails: warning + non-zero, switch still attempted
        assert "WARNING" in e and "po" in e and st["calls"] == ["login", "apply", "logout", "switch"]
        assert st["active"] == "squad"
    finally:
        omi.subprocess.run, omi.shutil.which, omi.apply_github = realrun, realwhich, realapply


if __name__ == "__main__":
    test_init_guard_status()
    test_github_rulesets()
    test_same_and_no_gh()
    test_github_po()
    print("ok")
