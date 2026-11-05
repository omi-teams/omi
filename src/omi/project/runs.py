"""Per-run record in the task file's `## Runs`: what each agent run was given and read."""

from . import tasks

SOURCES = ("role", "task", "step")


def skill_sources(role_ids, task_ids, step_ids):
    """{skill id: first source} over the role defaults, the task's skills and the step's skills."""
    found = {}
    for source, ids in zip(SOURCES, (role_ids, task_ids, step_ids)):
        for sid in ids:
            found.setdefault(sid, source)
    return found


def record_run(task, role, tool, model, effort, step, sources, read, rules, refs):
    """Append one line to `## Runs`; `sources` is {skill id: source}, `read`/`rules`/`refs` are id lists."""
    cells = [role, f"{tool} {model} {effort or 'n/a'}", step or "-",
             "skills: " + (" ".join(f"{s}@{src}" for s, src in sources.items()) or "-"),
             "read: " + (" ".join(read) or "-"), "rules: " + (" ".join(rules) or "-"), "refs: " + (" ".join(refs) or "-")]
    tasks.append_note(task, "Runs", "- " + " | ".join(cells))


def parse_runs(section):
    """Run dicts from the text of a `## Runs` section; lines in another shape are skipped."""
    runs = []
    for line in section.splitlines():
        cells = [c.strip() for c in line.removeprefix("- ").split(" | ")]
        if not line.startswith("- ") or len(cells) != 7 or len(cells[1].split()) != 3:
            continue
        tool, model, effort = cells[1].split()
        lists = [c.partition(": ")[2].split() for c in cells[3:]]
        lists = [[] if x == ["-"] else x for x in lists]
        runs.append({"role": cells[0], "tool": tool, "model": model, "effort": effort, "step": cells[2],
                     "skills": [dict(zip(("id", "source"), s.partition("@")[::2])) for s in lists[0]],
                     "read": lists[1], "rules": lists[2], "references": lists[3]})
    return runs
