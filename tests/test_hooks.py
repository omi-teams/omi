import io
import re
import shutil
import json
import os
import time
import subprocess
import sys
import tempfile
from pathlib import Path
from helpers import omi, assert_download_cache_env, git


def test_windows_test_shell():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / ".omi").mkdir()
        (root / ".omi" / "config.json").write_text('{"test": "FOO=1 example"}', encoding="utf-8")
        real = omi.core.WINDOWS, shutil.which, os.get_exec_path
        system32 = "C:\\Windows\\sYsTeM32\\"
        git_bin = r"C:\Program Files\Git\bin"
        bash = git_bin + r"\bash.exe"
        try:
            omi.core.WINDOWS = True
            os.get_exec_path = lambda: [system32, git_bin]

            def which(name, path=None):
                assert name == "bash" and path == git_bin, path
                return bash

            shutil.which = which
            assert omi.run.test_command(root, root) == [bash, "-c", "FOO=1 example"]
            assert omi.run.test_prompt_line(root, root) == "FOO=1 example"

            def missing(name, path=None):
                assert name in ("bash", "git") and path == git_bin, path
                return None

            shutil.which = missing
            assert omi.run.test_command(root, root) == 'cmd /d /s /c "FOO=1 example"'
            assert omi.run.test_prompt_line(root, root) == "FOO=1 example"
            python = sys.executable.replace("\\", "/")
            for code in (0, 3):
                command = f'set "FOO=1" && "{python}" -c "import os,sys;sys.exit({code} if os.environ[\'FOO\']==\'1\' else 1)"'
                (root / ".omi" / "config.json").write_text(json.dumps({"test": command}), encoding="utf-8")
                cmd = omi.run.test_command(root, root)
                assert cmd == f'cmd /d /s /c "{command}"'
                assert omi.run.test_prompt_line(root, root) == command
                if real[0]:  # exercise actual cmd quoting on the Windows host
                    assert subprocess.run(cmd, cwd=d).returncode == code
            (root / ".omi" / "config.json").write_text('{"test": "FOO=1 example"}', encoding="utf-8")
            os.get_exec_path = lambda: [system32]
            shutil.which = lambda name, path=None: None if path == "" else system32 + "bash.exe"
            assert omi.run.test_command(root, root) == 'cmd /d /s /c "FOO=1 example"'
            # WindowsApps alias skipped; Git Bash found from git.exe in Git\cmd while Git\bin is not on PATH
            (root / "Git" / "cmd").mkdir(parents=True)
            (root / "Git" / "bin").mkdir()
            (root / "Git" / "bin" / "bash.exe").write_text("", encoding="utf-8")
            cmd_dir, apps = str(root / "Git" / "cmd"), r"C:\Users\u\AppData\Local\Microsoft\WindowsApps"
            os.get_exec_path = lambda: [apps, system32, cmd_dir]

            def which_git(name, path=None):
                assert path == cmd_dir, path
                return str(root / "Git" / "cmd" / "git.exe") if name == "git" else None

            shutil.which = which_git
            assert omi.run.test_command(root, root) == [str(root / "Git" / "bin" / "bash.exe"), "-c", "FOO=1 example"]
            (root / "Git" / "bin" / "bash.exe").unlink()
            assert omi.run.test_command(root, root) == 'cmd /d /s /c "FOO=1 example"'
        finally:
            omi.core.WINDOWS, shutil.which, os.get_exec_path = real


def test_hooks():
    real = subprocess.run, shutil.which, omi.core.main_checkout, omi.core.WINDOWS, os.environ.get(omi.creds.TOKEN_ENV)
    calls, st = [], {}

    class R:
        def __init__(s, out=b"", rc=0): s.stdout, s.returncode, s.stderr = out, rc, ""

    def run(cmd, **kw):
        if "--git-common-dir" in cmd:
            return R(str(Path(cmd[2]) / "shared.git"))
        calls.append((cmd, kw))
        if cmd[:2] == ["docker", "run"]:
            assert (wt / "shared.git" / "info" / "exclude").read_text(encoding="utf-8").splitlines().count(".omi-cache/") == 1
        if cmd[:2] == ["docker", "info"]:
            return R(rc=0)
        if cmd[:2] == ["docker", "run"] and cmd[-2:] in (["sh", "-s"], ["python3", "-"]):
            return R(b"HOOKOUT", st.get("hook_rc", 0))
        if cmd[:2] == ["docker", "run"] and "agent_out" in st:
            return R(st["agent_out"])
        if "show" in cmd:
            return R("---\nscope: src/**\n---\n")
        if "status" in cmd:
            return R("")
        return R()

    def hooks():
        return [c for c in calls if c[0][:2] == ["docker", "run"] and c[0][-2:] in (["sh", "-s"], ["python3", "-"])]

    def agents():
        return [c for c in calls if c[0][:2] == ["docker", "run"] and c not in hooks()]

    with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
        main, wt = Path(d1).resolve(), Path(d2).resolve() / "wt"
        sys.stdout, saved = io.StringIO(), sys.stdout
        try:
            omi.upgrade.init(main)
            assert (main / ".omi" / "hooks" / "post-run.sh").is_file()  # the template ships it
            (main / ".omi" / "hooks" / "post-run.sh").unlink()
            wt.mkdir()
            shutil.copytree(main / ".omi", wt / ".omi")
            (wt / ".git").write_text("gitdir: /x")
            task = wt / ".omi" / "tasks" / "TASK-001.md"
            task.parent.mkdir(parents=True, exist_ok=True)
            task.write_text("---\nid: TASK-001\nstatus: in-progress\n---\n## Reports\n")
            subprocess.run, shutil.which = run, lambda _: "docker"
            omi.core.main_checkout, omi.core.WINDOWS = (lambda _: main), False
            os.environ[omi.creds.TOKEN_ENV] = "tok"
            go = lambda: omi.run.run_role("omi-agent-engineer", wt, task)  # noqa: E731
            # no hook file: no extra docker call
            calls.clear()
            assert go() == 0 and not hooks() and len(agents()) == 1
            assert_download_cache_env(agents()[0][0])
            # a hook only in the worktree is not run
            (wt / ".omi" / "hooks").mkdir(exist_ok=True)
            (wt / ".omi" / "hooks" / "pre-run.sh").write_text("exit 1")
            calls.clear()
            assert go() == 0 and not hooks()
            # pre-run in main passes: it runs before the agent, in an isolated container
            hook = main / ".omi" / "hooks" / "pre-run.sh"
            hook.parent.mkdir(exist_ok=True)
            hook.write_bytes(b"echo hi\r\n")
            config = main / ".omi" / "config.json"
            cfg = json.loads(config.read_text(encoding="utf-8"))
            cfg["worker"] = {"cache_mb": 3072}
            config.write_text(json.dumps(cfg), encoding="utf-8")
            calls.clear()
            assert go() == 0
            (argv, kw), = hooks()
            assert_download_cache_env(argv)
            assert "/cache:rw,exec,nosuid,uid=1000,gid=1000,size=3072m" in argv
            assert calls.index((argv, kw)) < calls.index(agents()[0]) and kw["input"] == b"echo hi\n"
            assert argv[argv.index("--network") + 1] == "none" and "--rm" in argv and f"{wt}:/work:ro" in argv
            assert "-w" in argv and argv[argv.index("-w") + 1] == "/work" and "omi-worker=1" in argv
            assert [a for i, a in enumerate(argv) if argv[i - 1] == "-e"] == ["HOME=/home/node", *omi.docker.CACHE_ENV]  # no token name
            assert omi.creds.TOKEN_ENV not in kw["env"] and "tok" not in " ".join(argv)
            assert "hook pre-run passed" in task.read_text()
            # failing pre-run: agent never started, output in Reports
            st["hook_rc"] = 3
            calls.clear()
            assert go() == 6 and not agents()
            assert "hook pre-run FAILED (exit 3)" in task.read_text() and "> HOOKOUT" in task.read_text()
            # failing post-run: rc 6, and `step done` is refused until a rerun passes
            hook.unlink()
            (main / ".omi" / "hooks" / "post-run.py").write_text("import sys")
            calls.clear()
            st["agent_out"] = b"DONE: all criteria met\n"
            assert go() == 6 and len(agents()) == 1 and hooks()[0][0][-2:] == ["python3", "-"]
            del st["agent_out"]
            assert "hook post-run FAILED (exit 3)" in task.read_text()
            assert "post-run hook failed: the task cannot move to review" in sys.stdout.getvalue()
            assert "hook post-run FAILED (exit 3)" in sys.stdout.getvalue()
            real_tw = omi.core.task_worktrees
            omi.core.task_worktrees = lambda _: {"TASK-001": str(wt)}
            task.write_text(task.read_text().replace("status: in-progress", "workflow: omi-flow-feature\nstep: plan")
                            + "\n## Steps\n- plan started 2026-01-01 00:00\n")
            try:
                omi.tasks.step(main, "TASK-001", "done")
                raise AssertionError("step done passed after a failed post-run")
            except SystemExit as e:
                assert "post-run hook failed" in str(e), e
            st["hook_rc"] = 0
            assert go() == 0
            assert "WARNING: step plan of TASK-001 is for coordinator, not omi-agent-engineer" in sys.stdout.getvalue()
            # a manual `omi hook` records its result like `omi run`
            real_mc = omi.core.main_checkout
            omi.core.main_checkout = lambda _: main
            st["hook_rc"] = 3
            try:
                sys.stdout.truncate(0)
                assert omi.hooks.hook_cmd("post-run", "TASK-001") == 3
                assert "hook post-run FAILED (exit 3)" in task.read_text()
                assert sys.stdout.getvalue().endswith("hook post-run FAILED (exit 3)\n")
                st["hook_rc"] = 0
                sys.stdout.truncate(0)
                assert omi.hooks.hook_cmd("post-run", "TASK-001") == 0 and "hook post-run passed" in task.read_text()
                assert sys.stdout.getvalue().endswith("hook post-run passed\n")
            finally:
                omi.core.main_checkout = real_mc
            assert omi.tasks.step(main, "TASK-001", "done") == 0
            # the guard reads only the Reports header line: hook output cannot fake `passed`
            st["hook_rc"] = 3
            assert go() == 6
            task.write_text(re.sub(r"- plan done.*\n", "", task.read_text()) + "> hook post-run passed\n")
            try:
                omi.tasks.step(main, "TASK-001", "done")
                raise AssertionError("step done passed on faked output")
            except SystemExit as e:
                assert "post-run hook failed" in str(e), e
            st["hook_rc"] = 0
            assert go() == 0
            # a hanging hook is killed by name and fails with a timeout message
            (main / ".omi" / "hooks" / "post-run.py").write_text("import time")
            (main / ".omi" / "config.json").write_text('{"hook_timeout": 7}')
            real_run = subprocess.run

            def hang(cmd, **kw):
                if cmd[:2] == ["docker", "run"] and cmd[-2:] == ["python3", "-"]:
                    assert kw["timeout"] == 7 and "--name" in cmd
                    calls.append((cmd, kw))
                    raise subprocess.TimeoutExpired(cmd, 7)
                return real_run(cmd, **kw)
            subprocess.run = hang
            calls.clear()
            assert go() == 6 and "hook post-run timed out after 7 s" in task.read_text()
            assert any(c[0][:3] == ["docker", "rm", "-f"] and c[0][3] == hooks()[0][0][hooks()[0][0].index("--name") + 1] for c in calls)
            subprocess.run = real_run
            (main / ".omi" / "config.json").unlink()
            # read roles run no hooks
            calls.clear()
            (main / ".omi" / "hooks" / "pre-run.sh").write_text("exit 1")
            omi.run.deterministic_checks, real_dc = (lambda *a: []), omi.run.deterministic_checks
            try:
                omi.run.run_role("omi-agent-architect", wt, task)
            finally:
                omi.run.deterministic_checks = real_dc
            assert agents() and not hooks()
            assert_download_cache_env(agents()[0][0])
            assert f"{wt}:/work:ro" in agents()[0][0]
            (main / ".omi" / "hooks" / "pre-run.sh").unlink()
            # pre-merge CLI: runs against the task worktree, exits with the hook's code; no hook is a no-op
            try:
                assert omi.hooks.hook_cmd("pre-merge", "TASK-001") == 0 and "no pre-merge hook" in sys.stdout.getvalue()
                (main / ".omi" / "hooks" / "pre-merge.sh").write_text("exit 4")
                st["hook_rc"] = 4
                assert omi.hooks.hook_cmd("pre-merge", "TASK-001") == 4
            finally:
                omi.core.task_worktrees = real_tw
        finally:
            sys.stdout = saved
            subprocess.run, shutil.which, omi.core.main_checkout, omi.core.WINDOWS, tok = real
            os.environ.pop(omi.creds.TOKEN_ENV, None)
            if tok is not None:
                os.environ[omi.creds.TOKEN_ENV] = tok
    # the shipped post-run.sh: exits 0 and says so when the project has no tests
    with tempfile.TemporaryDirectory() as d:
        sh = shutil.which("sh")
        if sh:
            r = subprocess.run([sh, str(omi.core.TEMPLATE / "dot-omi" / "hooks" / "post-run.sh")], cwd=d, capture_output=True, text=True)
            assert r.returncode == 0 and "no tests found" in r.stdout, r
            # tests exist but the runner is missing: exit 1 naming the tool (empty PATH; the script uses only sh builtins)
            bindir = Path(d) / "bin"
            bindir.mkdir()
            env = {"PATH": str(bindir)}
            for name, files in (("go", {"go.mod": ""}), ("npm", {"package.json": '{"scripts":{"test":"x"}}'})):
                w = Path(d) / name
                w.mkdir()
                for fn, c in files.items():
                    (w / fn).write_text(c)
                r = subprocess.run([sh, str(omi.core.TEMPLATE / "dot-omi" / "hooks" / "post-run.sh")], cwd=w, capture_output=True, text=True, env=env)
                assert r.returncode == 1 and f"{name} not in the worker image" in r.stdout, r
            # python tests only under tests/ (none at the root) are detected
            w = Path(d) / "py"
            (w / "tests").mkdir(parents=True)
            (w / "tests" / "test_x.py").write_text("")
            r = subprocess.run([sh, str(omi.core.TEMPLATE / "dot-omi" / "hooks" / "post-run.sh")], cwd=w, capture_output=True, text=True, env=env)
            assert "no tests found" not in r.stdout and "pytest not in the worker image" in r.stdout, r
    text = (omi.core.TEMPLATE / "dot-omi" / "hooks" / "post-run.sh").read_text()
    assert all(w in text for w in ("pytest", "go test", "npm test"))
    for f in (Path("AGENTS.md"), omi.core.TEMPLATE / "AGENTS.md", Path(".claude/skills/omi-task/SKILL.md"),
              omi.core.TEMPLATE / "dot-claude" / "skills" / "omi-task" / "SKILL.md"):
        assert "hook" in (Path(__file__).parents[1] / f if not f.is_absolute() else f).read_text(encoding="utf-8"), f


def test_run_read_role():
    real = subprocess.run, shutil.which, omi.core.main_checkout, omi.core.WINDOWS, os.environ.get(omi.creds.TOKEN_ENV)
    calls = []
    st = {}

    class R:
        def __init__(s, out="", rc=0): s.stdout, s.returncode, s.stderr = out, rc, ""

    def run(cmd, **kw):
        if "--git-common-dir" in cmd:
            return R(str(Path(cmd[2]) / "shared.git"))
        calls.append((cmd, kw))
        if cmd[:2] == ["docker", "run"]:
            assert (wt / "shared.git" / "info" / "exclude").read_text(encoding="utf-8").splitlines().count(".omi-cache/") == 1
        if cmd[:2] == ["docker", "info"]:
            return R(rc=st["info_rc"])
        if "show" in cmd:
            return R("---\nscope: src/**\n---\n")
        if "status" in cmd:
            return R(" M src/a.py\0")
        if "diff" in cmd and "--name-only" in cmd:
            return R("src/a.py\0" + st.get("extra", ""))
        if cmd[0] == sys.executable:
            return R("tests out", st.get("tests_rc", 0))
        return R()

    def docker_runs():
        return [c for c in calls if c[0][:2] == ["docker", "run"]]

    with tempfile.TemporaryDirectory() as d:
        wt = Path(d).resolve()
        (wt / ".git").write_text("gitdir: /x")
        task = wt / ".omi" / "tasks" / "TASK-001.md"
        subprocess.run, shutil.which = run, lambda _: "docker"
        omi.core.main_checkout, omi.core.WINDOWS = (lambda _: wt), False
        os.environ[omi.creds.TOKEN_ENV] = "tok"
        out = io.StringIO()
        sys.stdout, saved = out, sys.stdout
        try:
            def go(**kw):
                calls.clear()
                st.clear()
                st.update(info_rc=0)
                st.update(kw)
                try:
                    return omi.run.run_role("omi-agent-reviewer", wt, task)
                except SystemExit as e:
                    return str(e)

            assert go() == 0
            argv = docker_runs()[0][0]
            assert f"{wt}:/work:ro" in argv and f"{wt}:/work" not in argv, "read role must mount the worktree ro"
            assert f"{wt / '.git'}:/work/.git:ro" in argv and "omi-role=omi-agent-reviewer" in argv
            assert any(a.endswith(":/review:ro") for a in argv) and "Diff: /review/diff.patch" in argv[argv.index("claude") + 2]
            assert "bypassPermissions" in argv  # the ro mount, not prompts, is the boundary
            # the write role keeps a rw mount
            calls.clear()
            omi.run.run_role("omi-agent-engineer", wt, task)
            assert f"{wt}:/work" in docker_runs()[0][0]
            # codex: no key names `omi token set --tool codex`; with the env key it runs, key by name only
            os.environ.pop(omi.creds.CODEX_ENV, None)
            calls.clear()
            try:
                omi.run.run_role("omi-agent-engineer", wt, task, tool="codex", model="gpt-6.1-sol")
                raise AssertionError("ran without a key")
            except SystemExit as e:
                assert "omi token set --tool codex" in str(e) and not docker_runs(), e
            os.environ[omi.creds.CODEX_ENV] = "sk-SECRET"
            try:
                omi.run.run_role("omi-agent-engineer", wt, task, tool="codex", model="gpt-6.1-sol")
            finally:
                del os.environ[omi.creds.CODEX_ENV]
            argv = docker_runs()[0][0]
            assert omi.creds.CODEX_ENV in argv and not any("sk-SECRET" in x for x in argv)
            # a failing check blocks the role: no container, failure reported
            for kw, word in (({"tests_rc": 1}, "tests failed"), ({"extra": "docs/x.md\0"}, "outside scope: docs/x.md")):
                out.truncate(0); out.seek(0)
                assert go(**kw) == 4 and not docker_runs() and word in out.getvalue(), out.getvalue()
            # no host fallback when Docker is down
            e = go(info_rc=1)
            assert "Docker is not running" in e and not docker_runs()
            # the current step's skills join the prompt; the prompt names the test command
            st["info_rc"] = 0
            d = wt / ".omi" / "skills" / "g" / "omi-skill-zz"
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text(
                "---\nid: omi-skill-zz\ngroup: g\ndescription: use for zz\ntokens: 1\ntools: Read\nsource_repo: r\nsource_ref: v1.0\n"
                "source_file: f\nsource_license: MIT\nsource_use: adapt\n---\n# zz\n"
                + "".join(f"## {h}\nx\n" for h in ("When to use", "When not to use", "Inputs", "Steps", "Outputs and evidence", "Stop and escalate", "Tools needed")))
            omi.catalogs.skills_catalog(wt)
            (wt / ".omi" / "workflows").mkdir(parents=True)
            task.parent.mkdir(parents=True, exist_ok=True)
            (wt / ".omi" / "workflows" / "omi-flow-zz.md").write_text(
                "---\nid: omi-flow-zz\nsummary: s\nsteps:\n"
                "- id: build | role: omi-agent-engineer | skills: omi-skill-zz | input: i | output: o | gate: none | stop: s\n"
                "- id: review | role: omi-agent-reviewer | skills: | input: i | output: o | gate: review | stop: s\n---\nx\n")
            prompt = lambda: docker_runs()[0][0][docker_runs()[0][0].index("claude") + 2]  # noqa: E731
            task.write_text("---\nid: TASK-001\nworkflow: omi-flow-zz\nstep: build\n---\n")
            calls.clear()
            assert omi.run.run_role("omi-agent-engineer", wt, task) == 0
            assert "omi-skill-zz" in prompt() and "\nTests: python3 " in prompt(), prompt()
            assert task.read_text().splitlines()[-1].endswith("| 0/1 | - |"), task.read_text()  # Usage `skills read` cell
            # scope sync runs before `before` is read: the development scope (stub: src/**) is what the agent's task file keeps
            task.write_text("---\nid: TASK-001\nscope: docs/**\nworkflow: omi-flow-zz\nstep: build\n---\n")
            assert omi.run.run_role("omi-agent-engineer", wt, task) == 0
            assert "scope: src/**" in task.read_text() and "SCOPE SYNCED: src/**" in out.getvalue()
            task.write_text("---\nid: TASK-001\nworkflow: omi-flow-zz\nstep: review\n---\n")  # step role differs
            calls.clear()
            omi.run.run_role("omi-agent-engineer", wt, task)
            assert "omi-skill-zz" not in prompt()
            assert "WARNING: step review of TASK-001 is for omi-agent-reviewer" in out.getvalue()
            assert "omi step TASK-001 done` / `next`" in out.getvalue()
            # the task's own skills go to write roles only
            task.write_text("---\nid: TASK-001\nskills: [omi-skill-zz]\n---\n")
            calls.clear()
            omi.run.run_role("omi-agent-engineer", wt, task)
            assert "omi-skill-zz" in prompt()
            assert go() == 0, out.getvalue()
            assert "omi-skill-zz" not in prompt() and task.read_text().splitlines()[-1].endswith("| - | n/a |"), task.read_text()
        finally:
            sys.stdout = saved
            subprocess.run, shutil.which, omi.core.main_checkout, omi.core.WINDOWS, tok = real
            os.environ.pop(omi.creds.TOKEN_ENV, None)
            if tok is not None:
                os.environ[omi.creds.TOKEN_ENV] = tok


def test_incremental_review():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve()
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        (root / "a.py").write_text("x = 1\n", encoding="utf-8")
        git(root, "add", "a.py")
        git(root, "commit", "-q", "-m", "init")
        base = omi.core.git(root, "rev-parse", "HEAD")
        for i in range(30):
            (root / f"big{i}.py").write_text("".join(f"line {j}\n" for j in range(80)), encoding="utf-8")
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "work")
        sha = omi.core.git(root, "rev-parse", "--short=7", "HEAD")
        (root / "a.py").write_text("x = 2\n", encoding="utf-8")
        (root / "new.py").write_text("y = 1\n", encoding="utf-8")  # untracked fix
        index = (root / ".git" / "index").read_bytes()
        full, inc = omi.run.tree_diff(root, base), omi.run.tree_diff(root, sha)
        assert (root / ".git" / "index").read_bytes() == index, "real index must not change"
        assert "new.py" in full and "new.py" in inc and "big3.py" in full and "big3.py" not in inc
        f, i = -(-len(full.encode()) // 4), -(-len(inc.encode()) // 4)
        print(f"incremental review: full {f} tokens, incremental {i} tokens")
        assert i < f
    rows = "| omi-agent-reviewer | m | e | 1 | 1 | 1 | 1s | - | FAIL abc1234 |\n"
    text = "## Checkpoint\n### Review round 1\n- old.py:3 bad\n- src/b.py wrong\n\n## Usage\n|---|\n" + rows
    assert omi.tasks.prior_review(text) == (1, "abc1234", {"old.py", "src/b.py"})
    noisy = text.replace("- src/b.py wrong", "- e.g src/b.py wrong, 1.5 v2.0 x.py:7")
    assert omi.tasks.prior_review(noisy)[2] == {"old.py", "src/b.py", "x.py"}
    assert omi.tasks.prior_review(text + rows)[0] == 2
    assert omi.tasks.prior_review(text.replace("FAIL", "PASS"))[1] is None
    quota = "| omi-agent-reviewer | m | e | 1 | 1 | 1 | 1s | - | QUOTA->codex |\n"
    assert omi.tasks.prior_review(text + quota)[0] == 1
    assert omi.tasks.usage_totals("\n## Usage\n|---|\n" + rows + quota).endswith("review rounds: 1")
    assert omi.tools.resolve_effort("max", "codex") == "max" and omi.tools.resolve_effort("xhigh", "codex") == "xhigh"
    assert omi.tasks.prior_review("## Usage\n|---|\n| r | m | e | 1 | 1 | 1 | 1s | - | FAIL |\n") == (0, None, set())


def test_review_round_flow():
    real = subprocess.run, shutil.which, omi.core.main_checkout, os.environ.get(omi.creds.TOKEN_ENV)
    seen = {}

    class R:
        def __init__(s, out="", rc=0): s.stdout, s.returncode, s.stderr = out, rc, ""

    def run(cmd, **kw):
        if "--git-common-dir" in cmd:
            return R(str(Path(cmd[2]) / "shared.git"))
        if cmd[:2] == ["docker", "run"]:
            m = next(a.rsplit(":", 2)[0] for a in cmd if a.endswith(":/review:ro"))
            seen["files"] = sorted(p.name for p in Path(m).iterdir())
            seen["prompt"] = cmd[cmd.index("claude") + 2]
            return R(json.dumps({"result": "VERDICT: FAIL", "usage": {"input_tokens": 1}}))
        if "rev-parse" in cmd:
            return R("abc1234\n")
        if "ls-files" in cmd:
            return R("")
        if "diff" in cmd and "--name-only" in cmd:
            return R("src/a.py\0")
        if "diff" in cmd:
            return R("diff --git a/src/a.py b/src/a.py\n" if cmd[-1] != "." and "abc1234" in cmd else "full\n")
        if "status" in cmd:
            return R(" M src/a.py\0")
        if "show" in cmd:
            return R("---\nscope: src/**\n---\n")
        if cmd[0] == sys.executable:
            return R("ok")
        return R()

    with tempfile.TemporaryDirectory() as d:
        wt = Path(d).resolve()
        (wt / ".git").write_text("gitdir: /x")
        task = wt / ".omi" / "tasks" / "TASK-001.md"
        task.parent.mkdir(parents=True)
        task.write_text("---\nid: TASK-001\nscope: src/**\n---\n## Checkpoint\n### Review round 1\n- src/a.py bad\n", encoding="utf-8")
        subprocess.run, shutil.which, omi.core.main_checkout = run, lambda _: "docker", (lambda _: wt)
        os.environ[omi.creds.TOKEN_ENV] = "tok"
        sys.stdout, saved = io.StringIO(), sys.stdout
        try:
            omi.run.run_role("omi-agent-reviewer", wt, task)  # round 1: full diff, records the sha
            assert seen["files"] == ["diff.patch"] and "Incremental" not in seen["prompt"]
            assert task.read_text().splitlines()[-1].endswith("| FAIL abc1234 |"), task.read_text()
            omi.run.run_role("omi-agent-reviewer", wt, task)  # round 2: only the fixes
            assert seen["files"] == ["diff.patch", "full.patch"] and "Incremental round" in seen["prompt"]
            omi.run.run_role("omi-agent-reviewer", wt, task)  # round 3: full again
            assert seen["files"] == ["diff.patch"] and "Incremental" not in seen["prompt"]
            # usage but no result: the raw output is printed, never None
            run_raw = json.dumps({"usage": {"input_tokens": 1, "output_tokens": 2}})
            subprocess.run = lambda cmd, **kw: R(run_raw) if cmd[:2] == ["docker", "run"] else run(cmd, **kw)
            sys.stdout = io.StringIO()
            omi.run.run_role("omi-agent-engineer", wt, task)
            printed = sys.stdout.getvalue()
            # no env token: the host session login is used, and only its access token goes in
            cred = Path(os.environ["CLAUDE_CONFIG_DIR"]) / ".credentials.json"
            cred.write_text(json.dumps({"claudeAiOauth": {"accessToken": "sess-tok", "refreshToken": "REAL-REFRESH",
                                                          "expiresAt": int((time.time() + 3600) * 1000)}}))
            os.environ.pop(omi.creds.TOKEN_ENV, None)
            sys.stdout = io.StringIO()
            omi.run.run_role("omi-agent-engineer", wt, task)
            session_printed = sys.stdout.getvalue()
            cred.unlink()
        finally:
            sys.stdout = saved
            subprocess.run, shutil.which, omi.core.main_checkout, tok = real
            os.environ.pop(omi.creds.TOKEN_ENV, None)
            if tok is not None:
                os.environ[omi.creds.TOKEN_ENV] = tok
        assert printed.strip() == "claude auth: env\ntool: claude (claude-sonnet-5-5)\n" + run_raw, printed
        assert session_printed.strip() == "claude auth: session\ntool: claude (claude-sonnet-5-5)\n" + run_raw, session_printed
        assert "sess-tok" not in session_printed and "REAL-REFRESH" not in session_printed


def test_host_only_criteria():
    root = Path(__file__).parents[1]
    pairs = [(".omi/agents/omi-agent-reviewer.md", "src/omi/template/dot-omi/agents/omi-agent-reviewer.md"),
             (".claude/skills/omi-task/SKILL.md", "src/omi/template/dot-claude/skills/omi-task/SKILL.md")]
    for repo_copy, template_copy in pairs:
        text = (root / repo_copy).read_text(encoding="utf-8")
        assert text == (root / template_copy).read_text(encoding="utf-8")
        if "reviewer" in repo_copy:
            assert "`HOST <criterion>`" in text and "UNVERIFIED|HOST" in text and "is `UNVERIFIED`" in text
        else:
            assert "Host: <command> -> <result>" in text and "no merge without one `Host:` line" in text


def main():
    test_host_only_criteria()
    test_windows_test_shell()
    test_hooks()
    test_run_read_role()
    test_incremental_review()
    test_review_round_flow()


if __name__ == "__main__":
    main()
