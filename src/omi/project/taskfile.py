"""Task file text helpers: frontmatter blocks and the worktree copy sync from development."""
import re

from ..common import core
from ..state import resolve as state


def front_of(text):
    """The raw frontmatter block (between the `---` lines) of a task file, or None."""
    text = text.removeprefix("\ufeff")
    return text.split("---", 2)[1] if text.startswith("---") and text.count("---") >= 2 else None


def key_blocks(lines, key):
    """[(index, [key line + its following `- ` list lines])] for every `key:` in frontmatter lines."""
    found = []
    for i, ln in enumerate(lines):
        if ln.partition(":")[0].strip() == key:
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith("- "):
                j += 1
            found.append((i, lines[i:j]))
    return found


def sync_scope(wt, task, tid):
    """Copy the `scope:` line and the Coordinator-owned sections (Goal, Acceptance criteria, File plan) of the task file
    on development into the worktree's task file when they differ; Checkpoint, Reports and Steps stay as they are."""
    if state.resolve(wt).detached:
        return
    dev = core.git(wt, "show", f"development:.omi/tasks/{tid}.md")
    if not dev or not task.exists():
        return
    block = next((b for _, b in key_blocks((front_of(dev) or "").split("\n"), "scope")), None)
    text = core.read_task(task)
    changed = block is not None and core.split(core.parse(dev).get("scope")) != core.split(core.parse(text).get("scope"))
    if changed:
        head, front, rest = text.split("---", 2)
        lines = front.split("\n")
        old = key_blocks(lines, "scope")
        i, n = (old[0][0], len(old[0][1])) if old else (len(lines) - 1, 0)
        lines[i:i + n] = block
        text = f"{head}---{chr(10).join(lines)}---{rest}"
    synced = []
    for name in ("Goal", "Acceptance criteria", "File plan"):
        sec = lambda t: (re.search(rf"^## {name}[ \t]*\n.*?(?=^## |\Z)", t, re.S | re.M) or [None])[0]
        want, have = sec(dev), sec(text)
        if want is not None and (have is None or want.strip() != have.strip()):
            text = text.replace(have or "## Checkpoint", want.rstrip() + "\n\n" + ("" if have else "## Checkpoint"), 1)  # missing: before Checkpoint
            synced.append(name)
    if changed or synced:
        task.write_text(text, encoding="utf-8", newline="\n")
    if changed:
        print(f"SCOPE SYNCED: {core.parse(dev).get('scope')}")
    if synced:
        print(f"SECTIONS SYNCED: {', '.join(synced)}")
