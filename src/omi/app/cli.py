"""Command line: usage text, omi status and argument dispatch."""

import contextlib
import datetime
import json
import os
import re
import statistics
import sys
import webbrowser
from pathlib import Path

from ..board import server
from ..setup import attach, install, upgrade
from ..project import catalogs, github, improve, scope, structure, tasks, tree, workflows
from ..common import core
from ..worker import advance, budget, creds, dispatch as worker_dispatch, docker, drive, hooks, run
from ..state import resolve as state, sync as state_sync


STATUSES = ("in-progress", "review", "blocked", "planned")
USAGE = """usage: omi <command>
  attach [<repo path>] [--state <git url>]   register a code repo in detached omi state
  install-user [--remove]   install or remove user skills and Coordinator startup integration
  init [dir]   install the squad into a project (never overwrites)
  upgrade [--check | --to vX.Y.Z]   install a newer omi and update the project's unmodified template files (modified ones get <path>.omi-new)
  version      print the omi version and how to check for a newer one (also --version)
  status [--brief]   show tasks, checkpoints, delivery metrics and the next suggested task (--brief: one line per task and the next line)
  dockerfile reviewed   record that docker/Dockerfile was reviewed against this omi template; status warns again only when the template changes
  improve "<one line>" [--kind bug|security|idea] [--from <project>]   file an omi improvement
  sync         pull, commit leftover detached state changes and push
  board [--port N] [--no-open]   serve the read-only task board on 127.0.0.1 (default port 8765)
  guard        Claude Code PreToolUse hook: block writes outside task scope
  github       set up branches and rulesets: squad merges to development, only the PO to staging/main
  clean [<ID>] [--all] [--force]   remove this repo's worker containers, engineer session volumes and old worker images (--all: the current image too); <ID>: only that task's containers and volumes; refuses while a worker runs unless --force
  skills [check <task-file>]   write .omi/skills/CATALOG.md; or check a task's skills against the budget
  skills --check   validate every skill against the contract (parts, size, source, no widened permissions)
  token set [--tool claude|codex]   store the `claude setup-token` value (or the OpenAI API key) in Windows Credential Manager
  structure check [--changed|--baseline]   (structure init prints a proposed map from the tracked tree, never overwrites one) report files the .omi/structure.md map does not cover and imports against its layer or module rules; exit 1 on any not in .omi/structure-baseline.json (--baseline records them; --changed checks only files changed vs development, ignoring the baseline)
  plans        validate .omi/plans and write .omi/plans/CATALOG.md
  references   validate .omi/references and write .omi/references/CATALOG.md (task refs load as paths)
  rules        validate .omi/rules and write .omi/rules/CATALOG.md (rules auto-load by task scope)
  agents       write .omi/agents/CATALOG.md (one line per role)
  workflows [--check]   write .omi/workflows/CATALOG.md (one line per workflow); --check validates every workflow
  host-test <TASK-ID>   run `host_test` (.omi/config.json) on the host in the task's worktree; failure prints HOST TEST FAILED and counts as a fix round
  step <TASK-ID> next|done|back|skip|approve|reopen --why <reason>   record the task's workflow step (gates cannot be skipped; back --to <step> --why: return to an earlier agent step, e.g. architect; back and done take --why "<Coordinator reason>" (one round past max_fix_rounds) or --po "<PO's words>"; done --po overrides a review FAIL)
  note <TASK-ID> --step <step> --verdict <verdict> "<text>"   record a Coordinator decision under the task's ## Reports
  run <role> <TASK-ID> [--model M] [--effort E] [--tool claude|codex] [--fresh] [--why "<Coordinator reason>"|--po "<PO's words>"]   run a role in Docker (--fresh: no engineer session resume; read roles: ro worktree, after the deterministic checks)
  hook pre-run|post-run|pre-merge <TASK-ID>   run .omi/hooks/<event> (from the main checkout) in Docker against the task worktree; exits with its code
  dispatch next [--max N]   start ready parallel-safe planned tasks with skills picked (default: 1); starts `omi drive` unless it runs or `auto_drive` is false in .omi/config.json
  dispatch <role> <TASK-ID>   start `omi run` detached with a run record; refuses when scope or depends conflict with a running task; starts `omi drive` too
  stop <TASK-ID>   kill the task's running runs (wrapper process tree and containers), write rc and a `stopped` marker: watch shows DECIDE: STOPPED by <who>; never resumed
  drive [--once | --loop [--interval N]]   --loop: keep running when idle (poll every N s, default 60), resume idle in-progress tasks with a newer Coordinator note before planned ones; one loop per project (detached by dispatch): `omi advance` every finished run whose next action is NEXT:, `dispatch next` when a slot frees (`auto_dispatch_max` in .omi/config.json, default 1, 0 = off); stops a task only on DECIDE: and lists those; `omi advance` also runs `dispatch next` after a merge
  advance <TASK-ID> [--message "<msg>"] [--reject <n>[,<n>] --why "<reason>"] [--hook-fixed]   (--hook-fixed: accept a write run whose post-run hook failed once `omi hook post-run` passes on the current HEAD) scope-check a DONE write run, commit, rebase, draft PR, host-test and dispatch its reviewer; after a review FAIL: record the findings, step back, PR to draft, rerun the engineer (--reject leaves findings out); after review PASS: accept, pre-merge hook, PR ready, green CI, squash merge, pull, clean and post-merge test
  watch [--wait] [--all]   list running workers and every finished run not yet shown, with its next action (NEXT: deterministic, DECIDE: Coordinator); --wait blocks until a run finishes; --all: whole history
  parallel <TASK-ID> <TASK-ID> [...]   check that tasks can run in parallel (depends, status, scope overlap)
  worker <wt> <task-file> [--model M] [--effort E]   run the engineer in the Docker worker
  worker <wt> --prove   run docker/prove.sh in the worker (boundary check, no token)"""


def metrics(ts: dict) -> str:
    """Median lead time (first step start to the last step done, just before the merge), engineer runs per task,
    review FAIL rate and NEEDS SCOPE reports over the last 20 done tasks; '' without one."""
    done = []
    for m in ts.values():
        log = m.get("_text", "").partition("\n## Steps\n")[2].split("\n## ", 1)[0]
        stamps = re.findall(r"^- \S+ (started|done) (\d{4}-\d\d-\d\d \d\d:\d\d)", log, re.M)
        starts, ends = [s for e, s in stamps if e == "started"], [s for e, s in stamps if e == "done"]
        if m.get("status") == "done" and starts and ends:
            at = lambda s: datetime.datetime.strptime(s, "%Y-%m-%d %H:%M")  # noqa: E731
            done.append((at(ends[-1]), (at(ends[-1]) - at(starts[0])).total_seconds() / 3600, m["_text"]))
    done = sorted(done, key=lambda d: d[0])[-20:]
    if not done:
        return ""
    rows = [r for _, _, text in done for r in tasks.usage_rows(text)]
    reviews = [r for r in rows if r[0] in tasks.REVIEW_ROLES and r[-1][:4] in ("PASS", "FAIL")]
    fails = sum(r[-1].startswith("FAIL") for r in reviews)
    scope_asks = sum(len(re.findall(r"^> \W*NEEDS SCOPE\b", text.partition("\n## Reports\n")[2].split("\n## ", 1)[0], re.M)) for _, _, text in done)
    return (f"last {len(done)} done: lead time median {statistics.median(h for _, h, _ in done):.1f} h, "
            f"engineer runs/task {sum(r[0] == 'omi-agent-engineer' for r in rows) / len(done):.1f}, "
            f"review FAIL rate {fails}/{len(reviews)}{f' ({fails * 100 // len(reviews)}%)' if reviews else ''}, NEEDS SCOPE {scope_asks}")


def busy_tasks(project) -> tuple[list[dict], set[str]]:
    """(run records, ids of tasks with a running worker)."""
    try:
        recs = worker_dispatch.records(project.code)
    except state.StateError:
        recs = []
    busy = {r["tid"] for r in recs if r["running"]}
    return recs, busy | {row[0] for row in docker.running_workers(project.state if project.detached else project.code)}


def next_line(ts: dict, kids: dict, busy: set[str]) -> str:
    done = {k for k, m in ts.items() if m.get("status") == "done"}
    resume = [f"{k} (resume)" for k, m in ts.items() if m.get("status") == "in-progress" and k not in kids and k not in busy]
    nxt = next((k for k, m in ts.items()
                if m.get("status", "planned") == "planned" and k not in kids and set(core.split(m.get("depends"))) <= done), None)
    return f"next: {' '.join(resume + ([nxt] if nxt else [])) or 'none ready'}"


def brief(project) -> None:
    """`omi status --brief`: one line per open task (id, step, tool, running; runs over their token budget), the next line."""
    ts = tasks.rolled_up(tasks.tasks(project))
    kids = tree.children_map(ts)
    recs, busy = busy_tasks(project)
    budgets = {}
    budget_of = lambda role: budgets.setdefault(role, budget.token_budget(project, role, ts))  # noqa: E731
    for st in STATUSES:
        for k, m in ts.items():
            if m.get("status", "planned") == st and k not in kids:
                over = budget.over_budget(m["_text"], budget_of)
                print(f"{k} {m.get('step') or '-'} {m.get('tool') or '-'} {'running' if k in busy else st}"
                      + (f" · over budget: {', '.join(over)}" if over else ""))
    print(next_line(ts, kids, busy))
    if unhandled := sum(not r["running"] and not r["reported"] for r in recs):
        print(f"finished runs not handled: {unhandled}; run python -m omi watch")


def status(cwd=".", brief_form=False):
    project = state.resolve(cwd)
    if project.detached:
        attach.warn_in_repo_files(project.code)
        state_sync.pull(project)
    if brief_form:
        return brief(project)
    root = project.state
    print(f"branch: {core.git(cwd, 'rev-parse', '--abbrev-ref', 'HEAD')}")
    stamp_file = root / ".omi" / "version"
    stamp = stamp_file.read_text(encoding="utf-8").strip() if stamp_file.exists() else ""
    print(f"omi {core.version()} (project {stamp or 'none'})")
    try:
        old = not stamp or core.semver(stamp) < core.semver(core.version())
        if stamp and core.semver(stamp) > core.semver(core.version()):
            print(f'this project needs omi {stamp}; install it: python -m pip install --user "git+https://github.com/omi-teams/omi@v{stamp}"')
    except ValueError:
        old = True
    if old:
        print(f"run `python -m omi upgrade --apply` to bring the project files to omi {core.version()}")
    if not old:
        upgrade.stale_template_hint(root, detached=project.detached)
    if install.stale_user_integration():
        print("installed omi user skills or Codex block differ from the current template; run `python -m omi install-user`")
    source = project.state.name if project.detached else project.code.name
    print(f"omi improvements filed: {improve.open_count(source)} open")
    for line in upgrade.dockerfile_hint(project):
        print(line)
    for line in docker.full_volumes(root if project.detached else project.code):
        print(line)
    cfg = root / ".omi" / "config.json"
    try:
        missing_test = cfg.exists() and not json.loads(cfg.read_text(encoding="utf-8")).get("test")
    except ValueError:
        missing_test = False
    if missing_test:
        print('no `test` command in .omi/config.json; set one, e.g. "test": "python3 -m pytest -q"')
    ts = tasks.rolled_up(tasks.tasks(project))
    kids = tree.children_map(ts)
    finished = []
    for pid, m in catalogs.load_plans(root, strict=False).items():
        members = [t for t in ts.values() if t.get("plan") == pid]
        done_count = sum(t.get("status") == "done" for t in members)
        if tasks.plan_status(m["status"], [t.get("status") for t in members]) == "done":
            if m["status"] != "done":  # stored-done plans stay hidden, as before
                finished.append(pid)
        else:
            print(f"{pid} {m['title']}: done {done_count}/{len(members)}")
    if finished:
        print(f"done plans: {', '.join(finished)}")
    if not ts:
        print("no tasks yet - run omi-idea")
        docker.print_workers(project)
        return
    done = {k for k, m in ts.items() if m.get("status") == "done"}
    print(f"done: {len(done)}/{len(ts)}")
    if line := metrics(ts):
        print(line)
    for st in STATUSES:
        for k, m in ts.items():
            if m.get("status", "planned") == st and k not in kids:
                try:
                    steps = workflows.get_workflow(root, m.get("workflow") or workflows.DEFAULT_WORKFLOW)
                except SystemExit:
                    steps = []
                ph = tasks.phase(m, steps)
                print(f"[{ph['label']}] {k} {m.get('title', '')}")
                if ph["step"] and steps:
                    rnd = f" · vòng {ph['review_round']}" if ph["review_round"] else ""
                    print(f"  bước {ph['step_index'] or '?'}/{ph['step_count']} {ph['step']}{rnd} · {m.get('tool', '-')} {m.get('model', '-')}/{m.get('effort', '-')}")
                    print("  " + tasks.step_strip(m, steps))
                if st == "in-progress":
                    print(f"  resume: omi-task {k}")
                if st != "planned":
                    if "worktree" in m:
                        print(f"  worktree: {m['worktree']}")
                        print("  " + tasks.drift(m["worktree"], k))
                    for line in tasks.checkpoint(m["_text"]).splitlines():
                        print(f"  {line}")
                if tasks.usage_totals(m["_text"]):
                    print("  " + tasks.usage_totals(m["_text"]))
    if kids:
        print("tree:")
        show = lambda k, depth: (print(f"{'  ' * depth}{k} [{ts[k].get('type') or 'task'}] {ts[k]['status']} {ts[k].get('title', '')}"
                                       + (f" ({sum(ts[c]['status'] == 'done' for c in kids[k])}/{len(kids[k])} done)" if k in kids else "")),
                                 [show(c, depth + 1) for c in kids.get(k, [])])
        for k, m in ts.items():
            if m.get("parent") not in ts:
                show(k, 0)
    recs, busy = busy_tasks(project)
    print(next_line(ts, kids, busy))
    unhandled = sum(not r["running"] and not r["reported"] for r in recs)
    if unhandled:
        print(f"finished runs not handled: {unhandled}; run python -m omi watch")
    docker.print_workers(project)


def main(argv: list[str] | None = None) -> None:
    try:
        args = sys.argv[1:] if argv is None else argv
        cmd = args[0] if args else "help"
        if cmd != "guard":  # guard handles StateError itself and must exit 2 (blocking), not 1
            state.registry()
        mutates = cmd in {"init", "upgrade", "skills", "rules", "plans", "references", "agents", "dockerfile",
                          "workflows", "step", "note", "host-test", "run", "hook", "worker", "dispatch"}
        target = args[1] if cmd == "init" and len(args) > 1 else "."
        project = state.resolve(target) if mutates else None
        if project and project.detached:
            state_sync.conflicts(state_sync.repo(project))
        before = state_sync.snapshot(project) if project and project.detached else None
        try:
            return dispatch(argv)
        finally:
            if before is not None:
                after = state_sync.snapshot(project)
                paths = sorted(p for p in before.keys() | after.keys()
                               if not p.endswith(".omi-new") and before.get(p) != after.get(p))
                if paths:
                    state_sync.commit(project, paths, cmd + " state")
                    state_sync.push(project)
    except state.StateError as exc:
        sys.exit("OMI: " + " ".join(str(exc).splitlines()))


def dispatch(argv: list[str] | None = None) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:] if argv is None else argv
    cmd, rest = (args[0], args[1:]) if args else ("help", [])
    if cmd in ("upgrade", "skills", "rules", "plans", "references", "agents", "workflows"):
        project = state.resolve()
        root = state.catalog_root(project, ".")
    if cmd in ("version", "--version"):
        print(f"omi {core.version()}\nlatest: python -m omi upgrade --check")
    elif cmd == "attach":
        attach.attach(rest)
    elif cmd == "install-user":
        if rest not in ([], ["--remove"]):
            raise state.StateError("usage: omi install-user [--remove]")
        try:
            install.install_user(remove=bool(rest))
        except (OSError, UnicodeError) as exc:
            raise state.StateError(f"cannot install/remove user integration: {exc}") from exc
    elif cmd == "session-start":
        project = state.resolve()
        if project.detached:
            print(install.coordinator_rules())
            print(f"omi state: {project.state}")
            status()
    elif cmd == "init":
        target = rest[0] if rest else "."
        project = state.resolve(target)
        upgrade.init(state.catalog_root(project, target), detached=project.detached)
    elif cmd == "upgrade":
        sys.exit(upgrade.upgrade_cmd(rest, root, detached=project.detached))
    elif cmd == "template-shas" and len(rest) == 2:
        upgrade.template_shas_cmd(*rest)
    elif cmd == "template-regen" and len(rest) <= 1:
        upgrade.template_regen(*rest)
    elif cmd == "improve":
        improve.improve(rest)
    elif cmd == "sync":
        project = state.resolve()
        if rest:
            raise state.StateError("usage: omi sync")
        if not project.detached:
            raise state.StateError("omi sync requires a detached project (omi attach)")
        sys.exit(state_sync.sync(project))
    elif cmd == "status":
        status(*[a for a in rest if a != "--brief"][:1], brief_form="--brief" in rest)
    elif cmd == "dockerfile" and rest == ["reviewed"]:
        upgrade.dockerfile_reviewed(state.resolve())
    elif cmd == "board":
        port = core.flag(rest, "--port")
        if not set(rest) <= {"--port", "--no-open", port} or ("--port" in rest and not ((port or "").isascii() and (port or "").isdigit())):
            raise state.StateError("usage: omi board [--port N] [--no-open]")
        try:
            httpd = server.make_server(int(port) if port else 8765)
        except (OSError, OverflowError) as exc:
            raise state.StateError(f"cannot bind 127.0.0.1:{port or 8765}: {exc}") from exc
        url = f"http://127.0.0.1:{httpd.server_port}/"
        print(f"omi board: {url} (Ctrl+C to stop)")
        if "--no-open" not in rest:
            webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            httpd.server_close()
    elif cmd == "github":
        project = state.resolve()
        with contextlib.chdir(project.code if project.detached else Path.cwd()):
            github.github("--po" in rest)
    elif cmd == "clean":
        ids = [a for a in rest if not a.startswith("--")]
        docker.clean(all_images="--all" in rest, task=ids[0] if ids else None, force="--force" in rest)
    elif cmd == "skills":
        if rest[:1] == ["--check"]:
            catalogs.check_all_skills(root)
        elif rest[:1] == ["check"] and len(rest) > 1:
            project = state.resolve()
            task = Path(rest[1])
            if project.detached and not task.is_absolute():
                task = project.state / task
            meta = core.meta(task)
            catalogs.check_skills(project.state, catalogs.task_skill_ids(project.state, meta))
            if meta.get("step"):  # the current step's role against the task role
                steps = workflows.get_workflow(project.state, meta.get("workflow") or workflows.DEFAULT_WORKFLOW)
                workflows.check_role(project.state, meta, next((s["role"] for s in steps if s["id"] == meta["step"]), workflows.COORDINATOR))
            tasks.warn_sensitive(core.meta(task))
            print("skills ok")
        else:
            catalogs.skills_catalog(root)
    elif cmd == "parallel" and len(rest) >= 2:
        conflicts = tasks.parallel(state.resolve(core.main_checkout(".") or Path(".").resolve()), rest)
        if conflicts:
            sys.exit("\n".join(conflicts))
        print("parallel ok: " + " ".join(rest))
    elif cmd == "rules":
        catalogs.rules_catalog(root)
    elif cmd == "plans":
        catalogs.plans_catalog(root)
    elif cmd == "references":
        catalogs.references_catalog(root)
    elif cmd == "agents":
        catalogs.agents_catalog(root)
    elif cmd == "workflows":
        workflows.check_all_workflows(root) if rest[:1] == ["--check"] else workflows.workflows_catalog(root)
    elif cmd == "structure" and rest[:1] == ["check"] and set(rest[1:]) <= {"--changed", "--baseline"} and not {"--changed", "--baseline"} <= set(rest):
        project = state.resolve()
        try:
            sys.exit(structure.check(project.code, project.state, "--changed" in rest, "--baseline" in rest))
        except structure.StructureError as exc:
            sys.exit(f"OMI: {exc}")
    elif cmd == "structure" and rest == ["init"]:
        project = state.resolve()
        try:
            sys.exit(structure.init(project.code, project.state))
        except structure.StructureError as exc:
            sys.exit(f"OMI: {exc}")
    elif cmd == "step" and len(rest) >= 2:
        cut = rest.index("--why") if "--why" in rest else len(rest)
        head = rest[:cut]
        to, po = core.flag(head, "--to"), core.flag(head, "--po")
        why = " ".join(rest[cut + 1:]) if cut < len(rest) else None
        if "--to" in head and (rest[1] != "back" or not to or to.startswith("--")):
            sys.exit(f"usage: omi step {rest[0]} back --to <step> --why <reason>. Nothing changed.")
        project = state.resolve(core.main_checkout(".") or Path(".").resolve())
        worker_dispatch.claim(project, rest[0])
        sys.exit(tasks.step(project, rest[0], rest[1], why, to=to, po=po))
    elif cmd == "note" and rest:
        step_id, verdict = core.flag(rest, "--step"), core.flag(rest, "--verdict")
        words = [w for i, w in enumerate(rest[1:]) if w not in ("--step", "--verdict") and rest[i] not in ("--step", "--verdict")]
        tasks.note(state.resolve(core.main_checkout(".") or Path(".").resolve()), rest[0], step_id, verdict, " ".join(words))
    elif cmd == "run" and len(rest) >= 2 and not rest[1].startswith("--"):
        project = state.resolve(core.main_checkout(".") or Path(".").resolve())
        tasks.check_runnable(project, rest[1])
        if catalogs.get_role(project.state, rest[0])["access"] == "write":
            tasks.run_gate(project, rest[1], core.flag(rest, "--po"), core.flag(rest, "--why"))
            structure.require_map(project.state)
        argv = [sys.executable, "-m", "omi", "run", *rest]
        sys.exit(worker_dispatch.foreground(project, rest[1], rest[0], argv, lambda: run.run_cmd(rest[0], rest[1], rest)))
    elif cmd == "dispatch" and rest[:1] == ["next"]:
        if len(rest) not in (1, 3) or (len(rest) == 3 and (rest[1] != "--max" or not rest[2].isascii()
                                                                     or not rest[2].isdigit() or int(rest[2]) < 1)):
            raise state.StateError("usage: omi dispatch next [--max N] (N must be positive)")
        project = state.resolve(core.main_checkout(".") or Path(".").resolve())
        worker_dispatch.dispatch_next(project, int(rest[2]) if len(rest) == 3 else 1)
        worker_dispatch.start_driver(project)
    elif cmd == "dispatch" and len(rest) == 2 and not rest[1].startswith("--"):
        project = state.resolve(core.main_checkout(".") or Path(".").resolve())
        tasks.check_runnable(project, rest[1])
        if (task := state.task_file(project, rest[1])).exists():
            workflows.check_role(project.state, core.meta(task), rest[0])
        if catalogs.get_role(project.state, rest[0])["access"] == "write":
            structure.require_map(project.state)
        worker_dispatch.launch(project, rest[1], rest[0])
        worker_dispatch.start_driver(project)
    elif cmd == "drive" and set(rest) - {core.flag(rest, "--interval")} <= {"--once", "--loop", "--interval"}:
        interval = core.flag(rest, "--interval") or "60"
        if not interval.isdigit() or int(interval) < 1 or ("--interval" in rest and "--loop" not in rest):
            raise state.StateError("usage: omi drive [--once | --loop [--interval N]] (N seconds, positive)")
        drive.drive(state.resolve(core.main_checkout(".") or Path(".").resolve()), "--once" in rest,
                    loop=int(interval) if "--loop" in rest else None)
    elif cmd == "stop" and len(rest) == 1:
        worker_dispatch.stop(state.resolve(core.main_checkout(".") or Path(".").resolve()), rest[0], os.environ.get("OMI_BY") or "Coordinator")
    elif cmd == "advance" and (opts := [a for a in rest if a != "--hook-fixed"]) and len(opts) % 2 == 1 and set(opts[1::2]) <= {"--message", "--reject", "--why"}:
        reject = core.flag(opts, "--reject")
        if reject is not None and not all(n.isdigit() for n in reject.split(",")):
            sys.exit('usage: omi advance <TASK-ID> [--message "<msg>"] [--reject <n>[,<n>] --why "<reason>"] [--hook-fixed]')
        project = state.resolve(core.main_checkout(".") or Path(".").resolve())
        worker_dispatch.claim(project, opts[0])
        advance.advance(project, opts[0], core.flag(opts, "--message"), [int(n) for n in reject.split(",")] if reject else None,
                        core.flag(opts, "--why"), hook_fixed="--hook-fixed" in rest)
    elif cmd == "watch" and set(rest) <= {"--wait", "--all"}:
        worker_dispatch.watch(state.resolve(core.main_checkout(".") or Path(".").resolve()), "--wait" in rest, "--all" in rest)
    elif cmd == "host-test" and len(rest) == 1:
        sys.exit(run.host_test(state.resolve(core.main_checkout(".") or Path(".").resolve()), rest[0]))
    elif cmd == "hook" and len(rest) == 2:
        sys.exit(hooks.hook_cmd(*rest))
    elif cmd == "guard":
        sys.exit(scope.guard())
    elif cmd == "token" and rest[:1] == ["set"]:
        if "--tool" in rest and rest[rest.index("--tool") + 1:][:1] not in (["claude"], ["codex"]):
            sys.exit("usage: omi token set [--tool claude|codex]")
        creds.token_set(rest[rest.index("--tool") + 1] if "--tool" in rest else "claude")
    elif cmd == "worker" and rest:
        prove = "--prove" in rest
        if not prove and (len(rest) < 2 or rest[1].startswith("--")):
            sys.exit("usage: omi worker <wt> <task-file> [--model M] [--effort E]")
        sys.exit(run.worker(rest[0], None if prove else rest[1], core.flag(rest, "--model"), core.flag(rest, "--effort"), prove))
    else:
        print(USAGE)
