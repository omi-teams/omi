"""Task types, the type -> workflow map, the parent/child tree rules and the status derived from children."""

from . import workflows


TYPES = ("milestone", "epic", "fr", "nfr", "task", "bug", "security", "incident", "change", "spike", "chore")
TYPE_WORKFLOWS = {"bug": "omi-flow-bugfix", "security": "omi-flow-feature-sensitive", "incident": "omi-flow-incident",
                  "change": "omi-flow-change-request", "spike": "omi-flow-spike", "chore": "omi-flow-refactor"}  # type -> its workflow
PARENT_TYPES = {"milestone": (), "epic": ("milestone",), "fr": ("epic", "milestone"), "nfr": ("epic", "milestone"),  # child type -> parent types
                "incident": ("milestone", "epic"), "change": ("fr", "nfr", "epic", "milestone")}
CHILD_TYPES = {  # parent type -> other child types it may have; a type missing here is a leaf. Both tables: omi-skill-issue-types
    "milestone": ("epic", "fr", "nfr", "task", "chore", "spike"),
    "epic": ("fr", "nfr", "task", "chore", "spike"),
    "fr": ("task", "spike", "bug", "security"),
    "nfr": ("task", "spike", "bug", "security"),
    "incident": ("bug", "security", "chore"),
    "change": ("task",),
}


def children_map(found):
    """{parent id: [child ids]} for the tasks whose `parent:` exists."""
    kids = {}
    for tid, m in found.items():
        if m.get("parent") in found:
            kids.setdefault(m["parent"], []).append(tid)
    return kids


def fits(typ, ptyp):
    """Whether a `typ` task may sit under a `ptyp` task."""
    return typ in CHILD_TYPES.get(ptyp, ()) or ptyp in PARENT_TYPES.get(typ, ())


def tree_errors(found):
    """Messages naming each task with an unknown `type`, a missing `parent`, a parent of a type the tree table forbids, or a parent cycle."""
    out = []
    for tid, m in found.items():
        typ = m.get("type") or "task"
        if typ not in TYPES:
            out.append(f"{tid}: unknown type `{m['type']}` (use {'|'.join(TYPES)})")
        seen, cur = [tid], m.get("parent")
        if cur and cur not in found:
            out.append(f"{tid}: parent {cur} does not exist")
        elif cur and typ in TYPES and (ptyp := found[cur].get("type") or "task") in TYPES and not fits(typ, ptyp):
            if ptyp in CHILD_TYPES:
                allowed = [p for p in CHILD_TYPES if fits(typ, p)]
                out.append(f"{tid}: `{typ}` cannot be under {cur} (`{ptyp}`); " + (f"parent must be {'|'.join(allowed)}" if allowed else f"`{typ}` has no parent"))
            else:
                out.append(f"{tid}: parent {cur} is a leaf type `{ptyp}` and cannot have children")
        while cur in found:
            if cur in seen:
                out.append(f"{tid}: parent cycle {' -> '.join([*seen, cur])}")
                break
            seen.append(cur)
            cur = found[cur].get("parent")
    return out


def derived_status(found):
    """{id: status}: a task with children gets done/blocked/planned/in-progress from them (recursive), else its own."""
    kids, memo = children_map(found), {}

    def status(tid, seen=()):
        ch = [c for c in kids.get(tid, []) if c not in seen and c != tid]
        if not ch:
            return found[tid].get("status", "planned")
        if tid not in memo:
            sts = [status(c, (*seen, tid)) for c in ch]
            memo[tid] = ("done" if all(x == "done" for x in sts) else "blocked" if "blocked" in sts
                         else "planned" if all(x == "planned" for x in sts) else "in-progress")
        return memo[tid]
    return {tid: status(tid) for tid in found}


def warn_type_workflow(m):
    """Print a warning (never fail) when the task's type and workflow disagree (`omi-flow-feature-sensitive` may also carry a plain task)."""
    typ, wid = m.get("type") or "task", m.get("workflow") or workflows.DEFAULT_WORKFLOW
    owner = next((t for t, w in TYPE_WORKFLOWS.items() if w == wid), None)
    if typ in TYPE_WORKFLOWS and TYPE_WORKFLOWS[typ] != wid or owner and owner != typ and wid != "omi-flow-feature-sensitive":
        print(f"WARN: type `{typ}` does not match workflow {wid}" + (f" (type `{owner}` expected)" if owner else f" (use {TYPE_WORKFLOWS[typ]})"))
