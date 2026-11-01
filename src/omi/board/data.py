"""JSON-ready views of the fetched GitHub state snapshot."""

import json
import re
from pathlib import Path

from ..common import core
from ..project import tasks, workflows
from . import source


STATUSES = ("planned", "in-progress", "review", "blocked", "done")


def _name(value: str, project_name: bool = False) -> str:
    pattern = r"[A-Za-z0-9][A-Za-z0-9._-]*" if project_name else r"[A-Za-z0-9_-]+"
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise ValueError(f"invalid name or id: {value!r}")
    return value


def version(name: str | None = None) -> dict:
    """Return shared fetch metadata without reading or parsing state documents."""
    if name is not None:
        _name(name, project_name=True)
    metadata = source.version()
    if name is not None:
        path = f"projects/{name}"
        tree = core.git(source.state.state_home(), "ls-tree", "-d", "--name-only", metadata["sha"], "--", path)
        if tree is None:
            raise OSError("state tree unavailable")
        if tree != path:
            raise FileNotFoundError("project not found")
    return {"sha": metadata["sha"], "source": metadata}


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
    """Read a task detail. Invalid identifiers raise ValueError; tracked symlinks are excluded."""
    snap = source.snapshot()
    root = snap.root(_name(name, project_name=True))
    text = snap.read(root / ".omi" / "tasks" / f"{_name(id)}.md")
    return snap.response(_detail(snap, root, id, text))


def _detail(snap: source.Snapshot, root: Path, id: str, text: str) -> dict:
    meta = {k: v for k, v in core.parse(text).items() if k != "_text"}
    wid = _name(meta.get("workflow") or workflows.DEFAULT_WORKFLOW)
    path = root / ".omi" / "workflows" / f"{wid}.md"
    definitions = workflows.workflow_steps(snap.read(path)) if path in snap.paths else []
    ph = tasks.phase({**meta, "_text": text}, definitions)
    return {"id": id, "frontmatter": meta, "type": meta.get("type") or "task", "parent": meta.get("parent") or None,
            "children": [], "status": meta.get("status", "planned"), "workflow_steps": definitions,
            "phase": {"key": ph["key"], "label": ph["label"]}, "step_index": ph["step_index"],
            "step_count": ph["step_count"], "review_round": ph["review_round"],
            "current_step": meta.get("step") or None,
            "goal": _section(text, "Goal"),
            "criteria": [{"text": m[2], "checked": m[1].lower() == "x"}
                         for m in re.finditer(r"^- \[([ xX])\] (.*)$", _section(text, "Acceptance criteria"), re.M)],
            "checkpoint": tasks.checkpoint(text), "steps": _section(text, "Steps"),
            "reports": _section(text, "Reports"), "usage": _usage(text)}


def _plans(snap: source.Snapshot, root: Path, details: list[dict]) -> list[dict]:
    result = []
    for path in snap.files(root / ".omi" / "plans", "*.md"):
        if path.name == "CATALOG.md":
            continue
        meta = core.parse(snap.read(path))
        if meta.get("id") != path.stem or not meta.get("title") or meta.get("status") not in ("active", "done"):
            continue
        members = [t for t in details if t["frontmatter"].get("plan") == path.stem]
        result.append({k: v for k, v in meta.items() if k != "_text"} |
                      {"id": path.stem, "status": tasks.plan_status(meta["status"], [t["frontmatter"].get("status") for t in members]), "done": sum(t["frontmatter"].get("status") == "done" for t in members), "total": len(members)})
    return result


def _waiting(root: Path, details: list[dict]) -> list[dict]:
    waiting = []
    done = {t["id"] for t in details if t["status"] == "done"}
    next_task = next((t["id"] for t in details if t["status"] == "planned" and not t["children"]
                      and set(core.split(t["frontmatter"].get("depends"))) <= done), None)
    for t in details:
        m = t["frontmatter"]
        status, step = t["status"], m.get("step", "")
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


def project(name: str) -> dict:
    """Return a dashboard from one immutable remote snapshot."""
    snap = source.snapshot()
    return snap.response(_project(snap, name))


def _project(snap: source.Snapshot, name: str) -> dict:
    root = snap.root(_name(name, project_name=True))
    details = [_detail(snap, root, f.stem, snap.read(f)) for f in snap.files(root / ".omi" / "tasks", "*.md") if f.name != "_template.md" and _name(f.stem)]
    found = {t["id"]: t["frontmatter"] for t in details}
    kids, derived = tasks.children_map(found), tasks.derived_status(found)
    for t in details:
        t |= {"children": kids.get(t["id"], []), "status": derived[t["id"]]}
    kanban = {status: [] for status in STATUSES}
    for t in details:
        kanban.setdefault(t["status"], []).append(t)
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
    decisions_path = root / ".omi" / "decisions.md"
    decisions = [line for line in snap.read(decisions_path).splitlines() if line.startswith("- ")] if decisions_path in snap.paths else []
    rows = [row for t in details for row in t["usage"]["rows"]]
    waiting = _waiting(root, details)
    return {"name": name, "branch": "main",
            "plans": _plans(snap, root, details), "kanban": kanban,
            "task_counts": {status: len(items) for status, items in kanban.items()},
            "po_waiting": waiting, "po_waiting_count": len({item["id"] for item in waiting}),
            "activity": activity, "decisions": sorted(decisions, reverse=True),
            "usage": {"tasks": {t["id"]: t["usage"] for t in details},
                      "models": {model: _totals([r for r in rows if r["model"] == model]) for model in sorted({r["model"] for r in rows})},
                      "totals": _totals(rows)}}


def _prices(snap: source.Snapshot, root: Path) -> dict:
    """Per-model USD per million tokens from `.omi/config.json` `prices`; {} when absent or malformed."""
    path = root / ".omi" / "config.json"
    try:
        prices = json.loads(snap.read(path)).get("prices") if path in snap.paths else None
    except (json.JSONDecodeError, AttributeError):
        return {}
    ok = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0
    return {m: p for m, p in prices.items() if isinstance(p, dict) and ok(p.get("input")) and ok(p.get("output"))
            and ok(p.get("cache", 0))} if isinstance(prices, dict) else {}


def _usd(rows: list[dict], prices: dict) -> float | None:
    """Estimated cost of usage rows; None when no prices map exists or a used model has no price."""
    if not prices:
        return None
    total = 0.0
    for r in rows:
        tokens = _totals([r])
        if not any((tokens["input"], tokens["output"], tokens["cache"])):
            continue
        price = prices.get(r["model"])
        if price is None:
            return None
        total += sum(tokens[k] * price.get(k, 0) for k in ("input", "output", "cache")) / 1e6
    return round(total, 4)


def cost(name: str) -> dict:
    """Token and estimated USD sums per task, plan, tool and model from the `## Usage` tables."""
    snap = source.snapshot()
    root = snap.root(_name(name, project_name=True))
    prices = _prices(snap, root)
    items = []
    for f in snap.files(root / ".omi" / "tasks", "*.md"):
        if f.name == "_template.md" or not re.fullmatch(r"[A-Za-z0-9_-]+", f.stem):
            continue
        text = snap.read(f)
        meta, rows = core.parse(text), _usage(text)["rows"]
        if rows:
            items.append((f.stem, meta, rows))

    def group(label: str, key) -> list[dict]:
        keys = sorted({key(i) for i in items})
        return [{label: k, **_row([r for i in items if key(i) == k for r in i[2]])} for k in keys]

    def _row(rows: list[dict]) -> dict:
        t = _totals(rows)
        return {**t, "tokens": t["input"] + t["output"] + t["cache"], "cost": _usd(rows, prices)}

    tasks_ = [{"id": id, "title": meta.get("title", ""), "plan": meta.get("plan") or "—", "tool": meta.get("tool") or "—",
               "model": ", ".join(sorted({r["model"] for r in rows})),
               "fails": sum(r["role"] == "omi-agent-reviewer" and r.get("verdict", "").startswith("FAIL") for r in rows), **_row(rows)}
              for id, meta, rows in items]
    priced = bool(prices) and all(t["cost"] is not None for t in tasks_)
    tasks_.sort(key=lambda t: (-(t["cost"] if priced else t["tokens"]), t["id"]))
    for rank, t in enumerate(tasks_, 1):
        t["top"] = rank if rank <= 5 else None
    model_rows = [r for i in items for r in i[2]]
    tool = lambda r: "codex" if "(codex)" in r["model"] else "claude"
    return snap.response({
        "name": name, "has_prices": bool(prices), "tasks": tasks_,
        "plans": group("plan", lambda i: i[1].get("plan") or "—"),
        "tools": [{"tool": t, **_row([r for r in model_rows if tool(r) == t])} for t in sorted({tool(r) for r in model_rows})],
        "models": [{"model": m, **_row([r for r in model_rows if r["model"] == m])} for m in sorted({r["model"] for r in model_rows})],
        "totals": _row(model_rows)})


def projects() -> dict:
    """List project summaries and their shared remote source."""
    snap = source.snapshot()
    result = []
    names = sorted({p.parts[1] for p in snap.paths if len(p.parts) > 2 and p.parts[0] == "projects"})
    for name in names:
        view = _project(snap, name)
        result.append({"name": name, "plans": [p for p in view["plans"] if p["status"] != "done"],
                       "branch": view["branch"],
                       "task_counts": view["task_counts"], "po_waiting_count": view["po_waiting_count"]})
    return snap.response({"projects": result})
