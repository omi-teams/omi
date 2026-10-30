"""JSON-ready, uncached views of $OMI_STATE; no writes or network operations."""

import re
from pathlib import Path

from ..common import core
from ..project import catalogs, tasks, workflows
from ..state import resolve as state


STATUSES = ("planned", "in-progress", "review", "blocked", "done")


def _name(value: str, project_name: bool = False) -> str:
    pattern = r"[A-Za-z0-9][A-Za-z0-9._-]*" if project_name else r"[A-Za-z0-9_-]+"
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise ValueError(f"invalid name or id: {value!r}")
    return value


def _safe(path: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(state.state_home()):
        raise ValueError(f"path outside OMI_STATE: {path}")
    return resolved


def _root(name: str) -> Path:
    root = _safe(state.state_home() / "projects" / _name(name, project_name=True))
    if not root.is_dir():
        raise FileNotFoundError(root)
    return root


def _read(path: Path) -> str:
    return _safe(path).read_text(encoding="utf-8")


def _files(path: Path, pattern: str) -> list[Path]:
    found = sorted(_safe(path).glob(pattern))
    for file in found:
        _safe(file)
    return found


def _section(text: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return match[1].strip() if match else ""


def _usage(text: str) -> dict:
    rows = []
    for line in _section(text, "Usage").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) in (7, 8, 9) and cells[0] != "role" and not cells[0].startswith("---"):
            rows.append(dict(zip(("role", "model", "effort", "input", "output", "cache", "duration", "skills read", "verdict"), cells)))
    return {"rows": rows, "summary": tasks.usage_totals(text), **_totals(rows)}


def _totals(rows: list[dict]) -> dict:
    return {"runs": len(rows),
            **{key: sum(int(r[key]) for r in rows if r[key].isdigit()) for key in ("input", "output", "cache")},
            "review_rounds": sum(r["role"] == "omi-agent-reviewer" and not r.get("verdict", "").startswith("QUOTA->") for r in rows)}


def task(name: str, id: str) -> dict:
    """Read a task detail. Invalid identifiers/escaping symlinks raise ValueError."""
    root = _root(name)
    text = _read(root / ".omi" / "tasks" / f"{_name(id)}.md")
    return _detail(root, id, text)


def _detail(root: Path, id: str, text: str) -> dict:
    meta = {k: v for k, v in core.parse(text).items() if k != "_text"}
    wid = _name(meta.get("workflow") or workflows.DEFAULT_WORKFLOW)
    path = _safe(root / ".omi" / "workflows" / f"{wid}.md")
    definitions = workflows.workflow_steps(_read(path)) if path.exists() else []
    return {"id": id, "frontmatter": meta, "workflow_steps": definitions,
            "current_step": meta.get("step") or None,
            "goal": _section(text, "Goal"),
            "criteria": [{"text": m[2], "checked": m[1].lower() == "x"}
                         for m in re.finditer(r"^- \[([ xX])\] (.*)$", _section(text, "Acceptance criteria"), re.M)],
            "checkpoint": tasks.checkpoint(text), "steps": _section(text, "Steps"),
            "reports": _section(text, "Reports"), "usage": _usage(text)}


def _plans(root: Path, details: list[dict]) -> list[dict]:
    # Validate paths before the shared parser opens them (including directory symlinks).
    _files(root / ".omi" / "plans", "*.md")
    result = []
    for id, meta in catalogs.load_plans(root, strict=False).items():
        members = [t for t in details if t["frontmatter"].get("plan") == id]
        result.append({k: v for k, v in meta.items() if k != "_text"} |
                      {"id": id, "done": sum(t["frontmatter"].get("status") == "done" for t in members), "total": len(members)})
    return result


def _waiting(root: Path, details: list[dict]) -> list[dict]:
    waiting = []
    done = {t["id"] for t in details if t["frontmatter"].get("status") == "done"}
    next_task = next((t["id"] for t in details if t["frontmatter"].get("status", "planned") == "planned"
                      and set(core.split(t["frontmatter"].get("depends"))) <= done), None)
    for t in details:
        m = t["frontmatter"]
        status, step = m.get("status", "planned"), m.get("step", "")
        reasons = []
        if status == "blocked":
            reasons.append(("blocked", ""))
        if t["id"] == next_task:
            reasons.append(("next_task", ""))
        if status == "in-progress":
            reasons.extend(("next", line.partition(":")[2].strip()) for line in t["checkpoint"].splitlines()
                           if line.startswith("Next:") and line.partition(":")[2].strip())
        if status != "done" and step:
            text = "\n## Steps\n" + t["steps"] + "\n"
            if any(s.get("id") == step and s.get("gate") == "po" for s in t["workflow_steps"]) and tasks.step_states(text).get(step) not in ("done", "skipped"):
                reasons.append(("po_gate", step))
        waiting.extend({"id": t["id"], "reason": reason, "text": text} for reason, text in reasons)
    return waiting


def _sync() -> dict:
    home = state.state_home()
    counts = core.git(home, "rev-list", "--left-right", "--count", "HEAD...@{upstream}")
    ahead, behind = map(int, counts.split()) if counts else (None, None)
    dirty = core.git(home, "--no-optional-locks", "status", "--porcelain")
    return {"ahead": ahead, "behind": behind, "last_commit": core.git(home, "log", "-1", "--format=%H %cI %s"),
            "dirty": bool(dirty) if dirty is not None else None}


def project(name: str) -> dict:
    """Return a dashboard; sync describes the shared state repo, without fetching."""
    root = _root(name)
    details = [_detail(root, f.stem, _read(f)) for f in _files(root / ".omi" / "tasks", "*.md") if f.name != "_template.md" and _name(f.stem)]
    kanban = {status: [] for status in STATUSES}
    for t in details:
        kanban.setdefault(t["frontmatter"].get("status", "planned"), []).append(t)
    activity = []
    for t in details:
        for section in ("steps", "reports"):
            for line in t[section].splitlines():
                if line.strip():
                    stamp = re.search(r"\d{4}-\d\d-\d\d[ T]\d\d:\d\d(?::\d\d)?", line)
                    duration = re.search(r"\b\d+(?:\.\d+)?s\b", line)
                    activity.append({"id": t["id"], "section": section, "text": line,
                                     "time": stamp[0] if stamp else None, "duration": duration[0] if duration else None})
    activity.sort(key=lambda a: a["time"] or "", reverse=True)
    decisions_path = _safe(root / ".omi" / "decisions.md")
    decisions = [line for line in _read(decisions_path).splitlines() if line.startswith("- ")] if decisions_path.exists() else []
    rows = [row for t in details for row in t["usage"]["rows"]]
    waiting = _waiting(root, details)
    # These describe detached project state, like sync; the portable registry
    # stores remote identities, not local code checkout paths.
    return {"name": name, "path": str(root), "branch": core.git(root, "branch", "--show-current") or None,
            "plans": _plans(root, details), "kanban": kanban,
            "task_counts": {status: len(items) for status, items in kanban.items()},
            "po_waiting": waiting, "po_waiting_count": len({item["id"] for item in waiting}),
            "activity": activity, "decisions": sorted(decisions, reverse=True),
            "usage": {"tasks": {t["id"]: t["usage"] for t in details},
                      "models": {model: _totals([r for r in rows if r["model"] == model]) for model in sorted({r["model"] for r in rows})},
                      "totals": _totals(rows)}, "sync": _sync()}


def projects() -> list[dict]:
    """List project summaries in name order; count waiting tasks once each."""
    result = []
    directory = _safe(state.state_home() / "projects")
    if not directory.exists():
        return result
    for path in sorted(directory.iterdir()):
        if _safe(path).is_dir():
            view = project(path.name)
            result.append({"name": path.name, "plans": [p for p in view["plans"] if p["status"] == "active"],
                           "path": view["path"], "branch": view["branch"], "sync": view["sync"],
                           "task_counts": view["task_counts"], "po_waiting_count": view["po_waiting_count"]})
    return result
