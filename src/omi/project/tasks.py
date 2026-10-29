"""Task files: step log and `omi step`, frontmatter, notes, usage table, parallel check, drift."""

import datetime
import re
import sys
from pathlib import Path

from . import catalogs, workflows
from ..common import core
from ..state import resolve as state


STEP_LOG = re.compile(r"^- (\S+) (started|done|skipped|failed) ", re.M)


def step_states(text):
    """{step id: last recorded event} from the task's `## Steps` log."""
    _, sep, rest = text.partition("\n## Steps\n")
    return dict(STEP_LOG.findall(rest.split("\n## ", 1)[0])) if sep else {}


def po_approved(text, sid):
    """The Coordinator records the PO's words as a line `PO approval <step>: <text>` inside `## Steps`."""
    _, sep, rest = text.partition("\n## Steps\n")
    current = re.split(r"^- workflow reopened .*", rest.split("\n## ", 1)[0], flags=re.M)[-1]
    return bool(sep) and re.search(rf"^(?:- )?PO approval {re.escape(sid)}: *\S", current, re.M) is not None


def unticked(text):
    """Unticked `- [ ]` lines of the `## Acceptance criteria` section."""
    sec = text.partition("\n## Acceptance criteria\n")[2].split("\n## ", 1)[0]
    return [l for l in sec.splitlines() if l.startswith("- [ ]")]


def set_front(text, key, value):
    _, front, body = text.split("---", 2)
    lines = [ln for ln in front.split("\n") if ln.partition(":")[0].strip() != key]
    lines.insert(len(lines) - 1, f"{key}: {value}")
    return f"---{chr(10).join(lines)}---{body}"


FRONT_OWNED = ("step", "status", "workflow", "scope", "role", "skills", "refs", "plan", "model", "effort", "tool", "step_settings")  # Coordinator-owned task frontmatter


def front_of(text):
    """The raw frontmatter block (between the `---` lines) of a task file, or None."""
    return text.split("---", 2)[1] if text.startswith("---") and text.count("---") >= 2 else None


def revert_front(task, before):
    """Put the original lines of the Coordinator-owned frontmatter fields back (same position); returns the fields restored.
    `before` is the original text of the task file. A deleted file or lost frontmatter is restored as `frontmatter`."""
    old = front_of(before)
    if old is None:
        return []
    text = task.read_text(encoding="utf-8") if task.exists() else None
    cur = front_of(text) if text is not None else None
    if cur is None:
        task.write_text(before if text is None else f"---{old}---\n{text}", encoding="utf-8")
        return ["frontmatter"]
    olines, lines, changed = old.split("\n"), cur.split("\n"), []
    for key in FRONT_OWNED:
        mine = lambda ln: ln.partition(":")[0].strip() == key
        want = [(i, ln) for i, ln in enumerate(olines) if mine(ln)]
        if [ln for ln in lines if mine(ln)] == [ln for _, ln in want]:
            continue
        changed.append(key)
        lines = [ln for ln in lines if not mine(ln)]
        for i, ln in want:
            lines.insert(min(i, len(lines) - 1), ln)
    if changed:
        task.write_text(f"---{chr(10).join(lines)}---{text.split('---', 2)[2]}", encoding="utf-8")
    return changed


def add_step_log(text, line):
    head, sep, rest = text.partition("\n## Steps\n")
    if not sep:
        return text.rstrip("\n") + f"\n\n## Steps\n{line}\n"
    body, nxt, tail = rest.partition("\n## ")
    body = body.rstrip("\n") + "\n" if body.strip() else ""
    return f"{head}{sep}{body}{line}\n" + (f"\n## {tail}" if nxt else "")


SENSITIVE_SCOPE = (r".*migration.*", r"auth([-_.*].*)?", r"secrets?", r"\.github")  # scope path segments (regex, fullmatch) that want omi-flow-feature-sensitive


def warn_sensitive(m):
    """Print a warning (never fail) when the task's scope touches a sensitive path under a non-sensitive workflow."""
    if m.get("workflow") == "omi-flow-feature-sensitive":
        return
    segs = dict.fromkeys(seg for g in core.split(m.get("scope")) for seg in g.lower().split("/"))
    for seg in segs:
        if any(re.fullmatch(p, seg) for p in SENSITIVE_SCOPE):
            print(f"WARN: scope touches {seg} - consider omi-flow-feature-sensitive")


def commit_task_file(root, task, msg):
    """Commit only the task file on the development checkout; other staged or unstaged changes stay as they are."""
    rel = task.relative_to(root).as_posix()
    if core.git(root, "add", "--", rel) is not None:
        core.git(root, "commit", "-m", msg, "--only", "--", rel)


def sync_scope(wt, task, tid):
    """Copy the `scope:` line of the task file on development into the worktree's task file when they differ."""
    if state.resolve(wt).detached:
        return
    dev = core.git(wt, "show", f"development:.omi/tasks/{tid}.md")
    if not dev or not task.exists():
        return
    line = next((ln for ln in (front_of(dev) or "").split("\n") if ln.partition(":")[0].strip() == "scope"), None)
    text = task.read_text(encoding="utf-8")
    if line is None or core.split(core.parse(dev).get("scope")) == core.split(core.parse(text).get("scope")):
        return
    head, front, rest = text.split("---", 2)
    lines = front.split("\n")
    for i, ln in enumerate(lines):
        if ln.partition(":")[0].strip() == "scope":
            lines[i] = line
            break
    else:
        lines.insert(len(lines) - 1, line)
    task.write_text(f"{head}---{chr(10).join(lines)}---{rest}", encoding="utf-8")
    print(f"SCOPE SYNCED: {core.parse(dev).get('scope')}")


def step(root, tid, action, why=None, now=None):
    """Record a workflow step in the task file: `next` starts the following step, `done` closes the current one,
    `skip` closes it with a reason, `back` fails a started review gate and restarts the nearest earlier write step.
    `approve` records PO words; `reopen` restarts the last write step of a completed workflow.
    Gate steps cannot be skipped; a `po` gate needs the PO approval line."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", tid):
        sys.exit(f"invalid task id `{tid}`: use letters, digits, `-` and `_`. Nothing changed.")
    project = state.resolve(root)
    root = project.state
    task = state.task_file(project, tid)
    if not task.exists():
        sys.exit(f"no task file {task}. Nothing changed.")
    m = core.meta(task)
    wid = m.get("workflow") or workflows.DEFAULT_WORKFLOW
    steps = workflows.get_workflow(root, wid)
    ids = [s["id"] for s in steps]
    text, events, cur = m["_text"], step_states(m["_text"]), m.get("step") or ""
    if cur and cur not in ids:
        sys.exit(f"{tid}: step `{cur}` is not in workflow {wid} ({', '.join(ids)}). Nothing changed.")
    at = ids.index(cur) if cur else -1
    open_steps = [s for s in ids[:max(at, 0)] if events.get(s) not in ("done", "skipped")]
    if open_steps:
        sys.exit(f"{tid}: at step {cur} but {', '.join(open_steps)} not done or skipped; steps cannot be jumped over. "
                 "Nothing changed.")
    stamp = (now or datetime.datetime.now()).strftime("%Y-%m-%d %H:%M")
    if action == "reopen":
        if any(events.get(s) == "started" for s in ids):
            sys.exit(f"{tid}: a step is running; cannot reopen. Nothing changed.")
        if at != len(ids) - 1 or any(events.get(s) not in ("done", "skipped") for s in ids):
            sys.exit(f"{tid}: workflow {wid} is not complete; cannot reopen. Nothing changed.")
        if not (why or "").strip():
            sys.exit(f"usage: omi step {tid} reopen --why <reason>. Nothing changed.")
        prev = next((s for s in reversed(steps)
                     if s["role"] != workflows.COORDINATOR and catalogs.get_role(root, s["role"])["access"] == "write"), None)
        if not prev:
            sys.exit(f"{tid}: no write step to reopen. Nothing changed.")
        text = add_step_log(text, f"- workflow reopened {stamp}: {' '.join(why.split())}")
        for s in steps[ids.index(prev["id"]) + 1:]:
            text = add_step_log(text, f"- {s['id']} failed {stamp}")
        text = set_front(set_front(text, "step", prev["id"]), "status", "in-progress")
        text = add_step_log(text, f"- {prev['id']} started {stamp}")
        msg = f"{tid}: workflow reopened; back to {prev['id']} ({prev['role']})"
    elif action == "next":
        if cur and events.get(cur) not in ("done", "skipped"):
            sys.exit(f"{tid}: step {cur} is not done; run `omi step {tid} done` or `skip --why`. Nothing changed.")
        if cur and steps[at]["gate"] == "po" and not po_approved(text, cur):
            sys.exit(f"{tid}: step {cur} is a po gate; add the line `PO approval {cur}: <PO's words>` under `## Steps` first. "
                     "Nothing changed.")
        if cur and steps[at]["gate"] == "po" and unticked(text):
            sys.exit(f"{tid}: step {cur} is a po gate; tick the reviewed acceptance criteria first:\n"
                     + "\n".join(unticked(text)) + "\nNothing changed.")
        if at + 1 == len(ids):
            print(f"{tid}: workflow {wid} is complete")
            return 0
        new = steps[at + 1]
        if new["role"] != workflows.COORDINATOR:
            catalogs.get_role(root, m.get("role") or "omi-agent-engineer")  # unknown task role fails too
        catalogs.check_skills(root, workflows.step_skill_ids(root, new, m))
        if cur == "plan":
            warn_sensitive(m)
        text = add_step_log(set_front(text, "step", new["id"]), f"- {new['id']} started {stamp}")
        msg = (f"{tid}: step {new['id']} ({new['role']}, gate {new['gate']}): input {new['input']}; "
               f"output {new['output']}; stop when {new['stop']}")
    elif not cur:
        sys.exit(f"{tid}: no step started; run `omi step {tid} next`. Nothing changed.")
    elif events.get(cur) in ("done", "skipped"):
        sys.exit(f"{tid}: step {cur} is already {events[cur]}; run `omi step {tid} next`. Nothing changed.")
    elif action == "approve":
        if steps[at]["gate"] != "po":
            sys.exit(f"{tid}: step {cur} is not a po gate; cannot approve. Nothing changed.")
        if not (why or "").strip():
            sys.exit(f"usage: omi step {tid} approve --why <PO words>. Nothing changed.")
        text = add_step_log(text, f"PO approval {cur}: {' '.join(why.split())}")
        msg = f"{tid}: step {cur} PO approval recorded"
    elif action == "back":
        if steps[at]["gate"] != "review":
            sys.exit(f"{tid}: step {cur} is not a review gate; `back` only fails a started review step. Nothing changed.")
        prev = next((s for s in reversed(steps[:at])
                     if s["role"] != workflows.COORDINATOR and catalogs.get_role(root, s["role"])["access"] == "write"), None)
        if not prev:
            sys.exit(f"{tid}: no write step before {cur} to go back to. Nothing changed.")
        text = add_step_log(set_front(text, "step", prev["id"]), f"- {cur} failed {stamp}")
        text = add_step_log(text, f"- {prev['id']} started {stamp}")
        msg = f"{tid}: step {cur} failed; back to {prev['id']} ({prev['role']}), then `omi step {tid} done` and `next`"
    elif action == "done":
        if (re.findall(r"^\d{4}-\d\d-\d\d \d\d:\d\d hook post-run (FAILED|passed)", text, re.M) or [""])[-1] == "FAILED":
            sys.exit(f"{tid}: the last post-run hook failed; fix it and rerun `omi run` first. Nothing changed.")
        if steps[at]["gate"] == "po" and not po_approved(text, cur):
            sys.exit(f"{tid}: step {cur} is a po gate; add the line `PO approval {cur}: <PO's words>` under `## Steps` first. "
                     "Nothing changed.")
        if steps[at]["gate"] == "po" and unticked(text):
            sys.exit(f"{tid}: step {cur} is a po gate; tick the reviewed acceptance criteria first:\n"
                     + "\n".join(unticked(text)) + "\nNothing changed.")
        if steps[at]["gate"] == "review":
            rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in text.partition("\n## Usage")[2].split("\n## ", 1)[0].splitlines()
                    if l.startswith("|") and not l.startswith("|---") and not l.startswith("| role")]
            last = [r[-1].split()[0] for r in rows if r[0] == steps[at]["role"] and r[-1][:4] in ("PASS", "FAIL")]
            if last and last[-1] == "FAIL":
                sys.exit(f"{tid}: the last {steps[at]['role']} verdict is FAIL; run `omi step {tid} back`. Nothing changed.")
        text, msg = add_step_log(text, f"- {cur} done {stamp}"), f"{tid}: step {cur} done"
    elif action == "skip":
        if not (why or "").strip():
            sys.exit(f"usage: omi step {tid} skip --why <reason>. Nothing changed.")
        if steps[at]["gate"] != "none":
            sys.exit(f"{tid}: step {cur} has gate {steps[at]['gate']} and cannot be skipped. Nothing changed.")
        text = add_step_log(text, f"- {cur} skipped {stamp}: {' '.join(why.split())}")
        msg = f"{tid}: step {cur} skipped"
    else:
        sys.exit("usage: omi step <TASK-ID> next|done|back|skip|approve|reopen --why <reason>")
    task.write_text(text, encoding="utf-8")
    print(msg)
    if not project.detached and task == Path(root) / ".omi" / "tasks" / f"{tid}.md":  # the task branch's copy is committed with the branch
        commit_task_file(Path(root), task, f"chore({tid}): step {core.parse(text).get('step')} {action}")
    return 0


def tasks(root):
    project = state.resolve(root)
    found = {f.stem: core.meta(f) for f in sorted((project.state / ".omi" / "tasks").glob("TASK-*.md"))}
    for tid, wt in core.task_worktrees(project.code).items():
        f = state.task_file(project, tid) if project.detached else Path(wt) / ".omi" / "tasks" / f"{tid}.md"
        if f.exists():
            found[tid] = core.meta(f) | {"worktree": wt}
    return dict(sorted(found.items()))


def glob_prefix(glob):
    return re.split(r"[*?\[]", glob, 1)[0]


def globs_overlap(a, b):
    """# ponytail: compares only the literal prefix before the first wildcard; may report a false overlap, never misses one."""
    for x, y in ((a, b), (b, a)):
        px, py = glob_prefix(x), glob_prefix(y)
        if px == py or (px.startswith(py) and (py != y or py.endswith("/") or px[len(py)] == "/")):
            return True
    return False


def parallel(root, ids):
    """Conflicts that forbid running these tasks in parallel (empty list: ok)."""
    found = tasks(root)
    out = [f"{t}: duplicate id" for t in dict.fromkeys(ids) if ids.count(t) > 1]
    ids = list(dict.fromkeys(ids))
    for tid in ids:
        if tid not in found:
            out.append(f"{tid}: no task file")
        elif found[tid].get("status") not in ("planned", "in-progress"):
            out.append(f"{tid}: status {found[tid].get('status')} (need planned or in-progress)")

    def deps(tid, seen=()):
        for d in core.split(found.get(tid, {}).get("depends")):
            if d not in seen:
                yield d
                yield from deps(d, (*seen, d))
    for i, a in enumerate(ids):
        out += [f"{a} depends on {b}" for b in ids if b != a and b in set(deps(a))]
        for b in ids[i + 1:]:
            out += [f"{a} and {b} scopes overlap: {x} vs {y}" for x in core.split(found.get(a, {}).get("scope"))
                    for y in core.split(found.get(b, {}).get("scope")) if globs_overlap(x, y)]
    return out


def checkpoint(text):
    _, sep, rest = text.partition("## Checkpoint")
    return rest.split("\n## ", 1)[0].strip() if sep else ""


def drift(wt, tid):
    """One line: commits ahead of development, dirty flag, stale-checkpoint warning."""
    ahead = core.git(wt, "rev-list", "--count", "development..HEAD")
    dirty = bool(core.git(wt, "status", "--porcelain"))
    line = f"ahead of development: {ahead if ahead is not None else '?'}, uncommitted: {'yes' if dirty else 'no'}"
    if state.resolve(wt).detached:
        return line  # Detached checkpoints are not part of code history.
    last = core.git(wt, "log", "-1", "--format=%H", "--", f".omi/tasks/{tid}.md")
    after = core.git(wt, "rev-list", "--count", f"{last}..HEAD") if last else ahead
    return line + (" - WARNING checkpoint stale" if after not in (None, "0") else "")


def clip_report(text, limit=2000):
    """Report lines, middle truncated over the limit so the first (DONE/VERDICT) and last (commit) lines survive."""
    text = text.strip()
    if len(text) <= limit:
        return text.splitlines()
    lines = text.splitlines()
    head, tail = [l[:500] for l in lines[:1]], [l[:500] for l in lines[-1:]] if len(lines) > 1 else []
    room, mid = limit - sum(map(len, head + tail)), []
    for l in lines[1:-1]:
        if len(l) + 1 > room:
            break
        mid.append(l)
        room -= len(l) + 1
    return head + mid + ["[... truncated ...]"] + tail


def append_note(task, heading, line):
    """Append text to the task file's `## <heading>` section (created before `## Usage`, else at the end)."""
    if not task.exists():
        return
    text, h = task.read_text(encoding="utf-8"), f"\n## {heading}"
    if h in text:
        head, _, rest = text.partition(h)
        body, sep, tail = rest.partition("\n## ")
        text = f"{head}{h}{body.rstrip()}\n{line}\n" + (f"\n## {tail}" if sep else "")
    elif "\n## Usage" in text:
        head, _, rest = text.partition("\n## Usage")
        text = f"{head.rstrip()}\n\n## {heading}\n{line}\n\n## Usage{rest}"
    else:
        text = f"{text.rstrip()}\n\n## {heading}\n{line}\n"
    task.write_text(text, encoding="utf-8")


USAGE_HEAD = "| role | model | effort | input | output | cache | duration | skills read | verdict |"


def record_usage(task, role, model, effort, nums, seconds, skills="-", verdict="-"):
    """Append one row to the task file's `## Usage` table (created at the end if missing)."""
    if not task.exists():
        return
    cell = lambda v: "n/a" if v is None else str(v)
    row = f"| {role} | {model} | {effort or 'n/a'} | {cell(nums[0])} | {cell(nums[1])} | {cell(nums[2])} | {round(seconds)}s | {skills} | {verdict} |"
    text = task.read_text(encoding="utf-8")
    if "\n## Usage" in text:
        head, _, rest = text.partition("\n## Usage")
        body, sep, tail = rest.partition("\n## ")
        lines = body.split("\n")
        for i, l in enumerate(lines):
            if l.startswith("| role"):
                for col in ("skills read", "verdict"):
                    if col not in l:
                        l += f" {col} |"
                        if i + 1 < len(lines) and lines[i + 1].startswith("|---"):
                            lines[i + 1] += "---|"
                lines[i] = l
        body = "\n".join(lines)
        text = f"{head}\n## Usage{body.rstrip()}\n{row}\n" + (f"\n## {tail}" if sep else "")
    else:
        text = f"{text.rstrip()}\n\n## Usage\n{USAGE_HEAD}\n|---|---|---|---|---|---|---|---|---|\n{row}\n"
    task.write_text(text, encoding="utf-8")


def usage_totals(text):
    """One line for status: summed tokens over the Usage rows and reviewer rounds, or ''."""
    _, sep, rest = text.partition("\n## Usage")
    if not sep:
        return ""
    rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in rest.split("\n## ", 1)[0].splitlines()
            if l.startswith("|") and not l.startswith("|---") and not l.startswith("| role")]
    rows = [r for r in rows if len(r) in (7, 8, 9)]
    tot = [sum(int(r[i]) for r in rows if r[i].isdigit()) if any(r[i].isdigit() for r in rows) else "n/a" for i in (3, 4, 5)]
    return (f"usage: {len(rows)} runs, in {tot[0]} out {tot[1]} cache {tot[2]}, "
            f"review rounds: {sum(r[0] == 'omi-agent-reviewer' and not r[-1].startswith('QUOTA->') for r in rows)}")


def prior_review(text):
    """(earlier reviewer rounds, sha7 of the last one if it failed, repo paths named after the last `Review round`)."""
    rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in text.partition("\n## Usage")[2].splitlines()
            if l.startswith("| omi-agent-reviewer |") and "| QUOTA->" not in l]
    last = re.fullmatch(r"FAIL ([0-9a-f]{7})", rows[-1][-1]) if rows else None
    after = re.split(r"^.*Review round.*$", text.partition("\n## Usage")[0], flags=re.M)[-1] if "Review round" in text else ""
    after = after.split("\n## ", 1)[0]
    return len(rows), last and last.group(1), set(re.findall(r"[\w.-]+(?:/[\w.-]+)+|[\w-]+\.(?:py|md|json|toml|ya?ml|sh|txt|js|ts|cfg|ini)\b", after))
