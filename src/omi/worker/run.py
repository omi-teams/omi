"""omi run and omi worker: deterministic checks, test command, the agent run with quota fallback."""

import datetime
import importlib.util
import io
import json
import os
import posixpath
import re
import secrets
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import types
from pathlib import Path

from ..project import catalogs, scope, tasks, workflows
from ..common import core
from . import creds, docker, hooks, pr, session, tools
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


def test_command(wt, main):
    """`test` from .omi/config.json, else tests/test_omi.py if present, else pytest if importable, else each tests/test_*.py as a script."""
    cfg = Path(main) / ".omi" / "config.json"
    cmd = (json.loads(cfg.read_text(encoding="utf-8")) if cfg.exists() else {}).get("test")
    if cmd:  # through a shell, like in the containers, so `VAR=1 cmd` works
        if core.WINDOWS:
            bash = host_bash()
            return [bash, "-c", cmd] if bash else f'cmd /d /s /c "{cmd}"'
        return ["bash", "-c", cmd] if shutil.which("bash") else ["sh", "-c", cmd]
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
        r = subprocess.run([sys.executable, "-m", "omi", "workflows", "--check"], cwd=wt, capture_output=True, encoding="utf-8", errors="replace")
        if r.returncode:
            problems.append("workflows --check: " + (r.stdout + r.stderr).strip())
    try:
        r = subprocess.run(test_command(wt, main), cwd=wt, capture_output=True, encoding="utf-8", errors="replace")
    except OSError as e:
        problems.append(f"test command failed to start: {e}")
    else:
        if r.returncode in (127, 9009):  # shell: command not found (sh/bash, cmd)
            last = (r.stderr.strip().splitlines() or [f"exit {r.returncode}"])[-1]
            problems.append(f"test command failed to start: {last}")
        elif r.returncode:
            problems.append("tests failed:\n" + "\n".join((r.stdout + r.stderr).strip().splitlines()[-20:]))
    return problems


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
    catalogs.get_role(main, tm.get("role") or "omi-agent-engineer")  # unknown task role fails too
    steps = workflows.get_workflow(catalog, tm.get("workflow") or workflows.DEFAULT_WORKFLOW) \
        if tm.get("step") or tm.get("step_settings") else []
    settings = parse_step_settings(tm.get("step_settings", ""), [s["id"] for s in steps])
    cur = next((s for s in steps if s["id"] == tm.get("step")), None)
    step_settings = settings.get(cur["id"], {}) if cur and cur["role"] == role else {}
    task_settings = am["access"] == "write" or role == tm.get("role")  # other read roles keep their own settings
    tool = tool or step_settings.get("tool") or (tm.get("tool") if task_settings else None) or am.get("tool") or "claude"
    if tool not in ("claude", "codex"):
        sys.exit(f"unknown tool `{tool}`: claude or codex. Nothing changed.")
    other = "codex" if tool == "claude" else "claude"
    docker.need_docker()  # read roles too: no host fallback
    secret = creds.claude_auth() if tool == "claude" else creds.tool_secret(tool)
    if not secret[1]:
        if tool == "codex":
            sys.exit(f"no codex credentials: run `omi token set --tool codex` (Windows) or set {creds.CODEX_ENV}, "
                     f"or use your ChatGPT login ({secret[2]}). Nothing changed.")
        sys.exit(f"no token: run `omi token set` (Windows), set {creds.TOKEN_ENV}, or log in to Claude Code on the host"
                 f"{f' ({secret[2]})' if secret[2] else ''}. Nothing changed.")
    tasks.sync_scope(wt, task, task.stem)  # before `before`, so revert_front keeps the synced scope
    before = task.read_text(encoding="utf-8") if task.exists() else ""
    if cur and cur["role"] != role:
        print(f"WARNING: step {cur['id']} of {task.stem} is for {cur['role']}, not {role}; "
              f"if that step is finished run `omi step {task.stem} done` / `next` first")
    step_ids = catalogs.task_skills(cur) if cur and cur["role"] == role else []  # the current step's own skills
    own_ids = catalogs.task_skills(tm) if am["access"] == "write" else []  # task skills are for the implementer
    ids = list(dict.fromkeys([*catalogs.task_skills(am), *own_ids, *step_ids]))
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
    if read:
        problems = deterministic_checks(wt, main, task.stem)
        if problems:
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
        prompt_skills = prompt_skills.replace("/work/", "/state/")
        prompt_skills += ("\nDetached state: /state is read-only. Do not edit the task or catalogs. "
                          "Include checkpoint updates in your final report; the Coordinator records them.")
    prompt_skills += "\nTests: " + test_prompt_line(wt, main)
    text = am["_text"]
    if project.detached:
        text += ("\nFor this detached run, replace instructions to edit the task or its Checkpoint "
                 "with reporting those updates in your final response. /state is read-only.")
    tmp = tempfile.TemporaryDirectory() if read else None

    repo = docker.repo_key(main)

    def attempt(t, secret, note="", resume=None, hook_tail=None):
        """One container run with tool t (resume: continue that session id); returns (process, report text, skills read)."""
        env = dict(os.environ)
        env.pop(creds.TOKEN_ENV, None)
        env_name, value, _ = secret
        env[env_name] = value
        mdl, eff = models[t], efforts[t]
        cmd = (tools.engineer_cmd if t == "claude" else tools.codex_cmd)(text, task_rel, mdl, eff, prompt_skills + note, resume, hook_tail)
        if not read:  # the CLI's transcripts go to the per-task cache so a fix round can resume them
            cmd = session.wrap(t, cmd)
        chatgpt = env_name == creds.CODEX_AUTH_ENV
        if chatgpt:
            cmd = ["sh", "-c", creds.CODEX_AUTH_BOOT, "sh", *cmd]
        sess = [] if read else session.mount_args(repo, task.stem, t, image, fresh=resume is None)  # a fresh session gets a new volume
        t0 = time.monotonic()

        def run_once(name):
            with docker.egress(main, name, image, docker.allow_for(main, t, chatgpt=chatgpt)) as (net, proxy):
                with subprocess.Popen(docker.worker_argv(wt, image, cmd, name, repo,
                                                  {**docker.worker_labels(role, task.stem, mdl, eff), **docker.compose_labels(name, "agent")}, ro=read,
                                                  mounts=mounts, extra=sess, env_names=(env_name,), network=net, proxy=proxy,
                                                  **docker.worker_sizes(main)),
                                      env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      encoding="utf-8", errors="replace") as p:
                    err = []

                    def pump():  # echo the agent's stderr live, keep a copy for the name-conflict check
                        for line in p.stderr:
                            err.append(line)
                            sys.stderr.write(line)
                            sys.stderr.flush()

                    th = threading.Thread(target=pump, daemon=True)
                    th.start()
                    out = p.stdout.read()
                    p.wait()
                    th.join()
                r = types.SimpleNamespace(stdout=out, stderr="".join(err), returncode=p.returncode)
            if r.returncode and docker.name_taken(r.stderr, name):
                raise docker.NameTaken(name)
            return r

        try:
            for salt in ("", secrets.token_hex(1)):  # a name in use: one retry with a random 2-char suffix
                try:
                    r = run_once(docker.container_name(docker.repo_label(main), role, task.stem, t, mdl, eff, salt=salt))
                    break
                except docker.NameTaken:
                    continue
            else:
                sys.exit(f"container name in use again for {role} ({t}). Nothing changed.")
        finally:  # Ctrl-C, a container error and the exit above included: no token may stay in the session volume
            dropped = not read and session.scrub(repo, task.stem, t, image, value)
            if dropped and task.exists():  # token in a transcript: forget the session, next run is fresh
                task.write_text(session.LINE.sub("", task.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
        result, *nums = tools.parse_usage(t, r.stdout)
        done = skills_read(catalog, ids, tools.opened_files(t, r.stdout))
        verdict = (tools.verdict_of(result) or "n/a") if read else "-"
        head = core.git(wt, "rev-parse", "--short=7", "HEAD") if read and verdict != "n/a" else None
        if head:
            verdict += " " + head
        if tools.quota_hit(t, r.stdout, r.returncode):
            verdict = f"QUOTA->{'codex' if t == 'claude' else 'claude'}"
        if not read and not dropped and (sid := session.session_id(t, r.stdout)) and task.exists():
            task.write_text(session.with_session(task.read_text(encoding="utf-8"), t, sid, role), encoding="utf-8", newline="\n")
        tasks.record_usage(task, role, models[t] + (" (codex)" if t == "codex" else ""), efforts[t], nums,
                     time.monotonic() - t0, skills_cell(ids, done), verdict)
        return r, result, done

    def stop_quota(why):
        line = f"QUOTA: {why}; nothing discarded, the partial diff stays in {wt}. Resume: omi-task {task.stem}"
        tasks.append_note(task, "Checkpoint", line)
        print(line)
        return 5

    hook_failed = False
    try:
        if read:
            base = core.git(wt, "merge-base", "development", "HEAD") or "development"
            full = tree_diff(wt, base)
            rounds, sha, named = tasks.prior_review(task.read_text(encoding="utf-8") if task.exists() else "")
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
        sid = None if read or fresh else session.recorded(before, tool, role)  # another tool or role starts fresh
        if sid and not session.available(repo, task.stem, tool, sid):
            print(f"RESUME FAILED: session {sid} has no session volume; starting a fresh session")
            sid = None
        r, result, done = attempt(tool, secret, resume=sid)
        if sid and r.returncode and result is None and not tools.quota_hit(tool, r.stdout, r.returncode):
            print(f"RESUME FAILED: session {sid} could not be resumed; starting a fresh session")
            r, result, done = attempt(tool, secret)
        if tools.quota_hit(tool, r.stdout, r.returncode):
            other_secret, problem = (creds.claude_auth() if other == "claude" else creds.tool_secret(other)), None
            try:
                efforts[other] = tools.resolve_effort(want, other)
                try:
                    models[other] = tools.resolve_model(main, want_model, other)
                except SystemExit:
                    # A full ID is specific to one tool; use the role alias on a switch.
                    if not re.fullmatch(tools.CODEX_ID if tool == "codex" else r"claude-[a-zA-Z0-9_.-]+", want_model):
                        raise
                    models[other] = tools.resolve_model(main, am.get("model"), other)
            except SystemExit as exc:
                problem = str(exc)
            if not problem and not other_secret[1]:
                problem = other_secret[2] or f"no {other} token"
            if problem:
                return stop_quota(f"{tool} hit its usage limit and {other} cannot continue ({problem})")
            tasks.append_note(task, "Checkpoint", f"QUOTA: {tool} hit its usage limit; {role} continued with {other} on the partial diff.")
            print(f"QUOTA: {tool} hit its usage limit; rerunning {role} with {other} ({models[other]})")
            r, result, done = attempt(other, other_secret,
                                      f"\nNote: a previous run with {tool} stopped on its usage limit; "
                                      "a partial diff already exists in /work. Inspect it and continue, do not start over.")
            tool, secret = other, other_secret
            if tools.quota_hit(other, r.stdout, r.returncode):
                return stop_quota("claude and codex both hit their usage limit")
        rc = r.returncode
        print(result if result is not None else (r.stdout or ""))
        report = result or "(no report)"
        if rc:  # not a usage limit (handled above): show why the CLI failed
            report += "".join(f"\nERROR: {' '.join(t.split())}" for t in tools.error_texts(tool, r.stdout) if t.strip()) + f"\nexit code {rc}"
            print(report.partition(result or "(no report)")[2].strip())
        tasks.append_note(task, "Reports", f"{datetime.datetime.now():%Y-%m-%d %H:%M} {role} ({tool}):\n" + "\n".join("> " + l for l in tasks.clip_report(report)))
        verdict = (tools.verdict_of(result) or "n/a") if read else (m.group(1) if (m := re.match(r"\W*(DONE|BLOCKED|NEEDS SCOPE)\b", report)) else f"exit {rc}")
        pr.post_report(wt, task.stem, cur["id"] if cur else "-", role, tool, models[tool], efforts[tool], verdict, report)
        for sid in ids:
            if sid not in done:
                print(f"SKILL NOT READ: {sid}")
        res = hooks.run_hook(wt, main, "post-run", task.stem, image) if not rc and not read else None
        if res and res[0] and (sid := session.recorded(task.read_text(encoding="utf-8"), tool, role)) \
                and session.available(repo, task.stem, tool, sid):  # one retry: the engineer fixes what the hook found
            print("post-run hook failed; resuming the engineer once to fix it")
            if (fix := attempt(tool, secret, resume=sid, hook_tail="\n".join(res[1].strip().splitlines()[-20:])))[0].returncode:
                print(f"hook-fix attempt exited with code {fix[0].returncode}")
            res = hooks.run_hook(wt, main, "post-run", task.stem, image)
        if res:
            pr.post_hook(wt, task.stem, "post-run", res)
            if hooks.hook_note(task, "post-run", res):
                hook_failed = True
    finally:
        if tmp:
            tmp.cleanup()
        if not read:
            for key in tasks.revert_front(task, before):
                print(f"REVERTED: {key}")
    if hook_failed:
        print("post-run hook failed: the task cannot move to review")
    if read:
        return rc or (6 if hook_failed else 0)
    bad = scope.out_of_scope(wt, task.stem)
    for p in bad:
        print(f"OUT OF SCOPE: {p}")
    if scope.git_hint(bad):
        print(scope.git_hint(bad))
    return rc or (3 if bad else 0) or (6 if hook_failed else 0)


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
    for salt in ("", secrets.token_hex(1)):  # a name in use: one retry with a random 2-char suffix
        name = docker.container_name(docker.repo_label(main), "omi-agent-engineer", "prove", tm_tool, model, effort, salt=salt)
        try:
            with docker.egress(main, name, image, allow) as (net, proxy):
                r = subprocess.run(docker.worker_argv(wt, image, ["sh", "-s"], name, docker.repo_key(main),
                                               {**docker.worker_labels("prove", None, None, None), **docker.compose_labels(name, "agent")},
                                               network=net, proxy=proxy,
                                               mounts=[f"{project.state}:/state"] if project.detached else (),
                                               **docker.worker_sizes(main)), env=env,
                                   input=script.read_bytes().replace(b"\r\n", b"\n"), stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
            if r.returncode and docker.name_taken(r.stdout.decode("utf-8", "replace"), name):
                raise docker.NameTaken(name)
            break
        except docker.NameTaken:
            continue
    else:
        sys.exit("container name in use again for --prove. Nothing changed.")
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
