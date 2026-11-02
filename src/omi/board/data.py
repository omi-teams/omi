"""JSON-ready views of the fetched GitHub state snapshot."""

import hashlib
import json
import re
from datetime import datetime
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


def _inbox(t: dict) -> list[dict]:
    """Open PO requests only; never infer a stop from historical usage totals."""
    if t["status"] == "done":
        return []
    step = t["current_step"]
    log = "\n## Steps\n" + t["steps"] + "\n"
    result = []

    def add(reason: str, text: str, since: str | None = None) -> None:
        result.append({"id": t["id"], "title": t["frontmatter"].get("title", ""),
                       "reason": reason, "text": text, "since": since,
                       "command": f"omi-task {t['id']}"})

    if (step and any(s.get("id") == step and s.get("gate") == "po" for s in t["workflow_steps"])
            and tasks.step_states(log).get(step) not in ("done", "skipped")
            and not tasks.po_approved(log, step)):
        starts = re.findall(rf"^- {re.escape(step)} started (\d{{4}}-\d\d-\d\d \d\d:\d\d(?::\d\d)?)", t["steps"], re.M)
        add("po_gate", f"Duyệt bước {step}", starts[-1] if starts else None)
        result[-1]["gate"] = step

    # Only the latest report can represent an outstanding worker stop. Hooks
    # are validation evidence, not a replacement for the worker's request.
    reports = re.split(r"(?m)^(?=\d{4}-\d\d-\d\d \d\d:\d\d(?::\d\d)? (?!hook ))", t["reports"])
    report = reports[-1] if reports else ""
    stamp = re.match(r"(\d{4}-\d\d-\d\d \d\d:\d\d(?::\d\d)?)", report)
    since = stamp[1] if stamp else None
    later_step = since and any(date > since for date in re.findall(
        r"^- \S+ (?:started|done|skipped) (\d{4}-\d\d-\d\d \d\d:\d\d(?::\d\d)?)", t["steps"], re.M))
    body = "\n".join(line.removeprefix("> ").strip() for line in report.splitlines()[1:])
    checkpoint = t["checkpoint"]
    # Next/Not done are current requests. A bare QUOTA line is emitted by
    # stop_quota; a successful fallback explicitly says it continued.
    current = "\n".join(line for line in checkpoint.splitlines()
                        if re.match(r"(?:Next:|Not done:|NEEDS SCOPE:|QUOTA:)", line))
    rows = t["usage"]["rows"]
    if rows and not rows[-1].get("verdict", "").startswith("QUOTA->"):
        current = "\n".join(line for line in current.splitlines() if not line.startswith("QUOTA:"))
    evidence = current + ("\n" + body if not later_step else "")
    for reason, marker in (("needs_scope", "NEEDS SCOPE"), ("quota", "QUOTA")):
        lines = [line for line in evidence.splitlines() if re.match(
            rf"^(?:(?:Next|Not done):\s*)?{marker}[:\s]", line)]
        lines = [line for line in lines if not re.search(r"continued|rerunning|resolved|scope widened", line, re.I)]
        if lines:
            from_report = lines[-1] in body
            add(reason, lines[-1], since if from_report else None)
            result[-1]["request_marker"] = (since or "") if from_report else hashlib.sha1(lines[-1].encode()).hexdigest()[:12]
    verdicts = [r.get("verdict", "") for r in t["usage"]["rows"] if r["role"] == "omi-agent-reviewer"
                and r.get("verdict", "").startswith(("FAIL", "PASS"))]
    decision = re.search(r"(?:waiting|await|ask|chờ|cần).*(?:PO|decision|quyết định)|(?:PO|decision).*?(?:needed|required|decides)",
                         evidence, re.I)
    # A second reviewer FAIL is itself a stop; real reports don't always say
    # "Waiting for PO decision". A Coordinator's quoted PO instruction resolves it.
    review_stop = (not later_step and not re.search(r"\bPO\s*:", body)
                   and (re.search(r"^\d[^\n]*omi-agent-reviewer[^\n]*:\n", report)
                        and re.search(r"(?:VERDICT:|verdict is unchanged:)\s*FAIL", body, re.I)
                        or re.search(r"^\d[^\n]*Coordinator \(review\) FAIL:", report)))
    if len(verdicts) >= 2 and all(v.startswith("FAIL") for v in verdicts[-2:]) and (decision or review_stop):
        add("review_fail", decision[0] if decision else "Review FAIL ×2; cần PO quyết định", since if not later_step else None)
    return result


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


STALE_DAYS = 3
BEHIND_LIMIT = 20


def _now() -> datetime:
    return datetime.now()


def _stale_days(snap: source.Snapshot, root: Path) -> float:
    """`board_stale_days` from `.omi/config.json`; STALE_DAYS when absent or invalid."""
    path = root / ".omi" / "config.json"
    try:
        days = json.loads(snap.read(path)).get("board_stale_days") if path in snap.paths else None
    except (json.JSONDecodeError, AttributeError):
        return STALE_DAYS
    return days if isinstance(days, (int, float)) and not isinstance(days, bool) and days > 0 else STALE_DAYS


def _alerts(details: list[dict], stale_days: float) -> list[dict]:
    """Stuck-work flags. Activity is the newest Steps/Reports stamp (state only); branch lag is the task's `behind:` field."""
    status = {t["id"]: t["status"] for t in details}
    now, result = _now(), []
    for t in details:
        if t["status"] == "done":
            continue
        m, tid = t["frontmatter"], t["id"]

        def add(kind: str, chip: str, reason: str, action: str) -> None:
            result.append({"id": tid, "title": m.get("title", ""), "kind": kind, "chip": chip, "reason": reason, "action": action})

        stamps = re.findall(r"\d{4}-\d\d-\d\d[ T]\d\d:\d\d", t["steps"] + "\n" + t["reports"])
        if t["status"] == "in-progress" and stamps:
            idle = (now - datetime.fromisoformat(max(stamps))).total_seconds() / 86400
            if idle > stale_days:
                add("stale", "Không hoạt động", f"Đang làm nhưng {int(idle)} ngày chưa có Steps hay commit mới (ngưỡng: {stale_days:g} ngày).",
                    "Hỏi agent phụ trách, hoặc chuyển task về chưa bắt đầu.")
        fails = sum(r["role"] == "omi-agent-reviewer" and r.get("verdict", "").startswith("FAIL") for r in t["usage"]["rows"])
        if fails >= 2:
            add("review_fail", f"Review FAIL ×{fails}", f"Đã bị review FAIL {fails} lần.", "Đọc báo cáo review gần nhất; cân nhắc chia nhỏ task.")
        behind = str(m.get("behind", ""))
        if behind.isdigit() and int(behind) > BEHIND_LIMIT:
            add("behind", "Nhánh tụt hậu", f"Nhánh task chậm {behind} commit so với development (ngưỡng: {BEHIND_LIMIT}).", "Rebase nhánh lên development.")
        blocked = [d for d in core.split(m.get("depends")) if status.get(d) == "blocked"]
        if blocked:
            add("blocked_dep", "Phụ thuộc bị chặn", f"Phụ thuộc {', '.join(blocked)}, task này đang bị chặn.", f"Gỡ chặn {', '.join(blocked)} trước khi bắt đầu.")
    return result


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
            "inbox": [item for t in details for item in _inbox(t)],
            "alerts": _alerts(details, _stale_days(snap, root)),
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


def _tool(row: dict) -> str:
    return "codex" if "(codex)" in row["model"] else "claude"


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

    tasks_ = [{"id": id, "title": meta.get("title", ""), "plan": meta.get("plan") or "—", "tool": ", ".join(sorted({_tool(r) for r in rows})),
               "model": ", ".join(sorted({r["model"] for r in rows})),
               "fails": sum(r["role"] == "omi-agent-reviewer" and r.get("verdict", "").startswith("FAIL") for r in rows), **_row(rows)}
              for id, meta, rows in items]
    priced = bool(prices) and all(t["cost"] is not None for t in tasks_)
    tasks_.sort(key=lambda t: (-(t["cost"] if priced else t["tokens"]), t["id"]))
    for rank, t in enumerate(tasks_, 1):
        t["top"] = rank if rank <= 5 else None
    model_rows = [r for i in items for r in i[2]]
    return snap.response({
        "name": name, "has_prices": bool(prices), "tasks": tasks_,
        "plans": group("plan", lambda i: i[1].get("plan") or "—"),
        "tools": [{"tool": t, **_row([r for r in model_rows if _tool(r) == t])} for t in sorted({_tool(r) for r in model_rows})],
        "models": [{"model": m, **_row([r for r in model_rows if r["model"] == m])} for m in sorted({r["model"] for r in model_rows})],
        "totals": _row(model_rows)})


def _cycles(deps: dict[str, list[str]]) -> tuple[list[list[str]], set[str]]:
    """One cycle (`A → B → A` as [A, B, A]) per strongly connected group, starting at its lowest id, and all cyclic ids."""
    index, low, stack, on, groups = {}, {}, [], set(), []

    def visit(v: str) -> None:
        index[v] = low[v] = len(index)
        stack.append(v)
        on.add(v)
        for w in deps[v]:
            if w not in index:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            group = set()
            while True:
                w = stack.pop()
                on.discard(w)
                group.add(w)
                if w == v:
                    break
            if len(group) > 1 or v in deps[v]:
                groups.append(group)

    for v in sorted(deps):
        if v not in index:
            visit(v)
    result = []
    for group in sorted(groups, key=min):
        start = min(group)
        path, seen = [start], {start}

        def walk(v: str) -> bool:
            for w in sorted(d for d in deps[v] if d in group):
                if w == start:
                    return True
                if w not in seen:
                    seen.add(w)
                    path.append(w)
                    if walk(w):
                        return True
                    path.pop()
            return False

        walk(start)
        # `deps` points at prerequisites; show the chain in blocking order.
        result.append([start, *reversed(path[1:]), start])
    return result, set().union(*groups)


def _graph(items: list[dict]) -> dict:
    """Layered dependency graph of `items` (id, title, status, depends): layers, cycles, critical path."""
    ids = {t["id"] for t in items}
    deps = {t["id"]: sorted(d for d in set(core.split(t["frontmatter"].get("depends"))) if d in ids) for t in items}
    cycles, cyclic = _cycles(deps)
    layer: dict[str, int] = {}

    def depth(id: str) -> int:
        if id not in layer:
            layer[id] = 1 + max((depth(d) for d in deps[id] if d not in cyclic), default=0)
        return layer[id]

    nodes = {t["id"]: t for t in items if t["id"] not in cyclic}
    for id in nodes:
        depth(id)
    status = {t["id"]: t["status"] for t in items}
    last = max(layer.values(), default=0)
    critical = []
    if last:
        id = min(i for i in nodes if layer[i] == last)
        while True:
            critical.append(id)
            before = [d for d in deps[id] if d not in cyclic and layer[d] == layer[id] - 1]
            if not before:
                break
            id = min(before)
        critical.reverse()
    on_path = set(critical)
    blocks = {id: [] for id in nodes}
    for id in sorted(nodes):
        for d in deps[id]:
            if d in blocks:
                blocks[d].append(id)
    out = []
    for id in sorted(nodes, key=lambda i: (layer[i], i)):
        waiting = [d for d in deps[id] if d in nodes and status[d] != "done"]
        out.append({"id": id, "title": nodes[id]["frontmatter"].get("title", ""), "status": status[id], "layer": layer[id],
                    "depends": [d for d in deps[id] if d in nodes], "blocks": blocks[id], "waiting": waiting,
                    "blocked_by": waiting if status[id] == "blocked" else [], "critical": id in on_path})
    edges = [{"from": d, "to": n["id"], "critical": d in on_path and n["id"] in on_path and layer[d] == layer[n["id"]] - 1}
             for n in out for d in n["depends"]]
    return {"empty": not any(deps.values()), "nodes": out, "edges": edges, "cycles": cycles, "critical_path": critical,
            "summary": {"tasks": len(out), "layers": last, "blocked": sum(n["status"] == "blocked" for n in out),
                        "critical_left": sum(status[i] != "done" for i in critical), "critical": len(critical),
                        "cycle_tasks": len(cyclic)}}


def graph(name: str) -> dict:
    """Dependency graphs per plan and for all tasks, from one immutable remote snapshot."""
    snap = source.snapshot()
    view = _project(snap, name)
    items = sorted((t for ts in view["kanban"].values() for t in ts), key=lambda t: t["id"])
    scopes = {"all": _graph(items)} | {p["id"]: _graph([t for t in items if t["frontmatter"].get("plan") == p["id"]])
                                      for p in view["plans"]}
    return snap.response({"name": name, "plans": [{"id": p["id"], "title": p.get("title", ""), "status": p["status"]}
                                                  for p in view["plans"]], "scopes": scopes})


def projects() -> dict:
    """List project summaries and their shared remote source."""
    snap = source.snapshot()
    result = []
    inbox = []
    names = sorted({p.parts[1] for p in snap.paths if len(p.parts) > 2 and p.parts[0] == "projects"})
    for name in names:
        view = _project(snap, name)
        inbox.extend({**item, "project": name} for item in view["inbox"])
        result.append({"name": name, "plans": [p for p in view["plans"] if p["status"] != "done"],
                       "branch": view["branch"],
                       "task_counts": view["task_counts"], "po_waiting_count": view["po_waiting_count"]})
    inbox.sort(key=lambda item: (item["since"] is None, item["since"] or "", item["project"], item["id"], item["reason"]))
    return snap.response({"projects": result, "inbox": inbox})
