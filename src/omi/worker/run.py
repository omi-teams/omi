"""omi run and omi worker: deterministic checks, test command, the agent run with quota fallback."""

import datetime
import importlib.util
import io
import json
import os
import posixpath
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import types
from pathlib import Path

from ..project import catalogs, runs, scope, tasks, workflows
from ..common import core
from . import agent, budget, creds, docker, hooks, pr, session, tools
from ..state import resolve as state


def skills_read(root, ids, opened):
    """Ids of the declared skills whose SKILL.md or a declared reference is an opened path (whole path or `.../<rel>`)."""
    dirs = catalogs.skill_dirs(root)
    done = []
    for sid in ids:
        rels = [Path(f).relative_to(root).as_posix() for f in catalogs.skill_files(dirs[sid])]
        rels += [f"{dirs[sid].name}/{Path(f).relative_to(dirs[sid]).as_posix()}" for f in catalogs.skill_files(dirs[sid])]
        if any(o == r or o.endswith("/" + r) for r in rels for o in map(posixpath.normpath, filter(None, opened))):
            done.append(sid)
    return done


SCOPE_LINE = re.compile(r"^Run scope: (.*)$\n?", re.M)  # the task scope at the session's last run, under `## Checkpoint`


def widened_scope(text, now):
    """Scope entries in `now` that the session's previous run did not have; all of `now` for a legacy session without a record."""
    m = SCOPE_LINE.search(text or "")
    return [g for g in now if g not in core.split(m[1])] if m else list(now)


def record_scope(task, now):
    task.write_text(SCOPE_LINE.sub("", core.read_task(task)), encoding="utf-8", newline="\n")
    tasks.append_note(task, "Checkpoint", "Run scope: " + ", ".join(now))


def container_paths(text, detached):
    """Prompt text with `/work/` catalog paths pointing at the read-only `/state` mount of a detached project."""
    return text.replace("/work/", "/state/") if detached else text


def skills_cell(ids, done):
    return f"{len(done)}/{len(ids)} {' '.join(done)}".strip() if ids else "-"


def tree_diff(wt, since, exclude=None):
    """`git diff <since>` of the worktree including untracked files; the real index is not touched."""
    with tempfile.TemporaryDirectory() as d:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(d) / "index")}
        run = lambda *a, **kw: subprocess.run(["git", "-C", str(wt), *a], env=env, capture_output=True,  # noqa: E731
                                              encoding="utf-8", errors="replace", **kw)
        if run("read-tree", "HEAD").returncode == 0:
            new = run("ls-files", "--others", "--exclude-standard", "-z").stdout or ""
            if new:
                run("add", "-N", "--pathspec-from-file=-", "--pathspec-file-nul", input=new)
        return run("diff", since, *(["--", ".", f":(exclude){exclude}"] if exclude else [])).stdout or ""


def ensure_cache_excluded(wt: Path) -> None:
    """Ignore download caches across all worktrees without changing tracked files."""
    common = core.git(wt, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if not common:
        sys.exit(f"cannot find the shared git directory for {wt}")
    exclude = Path(common) / "info" / "exclude"
    existing = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
    if ".omi-cache/" not in existing.splitlines():
        exclude.parent.mkdir(parents=True, exist_ok=True)
        with exclude.open("a", encoding="utf-8", newline="\n") as f:
            f.write(("\n" if existing and not existing.endswith("\n") else "") + ".omi-cache/\n")


def host_bash():
    """Path of a bash that runs on this host, or None. On Windows: not the WSL aliases, also Git Bash when only Git\\cmd is on PATH."""
    if not core.WINDOWS:
        return shutil.which("bash")
    # The bash.exe in System32 and WindowsApps are WSL aliases, not the host's Git Bash.
    path = os.pathsep.join(p for p in os.get_exec_path() if posixpath.basename(
        p.replace("\\", "/").rstrip("/")).lower() not in ("system32", "windowsapps"))
    bash = shutil.which("bash", path=path)
    git = None if bash else shutil.which("git", path=path)  # Git\cmd on PATH, Git\bin not
    if git and (git_bash := Path(git).parent.parent / "bin" / "bash.exe").is_file():
        bash = str(git_bash)
    return bash


def shell_command(cmd):
    """`cmd` through a shell, like in the containers, so `VAR=1 cmd` works."""
    if core.WINDOWS:
        bash = host_bash()
        return [bash, "-c", cmd] if bash else f'cmd /d /s /c "{cmd}"'
    return ["bash", "-c", cmd] if shutil.which("bash") else ["sh", "-c", cmd]


def test_command(wt, main):
    """`test` from .omi/config.json, else tests/test_omi.py if present, else pytest if importable, else each tests/test_*.py as a script."""
    cfg = Path(main) / ".omi" / "config.json"
    cmd = (json.loads(cfg.read_text(encoding="utf-8")) if cfg.exists() else {}).get("test")
    if cmd:
        return shell_command(cmd)
    if (Path(wt) / "tests" / "test_omi.py").exists():
        argv = ["python", "tests/test_omi.py"]
    elif importlib.util.find_spec("pytest"):
        argv = ["python", "-m", "pytest", "-q"]
    else:
        argv = ["python", "-c", "import glob,subprocess,sys;codes=[subprocess.call([sys.executable,f]) "
                                "for f in sorted(glob.glob('tests/test_*.py'))];sys.exit(1 if any(codes) else 0)"]
    return [sys.executable if argv[0] == "python" else argv[0], *argv[1:]]


def test_prompt_line(wt, main):
    """The `Tests:` line of the agent prompt: shell-quoted so it parses back to the same argv."""
    argv = test_command(wt, main)
    if isinstance(argv, str):
        return argv.removeprefix('cmd /d /s /c "')[:-1]
    shell = posixpath.basename(argv[0].replace("\\", "/")).lower().removesuffix(".exe")
    return argv[2] if shell in ("bash", "sh", "cmd") and argv[1] in ("-c", "/c") else \
        shlex.join("python3" if a == sys.executable else a for a in argv)


def test_text(wt, main):
    """The `test` command text for the worker image: config `test`, else the default test script or pytest."""
    cfg = Path(main) / ".omi" / "config.json"
    return (json.loads(cfg.read_text(encoding="utf-8")) if cfg.exists() else {}).get("test") or \
        ("python3 tests/test_omi.py" if (Path(wt) / "tests" / "test_omi.py").exists() else "python3 -m pytest -q")


def clean_head(wt, tid):
    """Short HEAD of the worktree when it has no changes besides the task file, else None."""
    dirty = core.git(wt, "status", "--porcelain", "--", ".", f":(exclude).omi/tasks/{tid}.md")
    return None if dirty != "" else core.git(wt, "rev-parse", "--short=7", "HEAD")


def reused_hook(wt, main, tid):
    """`reused: hook post-run on X` when worker mode is on and the post-run hook passed on the worktree's clean HEAD X, else None."""
    if not hooks.review_test_in_worker(main):
        return None
    project = state.resolve(wt)
    task = state.task_file(project, tid)
    sha = clean_head(wt, tid)
    if task.exists() and hooks.hook_passed_on(core.read_task(task), sha):
        tasks.append_note(task, "Reports", f"{datetime.datetime.now():%Y-%m-%d %H:%M} reused: hook post-run on {sha}")
        return f"reused: hook post-run on {sha}"
    return None


def deterministic_checks(wt, main, tid):
    """Problems a script can find in the diff before a read role is started (empty = start the role)."""
    catalog = state.catalog_root(state.resolve(wt), wt)
    problems = []
    bad = scope.out_of_scope(wt, tid, committed=True)
    if bad:
        problems.append("scope check: outside scope: " + ", ".join(bad) + (f"\n{scope.git_hint(bad)}" if scope.git_hint(bad) else ""))
    saved, sys.stdout = sys.stdout, io.StringIO()
    try:
        catalogs.check_all_skills(catalog)
    except SystemExit as e:
        problems.append(f"skills --check: {e}")
    finally:
        sys.stdout = saved
    if (catalog / ".omi" / "workflows").is_dir():
        r = subprocess.run([sys.executable, "-m", "omi", "workflows", "--check"], cwd=wt, capture_output=True, encoding="utf-8", errors="replace",
                           stdin=subprocess.DEVNULL)
        if r.returncode:
            problems.append("workflows --check: " + (r.stdout + r.stderr).strip())
    problems.extend(agent.cmd_shims(wt))
    if note := reused_hook(wt, main, tid):
        print(note)
        return problems
    try:
        if hooks.review_test_in_worker(main):
            code, out = hooks.run_test(wt, main, "OMI_QUIET=1 " + test_text(wt, main), tid, None)
            r = types.SimpleNamespace(returncode=code, stdout=out, stderr="")
        else:
            r = subprocess.run(test_command(wt, main), cwd=wt, capture_output=True, encoding="utf-8", errors="replace",
                               stdin=subprocess.DEVNULL, env={**os.environ, "OMI_QUIET": "1"})  # tests/test_omi.py: failures and a summary only
    except (OSError, SystemExit) as e:
        problems.append(f"test command failed to start: {e}")
    else:
        if r.returncode in (127, 9009):  # shell: command not found (sh/bash, cmd)
            last = (r.stderr.strip().splitlines() or [f"exit {r.returncode}"])[-1]
            problems.append(f"test command failed to start: {last}")
        elif r.returncode:
            problems.append("tests failed:\n" + "\n".join((r.stdout + r.stderr).strip().splitlines()[-20:]))
    return problems


def host_test(project, tid):
    """`omi host-test <ID>`: run `host_test` on the host in the task's worktree and record a `host-test` row in `## Usage`.
    Returns the exit code: 0 on pass or when `host_test` is empty."""
    cmd = tasks.host_test_command(project.state)
    if not cmd:
        print("host_test is empty in .omi/config.json: skipped")
        return 0
    wt = core.task_worktrees(project.code).get(tid)
    if not wt:
        sys.exit(f"no worktree for {tid}: create it first (git worktree add). Nothing changed.")
    dirty = core.git(wt, "status", "--porcelain", "--", ".", f":(exclude).omi/tasks/{tid}.md")  # the task file gets this run's row
    if dirty is None:
        sys.exit(f"cannot read the git status of {tid}'s worktree. Nothing changed.")
    if dirty:
        sys.exit(f"{tid} worktree has uncommitted changes: commit first, so the result covers HEAD. Nothing changed.")
    if note := reused_hook(wt, project.state, tid):
        tasks.record_usage(state.task_file(project, tid), "host-test", "-", None, (None, None, None), 0,
                           "-", f"PASS {core.git(wt, 'rev-parse', '--short=7', 'HEAD')}")
        print(f"HOST TEST PASSED ({note})")
        return 0
    t0 = time.monotonic()
    try:
        r = subprocess.run(shell_command(cmd), cwd=wt, capture_output=True, encoding="utf-8", errors="replace")
        code, out = r.returncode, r.stdout + r.stderr
    except OSError as e:
        code, out = 1, f"host test failed to start: {e}"
    sha = core.git(wt, "rev-parse", "--short=7", "HEAD") or "unknown"
    tasks.record_usage(state.task_file(project, tid), "host-test", "-", None, (None, None, None), time.monotonic() - t0,
                       "-", f"{'FAIL' if code else 'PASS'} {sha}")
    if code:
        print("HOST TEST FAILED\n" + "\n".join(out.strip().splitlines()[-20:]))
        return 1
    print(f"HOST TEST PASSED {sha}")
    return 0


def parse_step_settings(value: str, step_ids: list[str] | None = None) -> dict[str, dict[str, str]]:
    """Parse per-step tool/model/effort overrides, allowing empty parts."""
    settings = {}
    if not value.strip():
        return settings
    for entry in value.split(","):
        match = re.fullmatch(r"\s*([a-z0-9][a-z0-9-]*)=([^/=,\s]*)/([^/=,\s]*)/([^/=,\s]*)\s*", entry)
        if not match or match[1] in settings:
            sys.exit(f"invalid step_settings entry `{entry.strip()}`: expected <step>=<tool>/<model>/<effort>, ... "
                     "(parts may be empty). Nothing changed.")
        if step_ids is not None and match[1] not in step_ids:
            sys.exit(f"unknown step_settings step `{match[1]}`: workflow step ids are "
                     f"{', '.join(step_ids)}. Nothing changed.")
        settings[match[1]] = dict(zip(("tool", "model", "effort"), match.groups()[1:]))
    return settings


def missing_lines(report, step_id):
    """Lines a DONE write report still needs before advance can use it: `Suggested commit:`, and `Reproduced:` on a reproduce step."""
    if not report or not re.match(r"\W*DONE\b", report):  # the same verdict test as the run record below
        return []
    need = [tools.COMMIT_KEY] + ([tools.REPRODUCED_KEY] if step_id in tools.REPRODUCE_STEPS else [])
    return [k for k in need if not tools.report_values(report, k)]


def report_note(task: Path, role: str, tool: str, report: str) -> None:
    """Append an agent report to ## Reports in full: the next step reads it from there."""
    tasks.append_note(task, "Reports", f"{datetime.datetime.now():%Y-%m-%d %H:%M} {role} ({tool}):\n" + "\n".join("> " + l for l in report.splitlines()))


MODULE_TESTS = ("Run only the tests of the modules you changed (OMI_QUIET=1 prints only failures); the full suite above runs once "
                "in the post-run hook after you finish, so do not run it yourself.")


def run_role(role, wt, task_file, model=None, effort=None, tool=None, fresh=False):
    wt = Path(wt).resolve()
    main = core.main_checkout(wt)
    if not main or not (wt / ".git").is_file():
        sys.exit(f"{wt} is not a git worktree. Nothing changed.")
    project = state.resolve(wt)
    main = project.state if project.detached else main
    catalog = state.catalog_root(project, wt)
    task = Path(task_file).resolve()
    try:
        task_rel = task.relative_to(catalog).as_posix()
    except ValueError:
        sys.exit(f"{task} is not inside {catalog}. Nothing changed.")
    tm = core.meta(task) if task.exists() else {}
    catalogs.check_task_plan(catalog, tm)
    am = catalogs.get_role(main, role)
    if role in tasks.REVIEW_ROLES:
        tasks.host_test_gate(project.state, task.stem, core.read_task(task) if task.exists() else "",
                             core.git(wt, "rev-parse", "--short=7", "HEAD"))
    catalogs.get_role(main, tm.get("role") or "omi-agent-engineer")  # unknown task role fails too
    steps = workflows.get_workflow(catalog, tm.get("workflow") or workflows.DEFAULT_WORKFLOW) \
        if tm.get("step") or tm.get("step_settings") else []
    settings = parse_step_settings(tm.get("step_settings", ""), [s["id"] for s in steps])
    cur = next((s for s in steps if s["id"] == tm.get("step")), None)
    if cur and cur["role"] != role:  # a reviewer dispatched with its stage runs as its own step
        cur = next((s for s in workflows.stage_of(steps, cur["id"]) if s["role"] == role), cur)
    step_settings = settings.get(cur["id"], {}) if cur and cur["role"] == role else {}
    task_settings = am["access"] == "write" or role == tm.get("role")  # other read roles keep their own settings
    tool = tool or step_settings.get("tool") or (tm.get("tool") if task_settings else None) or am.get("tool") or "claude"
    if tool not in ("claude", "codex"):
        sys.exit(f"unknown tool `{tool}`: claude or codex. Nothing changed.")
    if tool == "codex" and role in agent.CLAUDE_ONLY:
        sys.exit(f"{role} runs on Claude only (PO rule: the architect is never given to Codex). Nothing started.")
    other = "codex" if tool == "claude" else "claude"
    docker.need_docker()  # read roles too: no host fallback
    secret = creds.claude_auth() if tool == "claude" else creds.tool_secret(tool)
    if not secret[1]:
        if tool == "codex":
            sys.exit(f"no codex credentials: run `omi token set --tool codex` (Windows) or set {creds.CODEX_ENV}, "
                     f"or use your ChatGPT login ({secret[2]}). Nothing changed.")
        sys.exit(f"no token: run `omi token set` (Windows), set {creds.TOKEN_ENV}, or log in to Claude Code on the host"
                 f"{f' ({secret[2]})' if secret[2] else ''}. Nothing changed.")
    now_scope = scope.task_scope(wt, task.stem)
    added = widened_scope(core.read_task(task) if task.exists() else "", now_scope)  # read before sync_scope rewrites the copy
    tasks.sync_scope(wt, task, task.stem)  # before `before`, so revert_front keeps the synced scope
    before = core.read_task(task) if task.exists() else ""
    if cur and cur["role"] != role:
        print(f"WARNING: step {cur['id']} of {task.stem} is for {cur['role']}, not {role}; "
              f"if that step is finished run `omi step {task.stem} done` / `next` first")
    step_ids = catalogs.task_skills(cur) if cur and cur["role"] == role else []  # the current step's own skills
    own_ids = catalogs.task_skills(tm) if am["access"] == "write" else []  # task skills are for the implementer
    sources = runs.skill_sources(catalogs.task_skills(am), own_ids, step_ids)
    ids = list(sources)
    declared = catalogs.check_skills(catalog, ids)  # role defaults count against the budget
    rule_files = catalogs.task_rules(catalog, scope.task_scope(wt, task.stem))
    ref_files = catalogs.task_references(catalog, tm)
    want = effort or step_settings.get("effort") or (tm.get("effort") if task_settings else None) or am.get("effort")
    efforts = {tool: tools.resolve_effort(want, tool)}
    want_model = model or step_settings.get("model") or (tm.get("model") if task_settings else None) or am.get("model")
    models = {tool: tools.resolve_model(main, want_model, tool)}

    ensure_cache_excluded(wt)
    read = am["access"] == "read"
    mounts = [f"{project.state}:/state"] if project.detached else []
    problems = deterministic_checks(wt, main, task.stem) if read else []
    if problems and role in (*tasks.REVIEW_ROLES, "omi-agent-qa-tester"):  # other read roles (architect) are consulted when checks fail
        print(f"{role} not started; fix these first:\n" + "\n".join(problems))
        return 4
    image = docker.ensure_image(main)
    res = None if read else hooks.run_hook(wt, main, "pre-run", task.stem, image)  # hooks guard write roles only
    if res:
        pr.post_hook(wt, task.stem, "pre-run", res)
    if res and hooks.hook_note(task, "pre-run", res):
        print("pre-run hook failed; the agent was not started")
        return 6
    prompt_skills = catalogs.skill_prompt(catalog, declared) + catalogs.rule_prompt(catalog, rule_files) + catalogs.reference_prompt(catalog, ref_files)
    if project.detached:
        task_rel = "/state/" + task_rel
        prompt_skills = container_paths(prompt_skills, True)
        prompt_skills += ("\nDetached state: /state is read-only. Do not edit the task or catalogs. "
                          "Include checkpoint updates in your final report; the Coordinator records them.")
    resume_skills = container_paths(catalogs.skill_prompt(catalog, declared), project.detached)
    prompt_skills += "\nTests: " + test_prompt_line(wt, main) + ("" if read else "\n" + MODULE_TESTS)
    if problems:
        prompt_skills += "\nThe pre-review checks currently fail:\n" + "\n".join(problems)
    text = am["_text"]
    if project.detached:
        text += ("\nFor this detached run, replace instructions to edit the task or its Checkpoint "
                 "with reporting those updates in your final response. /state is read-only.")
    tmp = tempfile.TemporaryDirectory() if read else None
    timeout = agent.run_timeout(project, am["access"])

    repo = docker.repo_key(main)
    spent, ac = {}, {"left": role in tasks.REVIEW_ROLES}  # last attempt's input-equivalent tokens (cache at budget.CACHE_WEIGHT); one fresh rerun for missing AC lines

    def attempt(t, secret, note="", resume=None, hook_tail=None, missing=None):
        """One container run with tool t (resume: continue that session id); returns (process, report text, skills read)."""
        env = dict(os.environ)
        env.pop(creds.TOKEN_ENV, None)
        env_name, value, _ = secret
        env[env_name] = value
        mdl, eff = models[t], efforts[t]
        cmd = (tools.engineer_cmd if t == "claude" else tools.codex_cmd)(text, task_rel, mdl, eff, prompt_skills + note, resume, hook_tail, missing)
        if resume and declared:  # the resume prompt is short: point again at the step's skills so reading them is counted
            cmd[2 if t == "claude" else -1] += resume_skills + "\nRe-read them now, they are not in your context after a resume."
        if resume and added:  # the resumed session still remembers the old scope
            cmd[2 if t == "claude" else -1] += ("\nSCOPE SYNCED: the task scope was widened since your last run; these paths are now in scope: "
                                              + ", ".join(added) + ". Do not report NEEDS SCOPE for them.")
        cmd[2 if t == "claude" else -1] += budget.skeleton_prompt(before, role, am["access"], cur["id"] if cur else tm.get("step", ""))
        if not read:  # the CLI's transcripts go to the per-task cache so a fix round can resume them
            cmd = session.wrap(t, cmd)
        chatgpt = env_name == creds.CODEX_AUTH_ENV
        if chatgpt:
            cmd = ["sh", "-c", creds.CODEX_AUTH_BOOT, "sh", *cmd]
        sess = [] if read else session.mount_args(repo, task.stem, t, image, fresh=resume is None)  # a fresh session gets a new volume
        t0 = time.monotonic()

        def run_once(name):
            with docker.egress(main, name, image, docker.allow_for(main, t, chatgpt=chatgpt), task.stem) as (net, proxy):
                return agent.run_container(docker.worker_argv(
                    wt, image, cmd, name, repo, {**docker.worker_labels(role, task.stem, mdl, eff), **docker.compose_labels(name, "agent")},
                    ro=read, mounts=mounts, extra=sess, env_names=(env_name,), network=net, proxy=proxy, **docker.worker_sizes(main)),
                    env, name, timeout)

        try:
            r = agent.run_named(lambda salt: docker.container_name(docker.repo_label(main), role, task.stem, t, mdl, eff, salt=salt),
                                run_once, f"{role} ({t})")
        finally:  # Ctrl-C, a container error and the exit above included: no token may stay in the session volume
            dropped = not read and session.scrub(repo, task.stem, t, image, value)
            if dropped and task.exists():  # token in a transcript: forget the session, next run is fresh
                task.write_text(session.LINE.sub("", core.read_task(task)), encoding="utf-8", newline="\n")
        result, *nums = tools.parse_usage(t, r.stdout)
        if read:
            result = tools.full_report(t, r.stdout, result)
        done = skills_read(catalog, ids, tools.opened_files(t, r.stdout))
        seen = done  # every skill this session has read, for the Session line
        if resume and task.exists():  # skills the resumed session read earlier count too
            seen = list(dict.fromkeys([*session.skills_recorded(core.read_task(task), t, role), *done]))
            done = [sid for sid in ids if sid in seen]
        verdict = (tools.verdict_of(result) or "n/a") if read else "-"
        head = core.git(wt, "rev-parse", "--short=7", "HEAD") if read and verdict != "n/a" else None
        if head:
            verdict += " " + head
        if verdict.startswith("FAIL") and (rt := tasks.root_of(result)):
            verdict += f" root:{rt}"
        if (why := agent.failure(t, r)) == "quota":
            verdict = f"QUOTA->{'codex' if t == 'claude' else 'claude'}"
        elif why:
            verdict = "AUTH"
        elif ac["left"] and verdict[:4] in ("PASS", "FAIL") and (gap := budget.missing_ac(core.read_task(task) if task.exists() else "", result)):
            ac["gap"], verdict = gap, "AC-MISSING"  # not a verdict: the fresh rerun's row counts
        spent["input"] = budget.token_count(nums[0], nums[2], t == "codex")
        if not read and not dropped and (sid := session.session_id(t, r.stdout)) and task.exists():
            task.write_text(session.with_session(core.read_task(task), t, sid, role, seen), encoding="utf-8", newline="\n")
            record_scope(task, now_scope)
        tasks.record_usage(task, role, models[t] + (" (codex)" if t == "codex" else ""), efforts[t], nums,
                     time.monotonic() - t0, skills_cell(ids, done), verdict)
        runs.record_run(task, role, t, models[t], efforts[t], cur["id"] if cur else None, sources, done,
                        [Path(f).stem for f in rule_files], runs.ref_ids(catalog, ref_files))
        return r, result, done

    def stop(kind, t, why):
        """QUOTA (rc 5) or AUTH (rc 8) stop with one line under ## Checkpoint; AUTH also leaves an `auth` marker for watch."""
        if kind == "auth":
            line, rc = agent.auth_line(t), agent.AUTH_RC
            if os.environ.get("OMI_RUN_DIR"):
                core.write_text(Path(os.environ["OMI_RUN_DIR"]) / "auth", line)
            tasks.append_note(task, "Checkpoint", f"{line} ({why}); nothing discarded, the partial diff stays in {wt}")
        else:
            line, rc = f"QUOTA: {why}; nothing discarded, the partial diff stays in {wt}. Resume: omi-task {task.stem}", 5
            tasks.append_note(task, "Checkpoint", line)
        print(line)
        return rc

    hook_failed = False
    try:
        if read:
            base = core.git(wt, "merge-base", "development", "HEAD") or "development"
            full = tree_diff(wt, base)
            rounds, sha, named = tasks.prior_review(core.read_task(task) if task.exists() else "")
            patch, note = full, "\nDiff: /review/diff.patch (read-only; git does not work in this container)"
            if sha and rounds < 2:
                inc = tree_diff(wt, sha, None if project.detached else task_rel)
                changed = set(re.findall(r"^diff --git a/.* b/(.*)$", inc, re.M))
                if changed and changed <= named:
                    patch = inc
                    (Path(tmp.name) / "full.patch").write_text(full, encoding="utf-8", newline="\n")
                    note = ("\nDiff: /review/diff.patch (fixes since the last reviewed commit; read-only; git does not work in this container)"
                            "\nIncremental round: previous findings are under `## Checkpoint`; full diff at /review/full.patch only if needed")
            (Path(tmp.name) / "diff.patch").write_text(patch, encoding="utf-8", newline="\n")
            mounts.append(f"{tmp.name}:/review")
            prompt_skills += note
        print(f"tool: {tool} ({models[tool]})")
        sid = None if read or fresh or tool == "codex" else session.recorded(before, tool, role)  # Codex fix rounds avoid replaying the full cache
        if sid and not session.available(repo, task.stem, tool, sid):
            print(f"RESUME FAILED: session {sid} has no session volume; starting a fresh session")
            sid = None
        r, result, done = attempt(tool, secret, resume=sid)
        if sid and r.returncode and result is None and not agent.failure(tool, r):
            print(f"RESUME FAILED: session {sid} could not be resumed; starting a fresh session")
            r, result, done = attempt(tool, secret)
        if agent.failure(tool, r) == "auth" and (again := agent.fresh_secret(tool))[1]:
            print(f"AUTH: {tool} rejected the login; retrying {role} once with host credentials read fresh")
            secret = again
            r, result, done = attempt(tool, secret)
        if why := agent.failure(tool, r):
            what = "hit its usage limit" if why == "quota" else "login is invalid"
            other, other_secret = agent.other_tool(tool, role, main, want, want_model, am.get("model"), efforts, models)
            if other is None:
                return stop(why, tool, f"{tool} {what} and {other_secret}")
            tasks.append_note(task, "Checkpoint", f"{why.upper()}: {tool} {what}; {role} continued with {other} on the partial diff.")
            print(f"{why.upper()}: {tool} {what}; rerunning {role} with {other} ({models[other]})")
            r, result, done = attempt(other, other_secret, f"\nNote: a previous run with {tool} stopped on its {'usage limit' if why == 'quota' else 'login'}; "
                                      "a partial diff already exists in /work. Inspect it and continue, do not start over.")
            first, tool, secret = tool, other, other_secret
            if again := agent.failure(tool, r):
                return stop(again, tool, "claude and codex both hit their usage limit" if why == again == "quota"
                            else f"{first} {what}, then {tool} failed too")
        limit = budget.token_budget(project, role, tool=tool)
        over = bool(limit and (spent.get("input") or 0) > limit)
        if over:
            line = (f"BUDGET: {role} used {spent['input']} input-equivalent tokens (cache reads at {budget.CACHE_WEIGHT:.0%}), over its token_budget {limit}; stopped instead of continuing, "
                    f"the partial diff stays in {wt}. Resume: omi-task {task.stem}")
            tasks.append_note(task, "Checkpoint", line)
            print(line)
        rc = r.returncode
        if read and not rc and not over and ac.get("gap"):
            print(f"report has no AC: line for {len(ac['gap'])} criteria; rerunning {role} once fresh")
            ac["left"] = False
            r, result, done = attempt(tool, secret, "\nA previous review of this diff gave no `AC:` line for these criteria; review again "
                                                    "and write one `AC:` line per acceptance criterion, in task order:\n" + "\n".join("- " + g for g in ac["gap"]))
            rc = r.returncode
        if not over and not read and not rc and (missing := missing_lines(result, cur["id"] if cur else "")) \
                and (sid := session.recorded(core.read_task(task), tool, role)) and session.available(repo, task.stem, tool, sid):
            print(f"report is missing {', '.join(missing)}; resuming the engineer once to add them")
            fix = attempt(tool, secret, resume=sid, missing=missing)
            if not fix[0].returncode and fix[1] is not None:
                r, result, done = fix[0], fix[1], list(dict.fromkeys([*done, *fix[2]]))
        print(result if result is not None else (r.stdout or ""))
        report = result or "(no report)"
        if rc:  # not a usage limit (handled above): show why the CLI failed
            report += "".join(f"\nERROR: {' '.join(t.split())}" for t in tools.error_texts(tool, r.stdout) if t.strip()) + f"\nexit code {rc}"
            print(report.partition(result or "(no report)")[2].strip())
        report_note(task, role, tool, report)
        verdict = (tools.verdict_of(result) or "n/a") if read else (m.group(1) if (m := re.match(r"\W*(DONE|BLOCKED|NEEDS SCOPE)\b", report)) else f"exit {rc}")
        pr.post_report(wt, task.stem, cur["id"] if cur else "-", role, tool, models[tool], efforts[tool], verdict, report)
        for sid in ids:
            if sid not in done:
                print(f"SKILL NOT READ: {sid}")
        res = (hooks.regenerate(wt, project), hooks.run_hook(wt, main, "post-run", task.stem, image))[1] if not rc and not read and not over else None
        if res and res[0] and not agent.killed(res[0]) and (sid := session.recorded(core.read_task(task), tool, role)) \
                and session.available(repo, task.stem, tool, sid):  # one retry: the engineer fixes what the hook found
            print("post-run hook failed; resuming the engineer once to fix it")
            if (fix := attempt(tool, secret, resume=sid, hook_tail="\n".join(res[1].strip().splitlines()[-20:])))[0].returncode:
                print(f"hook-fix attempt exited with code {fix[0].returncode}")
            hooks.regenerate(wt, project)
            res = hooks.run_hook(wt, main, "post-run", task.stem, image)
        if res:
            pr.post_hook(wt, task.stem, "post-run", res)
            if hooks.hook_note(task, "post-run", res, clean_head(wt, task.stem)):
                hook_failed = True
    except agent.Timeout as exc:  # the container is gone; never resumed by the hook-fix path
        line = f"TIMEOUT: {role} {exc}; the partial diff stays in {wt}. Resume: omi-task {task.stem}"
        tasks.append_note(task, "Checkpoint", line)
        print(line)
        return agent.TIMEOUT_RC
    finally:
        if tmp:
            tmp.cleanup()
        if not read and not project.detached:  # read-only /state: the agent cannot touch it, keep Coordinator edits made meanwhile
            for key in tasks.revert_front(task, before):
                print(f"REVERTED: {key}")
    if hook_failed:
        print("post-run hook failed: the task cannot move to review")
    if read:
        return rc or (7 if over else 0) or (6 if hook_failed else 0)
    bad = scope.out_of_scope(wt, task.stem)
    for p in bad:
        print(f"OUT OF SCOPE: {p}")
    if scope.git_hint(bad):
        print(scope.git_hint(bad))
    plan_bad = scope.plan_violations(wt, task.stem)
    for line in plan_bad:
        print(line)
    return rc or (7 if over else 0) or (3 if bad or plan_bad else 0) or (6 if hook_failed else 0)


def worker(wt, task_file=None, model=None, effort=None, prove=False):
    if not prove:
        return run_role("omi-agent-engineer", wt, task_file, model, effort)
    wt = Path(wt).resolve()
    main = core.main_checkout(wt)
    if not main or not (wt / ".git").is_file():
        sys.exit(f"{wt} is not a git worktree. Nothing changed.")
    project = state.resolve(wt)
    main = project.state if project.detached else main
    docker.need_docker()
    allow = docker.allow_for(main, *docker.TOOL_API_HOST)
    image = docker.ensure_image(main)
    env = dict(os.environ)
    env.pop(creds.TOKEN_ENV, None)
    script = main / "docker" / "prove.sh"
    script = script if script.exists() else core.TEMPLATE / "docker" / "prove.sh"
    am = catalogs.get_role(main, "omi-agent-engineer")  # named like a real run: real role, tool, model, effort
    tm_tool = am.get("tool") or "claude"
    model, effort = tools.resolve_model(main, am.get("model"), tm_tool), tools.resolve_effort(am.get("effort"), tm_tool)
    def run_once(name):
        with docker.egress(main, name, image, allow) as (net, proxy):
            r = subprocess.run(docker.worker_argv(wt, image, ["sh", "-s"], name, docker.repo_key(main),
                                                  {**docker.worker_labels("prove", None, None, None), **docker.compose_labels(name, "agent")},
                                                  network=net, proxy=proxy, mounts=[f"{project.state}:/state"] if project.detached else (),
                                                  **docker.worker_sizes(main)), env=env,
                               input=script.read_bytes().replace(b"\r\n", b"\n"), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if r.returncode and docker.name_taken(r.stdout.decode("utf-8", "replace"), name):
            raise docker.NameTaken(name)
        return r

    r = agent.run_named(lambda salt: docker.container_name(docker.repo_label(main), "omi-agent-engineer", "prove", tm_tool, model, effort,
                                                           salt=salt), run_once, "--prove")
    out = r.stdout.decode("utf-8", "replace")
    print(out, end="")
    return docker.prove_rc(out, r.returncode)


def run_cmd(role, tid, rest):
    project = state.resolve(core.main_checkout(".") or Path(".").resolve())
    wt = core.task_worktrees(project.code).get(tid)
    if not wt:
        sys.exit(f"no worktree for {tid}: create it first (git worktree add). Nothing changed.")
    return run_role(role, wt, state.task_file(project, tid), core.flag(rest, "--model"), core.flag(rest, "--effort"),
                    core.flag(rest, "--tool"), "--fresh" in rest)
