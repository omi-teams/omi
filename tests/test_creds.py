import io
import shutil
import json
import contextlib
import getpass
import os
import time
import subprocess
import sys
import tempfile
from pathlib import Path
from helpers import omi, git, real_egress


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
            c = omi.creds.CRED(TargetName=target, CredentialBlobSize=len(store[target]),
                         CredentialBlob=ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
            self.keep += [buf, c]
            pp._obj.contents = c
            return 1

        def CredFree(self, p):
            store["freed"] = True

    real = omi.creds.advapi, omi.core.WINDOWS, getpass.getpass, os.environ.pop(omi.creds.TOKEN_ENV, None)
    fake = Fake()
    omi.creds.advapi, omi.core.WINDOWS = (lambda: fake), True
    out = io.StringIO()
    sys.stdout, saved = out, sys.stdout
    try:
        assert omi.creds.token() is None
        getpass.getpass = lambda prompt: " tok-123 \n"
        omi.creds.token_set()
        assert store[omi.creds.CRED_TARGET] == b"tok-123"
        assert omi.creds.token() == "tok-123" and store["freed"]
        assert "tok-123" not in out.getvalue(), "token echoed"
        omi.core.WINDOWS = False
        omi.creds.token_set()
        assert omi.creds.TOKEN_ENV in out.getvalue()
        os.environ[omi.creds.TOKEN_ENV] = "env-tok"
        assert omi.creds.token() == "env-tok"
        # codex: own target, claude's untouched; env fallback
        omi.core.WINDOWS = True
        os.environ.pop(omi.creds.CODEX_ENV, None)
        assert omi.creds.token("codex") is None
        getpass.getpass = lambda prompt: "sk-abc"
        omi.creds.token_set("codex")
        assert store[omi.creds.CODEX_CRED_TARGET] == b"sk-abc" and store[omi.creds.CRED_TARGET] == b"tok-123"
        assert omi.creds.token("codex") == "sk-abc" and omi.creds.token() == "tok-123"
        assert "sk-abc" not in out.getvalue()
        del store[omi.creds.CODEX_CRED_TARGET]
        os.environ[omi.creds.CODEX_ENV] = "sk-env"
        assert omi.creds.token("codex") == "sk-env"
    finally:
        sys.stdout = saved
        omi.creds.advapi, omi.core.WINDOWS, getpass.getpass, tok = real
        os.environ.pop(omi.creds.TOKEN_ENV, None)
        if tok is not None:
            os.environ[omi.creds.TOKEN_ENV] = tok


def test_usage():
    claude = json.dumps({"type": "result", "result": "DONE", "duration_ms": 5,
                         "usage": {"input_tokens": 10, "output_tokens": 20,
                                   "cache_read_input_tokens": 100, "cache_creation_input_tokens": 5}})
    assert omi.tools.parse_usage("claude", claude) == ("DONE", 10, 20, 105)
    codex = "\n".join(json.dumps(e) for e in (
        {"type": "item.completed", "item": {"type": "agent_message", "text": "hi"}},
        {"type": "turn.completed", "usage": {"input_tokens": 7, "cached_input_tokens": 3, "output_tokens": 2}},
        {"type": "turn.completed", "usage": {"input_tokens": 1, "cached_input_tokens": 0, "output_tokens": 1}}))
    assert omi.tools.parse_usage("codex", codex) == ("hi", 8, 3, 3)
    assert omi.tools.parse_usage("claude", "garbage") == (None, None, None, None)
    with tempfile.TemporaryDirectory() as d:
        task = Path(d) / "TASK-001.md"
        task.write_text("---\nid: TASK-001\n---\n## Checkpoint\nDone: x\n", encoding="utf-8")
        omi.tasks.record_usage(task, "omi-agent-engineer", "sonnet", "medium", (10, 20, 105), 3.2)
        omi.tasks.record_usage(task, "omi-agent-reviewer", "opus", "high", (None, None, None), 1)
        omi.tasks.record_usage(task, "omi-agent-reviewer", "opus", "high", (1, 2, 3), 1)
        text = task.read_text(encoding="utf-8")
        assert text.count("## Usage") == 1 and "| omi-agent-engineer | sonnet | medium | 10 | 20 | 105 | 3s | - | - |" in text
        assert "| omi-agent-reviewer | opus | high | n/a | n/a | n/a | 1s | - | - |" in text
        assert omi.tasks.checkpoint(text) == "Done: x"
        assert omi.tasks.usage_totals(text) == "usage: 3 runs, in 11 out 22 cache 108, review rounds: 2"
    assert omi.tasks.usage_totals("## Goal\n") == ""
    old = "\n## Usage\n| role | model | effort | input | output | cache | duration |\n|---|---|---|---|---|---|---|\n| r | m | e | 1 | 2 | 3 | 4s |\n"
    assert omi.tasks.usage_totals(old) == "usage: 1 runs, in 1 out 2 cache 3, review rounds: 0"
    assert omi.tools.verdict_of("x\nVERDICT: FAIL\n**VERDICT: PASS**") == "PASS" and omi.tools.verdict_of("no verdict") is None
    assert omi.tools.verdict_of("VERDICT: FAIL") == "FAIL" and omi.tools.verdict_of(None) is None
    with tempfile.TemporaryDirectory() as d:
        task = Path(d) / "TASK-003.md"
        task.write_text("# t\n\n## Usage\n| role | model | effort | input | output | cache | duration | skills read |\n"
                        "|---|---|---|---|---|---|---|---|\n| r | m | e | 1 | 2 | 3 | 4s | - |\n", encoding="utf-8")
        omi.tasks.record_usage(task, "omi-agent-reviewer", "m", "e", (1, 1, 1), 1, "-", "FAIL")
        text = task.read_text(encoding="utf-8")
        assert "| skills read | verdict |\n|---|---|---|---|---|---|---|---|---|\n| r | m | e | 1 | 2 | 3 | 4s | - |\n" in text
        assert text.rstrip().endswith("| omi-agent-reviewer | m | e | 1 | 1 | 1 | 1s | - | FAIL |")
        assert omi.tasks.usage_totals(text) == "usage: 2 runs, in 2 out 3 cache 4, review rounds: 1"
    assert omi.run.skills_cell([], []) == "-" and omi.run.skills_cell(["a", "b"], ["b"]) == "1/2 b"
    assert omi.run.skills_cell(["a"], []) == "0/1"
    use = lambda p: {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read", "input": {"file_path": p}}]}}
    stream = "\n".join(json.dumps(e) for e in (
        {"type": "system", "subtype": "init"}, use("/work/.omi/skills/g/omi-skill-a/SKILL.md"),
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {"command": "cat /work/.omi/skills/g/omi-skill-b/SKILL.md"}}]}},
        json.loads(claude)))
    assert omi.tools.parse_usage("claude", stream) == ("DONE", 10, 20, 105)
    assert omi.tools.opened_files("claude", stream) == ["/work/.omi/skills/g/omi-skill-a/SKILL.md", "/work/.omi/skills/g/omi-skill-b/SKILL.md"]
    cx = "\n".join(json.dumps(e) for e in (
        {"type": "item.completed", "item": {"type": "command_execution", "command": "bash -lc 'cat /work/.omi/skills/g/omi-skill-b/ref.md'"}},
        {"type": "item.completed", "item": {"type": "agent_message", "text": "hi"}}))
    assert omi.tools.opened_files("codex", cx) == ["/work/.omi/skills/g/omi-skill-b/ref.md"]
    sk = "/work/.omi/skills/g/omi-skill-b/SKILL.md"
    for bad in (f"ls {sk}", f"rm {sk}", f"echo {sk}", f"echo x > {sk}", f"ls {sk} && echo cat"):
        assert omi.tools.read_commands(bad) == [], bad
    assert omi.tools.read_commands(f"bash -lc 'ls && sed -n 1,5p {sk}'") == [sk]
    assert omi.tools.read_commands(f"rg foo {sk} | head") == [sk]
    for wrap in (f"/bin/bash -lc 'cat {sk}'", f"/usr/bin/env bash -c 'cat {sk}'", f"env FOO=1 /bin/sh -c \"head -n 5 {sk}\""):
        assert omi.tools.read_commands(wrap) == [sk], wrap
    for ok in (f"grep -i foo {sk}", f"rg -i foo {sk}", f"less -i {sk}", f"grep -e foo {sk}", f"sed -n 1p {sk}", f"cat < {sk}"):
        assert omi.tools.read_commands(ok) == [sk], ok
    assert omi.tools.read_commands(f"grep -c {sk} README.md") == ["README.md"]
    assert omi.tools.read_commands(f"grep -e {sk} README.md") == ["README.md"]
    for bad in (f"cat x > {sk}", f"cat x >> {sk}", f"cat > {sk} <<EOF", f"sed -i s/a/b/ {sk}", f"sed -i.bak s/a/b/ {sk}",
                f"sed -ni s/a/b/ {sk}", f"sed --in-place=.bak s/a/b/ {sk}", f"sed --in-place s/a/b/ {sk}"):
        assert not any(sk in c for c in omi.tools.read_commands(bad)), bad
    assert omi.tools.read_commands(f"cat {sk} 2>/dev/null") == [sk]
    assert omi.tools.read_commands("cd /work/.omi/skills/g/omi-skill-b && cat SKILL.md") == ["/work/.omi/skills/g/omi-skill-b/SKILL.md"]
    assert omi.tools.read_commands("cat SKILL.md", "/w/skills/x") == ["/w/skills/x/SKILL.md"]
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        for sid in ("a", "b"):
            sd = root / ".omi" / "skills" / "g" / f"omi-skill-{sid}"
            sd.mkdir(parents=True)
            (sd / "SKILL.md").write_text("---\nreferences: ref.md\n---\n", encoding="utf-8")
            (sd / "ref.md").write_text("x", encoding="utf-8")
        ids = ["omi-skill-a", "omi-skill-b"]
        assert omi.run.skills_read(root, ids, omi.tools.opened_files("claude", stream)) == ["omi-skill-a", "omi-skill-b"]
        assert omi.run.skills_read(root, ids, omi.tools.opened_files("codex", cx)) == ["omi-skill-b"]
        cmds = lambda c, **kw: omi.tools.opened_files("codex", json.dumps({"type": "item.completed", **kw, "item": {"type": "command_execution", "command": c}}))
        assert omi.run.skills_read(root, ids, cmds("cd .omi/skills/g/omi-skill-b && cat SKILL.md")) == ["omi-skill-b"]
        assert omi.run.skills_read(root, ids, cmds("cat ../omi-skill-b/ref.md")) == ["omi-skill-b"]
        assert omi.run.skills_read(root, ids, cmds("cat SKILL.md", cwd="/work/.omi/skills/g/omi-skill-a")) == ["omi-skill-a"]
        assert omi.run.skills_read(root, ids, cmds("cat SKILL.md")) == []
        assert omi.run.skills_read(root, ids, cmds("cd .omi/skills/g/omi-skill-b && cat x > SKILL.md")) == []
        assert omi.run.skills_read(root, ids, cmds("cd .omi/skills/g/omi-skill-b && sed -i s/a/b/ SKILL.md")) == []
        assert omi.run.skills_read(root, ids, cmds("/bin/bash -lc 'cd .omi/skills/g/omi-skill-a && cat SKILL.md'")) == ["omi-skill-a"]
        assert omi.run.skills_read(root, ids, cmds("grep -i x omi-skill-b/SKILL.md")) == ["omi-skill-b"]
        for bad in ("grep -c omi-skill-b/SKILL.md README.md", "cat omi-skill-b/SKILL.md.bak", "cat xomi-skill-b/SKILL.md",
                    "sed -ni s/a/b/ omi-skill-b/SKILL.md", "echo omi-skill-b/SKILL.md | cat"):
            assert omi.run.skills_read(root, ids, cmds(bad)) == [], bad
        neg = json.dumps({"type": "item.completed", "item": {"type": "command_execution", "command": "rm /work/.omi/skills/g/omi-skill-b/SKILL.md"}})
        assert omi.run.skills_read(root, ids, omi.tools.opened_files("codex", neg)) == []
    # existing 7-column table gets the new column; old rows still parse
    with tempfile.TemporaryDirectory() as d:
        task = Path(d) / "TASK-002.md"
        task.write_text("# t\n\n## Usage\n| role | model | effort | input | output | cache | duration |\n|---|---|---|---|---|---|---|\n| r | m | e | 1 | 2 | 3 | 4s |\n", encoding="utf-8")
        omi.tasks.record_usage(task, "r2", "m", "e", (1, 1, 1), 1, "1/1 x")
        text = task.read_text(encoding="utf-8")
        assert "| duration | skills read | verdict |\n|---|---|---|---|---|---|---|---|---|\n| r | m | e | 1 | 2 | 3 | 4s |\n" in text
        assert text.rstrip().endswith("| r2 | m | e | 1 | 1 | 1 | 1s | 1/1 x | - |")
        assert omi.tasks.usage_totals(text) == "usage: 2 runs, in 2 out 3 cache 4, review rounds: 0"
    # run_role records the harness numbers
    real = subprocess.run, shutil.which, omi.core.main_checkout, os.environ.get(omi.creds.TOKEN_ENV)

    class R:
        def __init__(s, out="", rc=0): s.stdout, s.returncode, s.stderr = out, rc, ""

    run_out = [claude]

    def run(cmd, **kw):
        if "--git-common-dir" in cmd:
            return R(str(Path(cmd[2]) / "shared.git"))
        if cmd[:2] == ["docker", "run"]:
            return R(run_out[0])
        if "status" in cmd:
            return R(" M src/a.py\0")
        if "show" in cmd:
            return R("---\nscope: src/**\n---\n")
        return R()

    with tempfile.TemporaryDirectory() as d:
        wt = Path(d).resolve()
        (wt / ".git").write_text("gitdir: /x")
        task = wt / ".omi" / "tasks" / "TASK-001.md"
        task.parent.mkdir(parents=True)
        task.write_text("---\nid: TASK-001\nscope: src/**\n---\n## Goal\ng\n", encoding="utf-8")
        subprocess.run, shutil.which, omi.core.main_checkout = run, lambda _: "docker", (lambda _: wt)
        os.environ[omi.creds.TOKEN_ENV] = "tok"
        sys.stdout, saved = io.StringIO(), sys.stdout
        try:
            omi.run.run_role("omi-agent-engineer", wt, task)
        finally:
            sys.stdout = saved
            subprocess.run, shutil.which, omi.core.main_checkout, tok = real
            os.environ.pop(omi.creds.TOKEN_ENV, None)
            if tok is not None:
                os.environ[omi.creds.TOKEN_ENV] = tok
        assert "| omi-agent-engineer |" in task.read_text(encoding="utf-8") and "| 10 | 20 | 105 |" in task.read_text(encoding="utf-8")
        # one declared skill read, one not: warning printed, exit code unchanged, cell recorded
        for sid in ("a", "b"):
            sd = wt / ".omi" / "skills" / "g" / f"omi-skill-{sid}"
            sd.mkdir(parents=True)
            (sd / "SKILL.md").write_text("---\ndescription: d\n---\n", encoding="utf-8")
        omi.catalogs.skills_catalog(wt)
        task.write_text("---\nid: TASK-001\nscope: src/**\nskills: omi-skill-a, omi-skill-b\n---\n## Goal\ng\n", encoding="utf-8")
        run_out[0] = "\n".join(json.dumps(e) for e in (use("/work/.omi/skills/g/omi-skill-a/SKILL.md"), json.loads(claude)))
        subprocess.run, shutil.which, omi.core.main_checkout = run, lambda _: "docker", (lambda _: wt)
        os.environ[omi.creds.TOKEN_ENV] = "tok"
        sys.stdout, saved = io.StringIO(), sys.stdout
        try:
            rc = omi.run.run_role("omi-agent-engineer", wt, task)
            printed = sys.stdout.getvalue()
        finally:
            sys.stdout = saved
            subprocess.run, shutil.which, omi.core.main_checkout, tok = real
            os.environ.pop(omi.creds.TOKEN_ENV, None)
            if tok is not None:
                os.environ[omi.creds.TOKEN_ENV] = tok
        assert "SKILL NOT READ: omi-skill-b" in printed and "SKILL NOT READ: omi-skill-a" not in printed
        assert rc == 0
        assert "| 1/2 omi-skill-a |" in task.read_text(encoding="utf-8")


def test_git_non_ascii():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve()
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        (root / "README.md").write_text("ASCII\n", encoding="utf-8")
        git(root, "add", "README.md")
        git(root, "commit", "-q", "-m", "init")
        (root / "README.md").write_text("ASCII\nTiếng Việt có dấu\n", encoding="utf-8")
        diff = omi.core.git(root, "diff")
        assert diff is not None and "Tiếng Việt có dấu" in diff, "git() must decode UTF-8 output"


def test_claude_session_login():
    cfg = Path(os.environ["CLAUDE_CONFIG_DIR"])
    cred = cfg / ".credentials.json"
    real = omi.core.WINDOWS, omi.creds.cred_read, os.environ.pop(omi.creds.TOKEN_ENV, None)
    omi.core.WINDOWS, omi.creds.cred_read = True, lambda target: "stored-tok"
    write = lambda exp: cred.write_text(json.dumps({"claudeAiOauth": {"accessToken": "sess-tok", "refreshToken": "REAL-REFRESH",
                                                                      "expiresAt": exp}}))
    try:
        cred.unlink(missing_ok=True)  # missing file: stored
        assert omi.creds.claude_secret() == ("stored-tok", "stored", None)
        write(int((time.time() + 3600) * 1000))  # session beats stored
        assert omi.creds.claude_secret() == ("sess-tok", "session", None)
        assert omi.creds.tool_secret("claude") == (omi.creds.TOKEN_ENV, "sess-tok", None)
        os.environ[omi.creds.TOKEN_ENV] = "env-tok"  # env beats session
        assert omi.creds.claude_secret() == ("env-tok", "env", None)
        del os.environ[omi.creds.TOKEN_ENV]
        write(1000)  # expired: note, falls through to stored
        val, src, note = omi.creds.claude_secret()
        assert (val, src) == ("stored-tok", "stored") and "session login expired" in note
        omi.creds.cred_read = lambda target: None  # nothing usable: no value, note kept
        val, src, note = omi.creds.claude_secret()
        assert val is None and "expired" in note
        # the refresh token is never returned
        write(int((time.time() + 3600) * 1000))
        assert "REAL-REFRESH" not in repr(omi.creds.claude_secret())
    finally:
        omi.core.WINDOWS, omi.creds.cred_read = real[0], real[1]
        cred.unlink(missing_ok=True)
        if real[2]:
            os.environ[omi.creds.TOKEN_ENV] = real[2]


def test_codex_chatgpt_login():
    import base64
    jwt = lambda exp: "h." + base64.urlsafe_b64encode(json.dumps({"exp": exp}).encode()).decode().rstrip("=") + ".s"
    home = Path(os.environ["CODEX_HOME"])
    auth = home / "auth.json"
    os.environ.pop(omi.creds.CODEX_ENV, None)
    real = omi.core.WINDOWS
    omi.core.WINDOWS = False
    try:
        # missing login
        auth.unlink(missing_ok=True)
        env, val, problem = omi.creds.tool_secret("codex")
        assert val is None and "codex login" in problem
        # valid login: slim auth, refresh token never copied
        good = jwt(time.time() + 3600)
        auth.write_text(json.dumps({"auth_mode": "chatgpt", "OPENAI_API_KEY": None, "last_refresh": "t0", "tokens": {
            "access_token": good, "id_token": "idt", "account_id": "acc", "refresh_token": "REAL-REFRESH"}}))
        env, val, problem = omi.creds.tool_secret("codex")
        slim = json.loads(val)
        assert env == omi.creds.CODEX_AUTH_ENV == "OMI_CODEX_AUTH" and problem is None and "REAL-REFRESH" not in val
        assert slim["tokens"] == {"access_token": good, "id_token": "idt", "account_id": "acc", "refresh_token": "omi-no-refresh"}
        assert slim["auth_mode"] == "chatgpt" and slim["last_refresh"] == "t0"
        # an API key (env) goes first
        os.environ[omi.creds.CODEX_ENV] = "sk-env"
        assert omi.creds.tool_secret("codex") == (omi.creds.CODEX_ENV, "sk-env", None)
        del os.environ[omi.creds.CODEX_ENV]
        # expired
        data = json.loads(auth.read_text())
        data["tokens"]["access_token"] = jwt(1)
        auth.write_text(json.dumps(data))
        env, val, problem = omi.creds.tool_secret("codex")
        assert val is None and "expired" in problem and "codex login" in problem
        # allowlist: chatgpt.com only in ChatGPT mode
        with tempfile.TemporaryDirectory() as d:
            assert "chatgpt.com" not in omi.docker.allow_for(Path(d), "codex")
            assert omi.docker.allow_for(Path(d), "codex", chatgpt=True)[-2:] == ["api.openai.com", "chatgpt.com"]
            assert "chatgpt.com" not in omi.docker.allow_for(Path(d), "claude", chatgpt=True)
    finally:
        omi.core.WINDOWS = real
        auth.unlink(missing_ok=True)


def test_codex_chatgpt_run():
    """run_role with a ChatGPT login: the token travels by env name only, the boot wrapper writes auth.json in the container."""
    calls = []
    allowed = []

    @contextlib.contextmanager
    def egress(main, name, image, allow):
        allowed.append(allow)
        yield "test-net", "test-proxy"

    class R:
        def __init__(s, out="", rc=0): s.stdout, s.returncode, s.stderr = out, rc, ""

    def run(cmd, **kw):
        if "--git-common-dir" in cmd:
            return R(str(Path(cmd[2]) / "shared.git"))
        calls.append((cmd, kw))
        if "show" in cmd:
            return R("---\nscope: src/**\n---\n")
        if "status" in cmd:
            return R(" M src/a.py\0")
        if "diff" in cmd and "--name-only" in cmd:
            return R("src/a.py\0")
        return R()

    class P:
        def __init__(s, cmd, **kw): calls.append((cmd, kw)); s.stdout, s.stderr, s.returncode = io.StringIO(""), io.StringIO(""), 0
        def __enter__(s): return s
        def __exit__(s, *a): pass
        def wait(s): pass

    real = subprocess.run, subprocess.Popen, shutil.which, omi.core.main_checkout, omi.core.WINDOWS, omi.docker.ensure_image
    real_egress, omi.docker.egress = omi.docker.egress, egress
    claude_token = os.environ.get(omi.creds.TOKEN_ENV)
    os.environ[omi.creds.TOKEN_ENV] = "CLAUDE-SECRET"
    auth = Path(os.environ["CODEX_HOME"]) / "auth.json"
    os.environ.pop(omi.creds.CODEX_ENV, None)
    with tempfile.TemporaryDirectory() as d:
        wt = Path(d).resolve()
        (wt / ".git").write_text("gitdir: /x")
        task = wt / ".omi" / "tasks" / "TASK-001.md"
        subprocess.run, subprocess.Popen, shutil.which = run, P, lambda _: "docker"
        omi.core.main_checkout, omi.core.WINDOWS, omi.docker.ensure_image = (lambda _: wt), False, lambda m: "img"
        saved, sys.stdout = sys.stdout, io.StringIO()
        try:
            auth.unlink(missing_ok=True)
            try:
                omi.run.run_role("omi-agent-engineer", wt, task, tool="codex", model="gpt-6.1-sol")
                raise AssertionError("ran without credentials")
            except SystemExit as e:
                assert "codex login" in str(e) and "omi token set --tool codex" in str(e), e
            assert not [c for c in calls if c[0][:2] == ["docker", "run"]]
            tok = "h." + "e30" + ".secretsig"
            auth.write_text(json.dumps({"auth_mode": "chatgpt", "tokens": {"access_token": tok, "refresh_token": "REAL-REFRESH"}}))
            calls.clear()
            omi.run.run_role("omi-agent-engineer", wt, task, tool="codex", model="gpt-6.1-sol")
            argv, kw = next(c for c in calls if c[0][:2] == ["docker", "run"])
            assert omi.creds.CODEX_AUTH_ENV in argv and not any(tok in x or "REAL-REFRESH" in x for x in argv)
            i = argv.index("img")
            assert argv[i + 1:i + 3] == ["sh", "-c"] and "printenv OMI_CODEX_AUTH" in argv[i + 3] and "codex" in argv[i + 5:]
            assert tok in kw["env"][omi.creds.CODEX_AUTH_ENV] and "REAL-REFRESH" not in kw["env"][omi.creds.CODEX_AUTH_ENV]
            assert omi.creds.TOKEN_ENV not in kw["env"]
            env_args = [argv[n + 1] for n, arg in enumerate(argv) if arg == "-e"]
            assert omi.creds.CODEX_AUTH_ENV in env_args and omi.creds.CODEX_ENV not in env_args
            assert omi.creds.TOKEN_ENV not in env_args and "CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=0" not in env_args
            mounts = [argv[n + 1] for n, arg in enumerate(argv) if arg == "-v"]
            assert mounts == [f"{wt}:/work", f"{wt / '.git'}:/work/.git:ro"]
            tmpfs = [argv[n + 1] for n, arg in enumerate(argv) if arg == "--tmpfs"]
            assert any(m.startswith("/home/node:rw,noexec,nosuid,") for m in tmpfs)
            assert "HOME=/home/node" in env_args and "--read-only" in argv
            assert allowed == [[*omi.docker.DEFAULT_ALLOW, "api.openai.com", "chatgpt.com"]]
            assert not any(secret in repr(calls) for secret in ("CLAUDE-SECRET", "REAL-REFRESH"))
            for path in wt.rglob("*"):
                if path.is_file():
                    assert tok not in path.read_text(encoding="utf-8")
            # API-key runs pass only their key and add only the API host.
            calls.clear()
            allowed.clear()
            os.environ[omi.creds.CODEX_ENV] = "sk-CODEX-SECRET"
            omi.run.run_role("omi-agent-engineer", wt, task, tool="codex", model="gpt-6.1-sol")
            argv, kw = next(c for c in calls if c[0][:2] == ["docker", "run"])
            env_args = [argv[n + 1] for n, arg in enumerate(argv) if arg == "-e"]
            assert omi.creds.CODEX_ENV in env_args and omi.creds.CODEX_AUTH_ENV not in env_args and omi.creds.TOKEN_ENV not in env_args
            assert "sk-CODEX-SECRET" not in repr(argv) and omi.creds.TOKEN_ENV not in kw["env"]
            assert allowed == [[*omi.docker.DEFAULT_ALLOW, "api.openai.com"]]
        finally:
            sys.stdout = saved
            omi.docker.egress = real_egress
            os.environ.pop(omi.creds.CODEX_ENV, None)
            os.environ.pop(omi.creds.TOKEN_ENV, None)
            if claude_token is not None:
                os.environ[omi.creds.TOKEN_ENV] = claude_token
            auth.unlink(missing_ok=True)
            subprocess.run, subprocess.Popen, shutil.which, omi.core.main_checkout, omi.core.WINDOWS, omi.docker.ensure_image = real


def test_codex_auth_boot_nested_process():
    """The real POSIX bootstrap leaves slim auth readable by descendants, without its transport env."""
    if os.name == "nt":
        return  # the bootstrap runs in the Linux worker
    with tempfile.TemporaryDirectory() as d:
        home = Path(d)
        auth = json.dumps({"auth_mode": "chatgpt", "tokens": {
            "access_token": "test-access", "refresh_token": "omi-no-refresh"}})
        # This child starts a grandchild, as a worker agent does for a nested CLI.
        probe = """import json, os, stat
from pathlib import Path
p = Path.home() / '.codex' / 'auth.json'
assert stat.S_IMODE(p.stat().st_mode) == 0o600
assert json.loads(p.read_text(encoding='utf-8'))['tokens'] == {
    'access_token': 'test-access', 'refresh_token': 'omi-no-refresh'}
assert 'OMI_CODEX_AUTH' not in os.environ
print('ok')
"""
        child = "import subprocess, sys; subprocess.run([sys.executable, '-c', sys.argv[1]], check=True)"
        result = subprocess.run([omi.run.host_bash() or "sh", "-c", omi.creds.CODEX_AUTH_BOOT, "sh", sys.executable, "-c", child, probe],
                                env={"PATH": os.environ["PATH"], "HOME": str(home), omi.creds.CODEX_AUTH_ENV: auth},
                                capture_output=True, encoding="utf-8", check=True)
        assert result.stdout == "ok\n" and result.stderr == ""


def test_subprocess_text_encoding():
    import ast
    src = (Path(__file__).parents[1] / "src" / "omi" / "__init__.py").read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Call) and any(k.arg == "text" for k in node.keywords):
            assert any(k.arg == "encoding" for k in node.keywords), f"line {node.lineno}: text=True needs encoding= (locale decoding on Windows)"
    # the agent run path: UTF-8 output from the container must reach ## Reports unchanged
    real = subprocess.run, shutil.which, omi.core.main_checkout, omi.core.WINDOWS, os.environ.get(omi.creds.TOKEN_ENV)
    report = "Xong → Tiếng Việt có dấu"
    stdout = (json.dumps({"result": report, "usage": {"input_tokens": 1, "output_tokens": 1}}, ensure_ascii=False) + "\n").encode("utf-8")

    class R:
        def __init__(s, out="", rc=0): s.stdout, s.returncode, s.stderr = out, rc, ""

    def run(cmd, **kw):
        if "--git-common-dir" in cmd:
            return R(str(Path(cmd[2]) / "shared.git"))
        if cmd[:2] == ["docker", "info"]:
            return R()
        if "show" in cmd:
            return R("---\nscope: src/**\n---\n")
        if "status" in cmd:
            return R(" M src/a.py\0")
        if "diff" in cmd and "--name-only" in cmd:
            return R("src/a.py\0")
        if cmd[:2] == ["docker", "run"]:
            return R(stdout)  # bytes, as a real process would produce them
        return R()

    with tempfile.TemporaryDirectory() as d:
        wt = Path(d).resolve()
        (wt / ".git").write_text("gitdir: /x")
        task = wt / ".omi" / "tasks" / "TASK-001.md"
        task.parent.mkdir(parents=True)
        task.write_text("---\nid: TASK-001\nscope: src/**\n---\n## Goal\n- [ ] x\n", encoding="utf-8")
        subprocess.run, shutil.which = run, lambda _: "docker"
        omi.core.main_checkout, omi.core.WINDOWS = (lambda _: wt), False
        os.environ[omi.creds.TOKEN_ENV] = "tok"
        sys.stdout, saved = io.StringIO(), sys.stdout
        try:
            omi.run.run_role("omi-agent-reviewer", wt, task)
        finally:
            sys.stdout = saved
            subprocess.run, shutil.which, omi.core.main_checkout, omi.core.WINDOWS = real[:4]
            if real[4] is None: os.environ.pop(omi.creds.TOKEN_ENV, None)
            else: os.environ[omi.creds.TOKEN_ENV] = real[4]
        assert report in task.read_text(encoding="utf-8").partition("## Reports")[2], "UTF-8 report must reach ## Reports unchanged"


def main():
    test_usage()
    test_claude_session_login()
    test_codex_chatgpt_login()
    test_codex_chatgpt_run()
    test_codex_auth_boot_nested_process()
    test_git_non_ascii()
    test_subprocess_text_encoding()
    test_credential_manager()


if __name__ == "__main__":
    main()
