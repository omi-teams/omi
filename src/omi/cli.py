"""Command line: usage text, omi status and argument dispatch."""

import contextlib
import json
import sys
from pathlib import Path

from . import catalogs, core, creds, docker, github, hooks, run, scope, state, tasks, upgrade, workflows


STATUSES = ("in-progress", "review", "blocked", "planned")
USAGE = """usage: omi <command>
  attach [<repo path>] [--state <git url>]   register a code repo in detached omi state
  init [dir]   install the squad into a project (never overwrites)
  upgrade [--check | --to vX.Y.Z]   install a newer omi and update the project's unmodified template files (modified ones get <path>.omi-new)
  version      print the omi version and how to check for a newer one (also --version)
  status       show tasks, checkpoints and the next suggested task
  guard        Claude Code PreToolUse hook: block writes outside task scope
  github       set up branches and rulesets: squad merges to development, only the PO to staging/main
  clean [--all]   remove this repo's worker containers and old worker images (--all: the current image too)
  skills [check <task-file>]   write .omi/skills/CATALOG.md; or check a task's skills against the budget
  skills --check   validate every skill against the contract (parts, size, source, no widened permissions)
  token set [--tool claude|codex]   store the `claude setup-token` value (or the OpenAI API key) in Windows Credential Manager
  plans        validate .omi/plans and write .omi/plans/CATALOG.md
  references   validate .omi/references and write .omi/references/CATALOG.md (task refs load as paths)
  rules        validate .omi/rules and write .omi/rules/CATALOG.md (rules auto-load by task scope)
  agents       write .omi/agents/CATALOG.md (one line per role)
  workflows [--check]   write .omi/workflows/CATALOG.md (one line per workflow); --check validates every workflow
  step <TASK-ID> next|done|back|skip --why <reason>   record the task's workflow step (gates cannot be skipped)
  run <role> <TASK-ID> [--model M] [--effort E] [--tool claude|codex]   run a role in Docker (read roles: ro worktree, after the deterministic checks)
  hook pre-run|post-run|pre-merge <TASK-ID>   run .omi/hooks/<event> (from the main checkout) in Docker against the task worktree; exits with its code
  parallel <TASK-ID> <TASK-ID> [...]   check that tasks can run in parallel (depends, status, scope overlap)
  worker <wt> <task-file> [--model M] [--effort E]   run the engineer in the Docker worker
  worker <wt> --prove   run docker/prove.sh in the worker (boundary check, no token)"""


def status(cwd="."):
    project = state.resolve(cwd)
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
    dockerfile = root / "docker" / "Dockerfile"
    if dockerfile.exists() and dockerfile.read_bytes().replace(b"\r\n", b"\n") != (core.TEMPLATE / "docker" / "Dockerfile").read_bytes().replace(b"\r\n", b"\n"):
        print(f"docker/Dockerfile differs from the omi {core.version()} template; review it (omi init never overwrites it)")
        print(f"  see the diff: git diff --no-index {core.TEMPLATE / 'docker' / 'Dockerfile'} docker/Dockerfile\n  merge by hand; omi init and upgrade never overwrite it")
    for line in docker.full_volumes(root if project.detached else project.code):
        print(line)
    cfg = root / ".omi" / "config.json"
    try:
        missing_test = cfg.exists() and not json.loads(cfg.read_text(encoding="utf-8")).get("test")
    except ValueError:
        missing_test = False
    if missing_test:
        print('no `test` command in .omi/config.json; set one, e.g. "test": "python3 -m pytest -q"')
    ts = tasks.tasks(project)
    for pid, m in catalogs.load_plans(root, strict=False).items():
        if m["status"] == "active":
            members = [t for t in ts.values() if t.get("plan") == pid]
            done_count = sum(t.get("status") == "done" for t in members)
            print(f"{pid} {m['title']}: done {done_count}/{len(members)}")
    if not ts:
        print("no tasks yet - run omi-idea")
        docker.print_workers(project)
        return
    done = {k for k, m in ts.items() if m.get("status") == "done"}
    print(f"done: {len(done)}/{len(ts)}")
    for st in STATUSES:
        for k, m in ts.items():
            if m.get("status", "planned") == st:
                print(f"[{st}] {k} {m.get('title', '')}" + (f" (step: {m['step']})" if st == "in-progress" and m.get("step") else ""))
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
    nxt = next((k for k, m in ts.items()
                if m.get("status", "planned") == "planned" and set(core.split(m.get("depends"))) <= done), None)
    print(f"next: {nxt or 'none ready'}")
    docker.print_workers(project)


def main(argv: list[str] | None = None) -> None:
    try:
        state.registry()
        return dispatch(argv)
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
        upgrade.attach(rest)
    elif cmd == "init":
        target = rest[0] if rest else "."
        project = state.resolve(target)
        upgrade.init(state.catalog_root(project, target), detached=project.detached)
    elif cmd == "upgrade":
        sys.exit(upgrade.upgrade_cmd(rest, root, detached=project.detached))
    elif cmd == "template-shas" and len(rest) == 2:
        upgrade.template_shas_cmd(*rest)
    elif cmd == "status":
        status(*rest[:1])
    elif cmd == "github":
        project = state.resolve()
        with contextlib.chdir(project.code if project.detached else Path.cwd()):
            github.github("--po" in rest)
    elif cmd == "clean":
        docker.clean(all_images="--all" in rest)
    elif cmd == "skills":
        if rest[:1] == ["--check"]:
            catalogs.check_all_skills(root)
        elif rest[:1] == ["check"] and len(rest) > 1:
            project = state.resolve()
            task = Path(rest[1])
            if project.detached and not task.is_absolute():
                task = project.state / task
            catalogs.check_skills(project.state, catalogs.task_skill_ids(project.state, core.meta(task)))
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
    elif cmd == "step" and len(rest) >= 2:
        why = " ".join(rest[rest.index("--why") + 1:]) if "--why" in rest else None
        sys.exit(tasks.step(state.resolve(core.main_checkout(".") or Path(".").resolve()), rest[0], rest[1], why))
    elif cmd == "run" and len(rest) >= 2 and not rest[1].startswith("--"):
        sys.exit(run.run_cmd(rest[0], rest[1], rest))
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
