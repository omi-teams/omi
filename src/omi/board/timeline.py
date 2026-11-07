"""Task timeline view: `## Steps` events and `## Reports` verdicts as ordered rows."""

import re
from datetime import datetime

STAMP = r"\d{4}-\d\d-\d\d \d\d:\d\d(?::\d\d)?"
EVENT = re.compile(rf"^- (\S+) (started|done|skipped) ({STAMP})")
REPORT = re.compile(rf"^({STAMP}) (.+?):\s*$")
VERDICT = re.compile(r"\b(DONE|PASS|FAIL|BLOCKED|NEEDS SCOPE)\b")


def _when(stamp: str) -> datetime:
    return datetime.fromisoformat(stamp)


def duration(seconds: float) -> str:
    """Vietnamese duration with at most two units: `N giờ M phút`, `N phút M giây`, `N giây`."""
    h, m, s = int(seconds) // 3600, int(seconds) % 3600 // 60, int(seconds) % 60
    units = [(h, "giờ"), (m, "phút")] if h else [(m, "phút"), (s, "giây")] if m else [(s, "giây")]
    return " ".join(f"{n} {unit}" for n, unit in units if n) or "0 giây"


def _rounds(reports: str) -> list[dict]:
    """Agent reports with a stamp; hook output is validation evidence, not a review round."""
    result = []
    for block in re.split(rf"(?m)^(?={STAMP} )", reports):
        head, _, body = block.partition("\n")
        m = REPORT.match(head)
        if not m or m[2].startswith("hook "):
            continue
        body = "\n".join(line.removeprefix("> ") for line in body.splitlines()).strip()
        verdict = VERDICT.search(f"{m[2]} {body.partition(chr(10))[0]}")
        result.append({"stamp": m[1], "at": _when(m[1]), "role": m[2].partition(" (")[0].removeprefix("omi-agent-"),
                       "verdict": verdict[1] if verdict else "", "body": body})
    return result


def build(steps: str, reports: str, now: datetime) -> dict:
    """Rows oldest first. A step row runs from `started` to `done`/`skipped`; other lines become note rows."""
    rows: list[dict] = []
    last = None  # notes carry the stamp of the line before them
    for line in steps.splitlines():
        if not line.strip():
            continue
        m = EVENT.match(line)
        if not m:
            rows.append({"kind": "note", "text": line.strip(), "start": last})
            continue
        name, event, stamp = m.groups()
        last = stamp
        if event == "started":
            rows.append({"kind": "step", "name": name, "start": stamp, "end": None, "state": "running", "rounds": []})
            continue
        open_row = next((r for r in reversed(rows) if r["kind"] == "step" and r["name"] == name and r["end"] is None), None)
        if open_row is None:  # done/skipped without `started`: a zero-length row
            open_row = {"kind": "step", "name": name, "start": stamp, "rounds": []}
            rows.append(open_row)
        open_row |= {"end": stamp, "state": "done" if event == "done" else "skipped"}
    for r in rows:
        if r["kind"] == "step":
            end = _when(r["end"]) if r["end"] else now
            r["seconds"] = max(0, int((end - _when(r["start"])).total_seconds()))
            r["duration"] = duration(r["seconds"])
            r["po"] = bool(re.search(rf"(?m)^(?:- )?PO approval {re.escape(r['name'])}: *\S", steps))
    steps_rows = [r for r in rows if r["kind"] == "step"]
    for rnd in _rounds(reports):
        owner = next((r for r in reversed(steps_rows) if _when(r["start"]) <= rnd["at"]), None)
        if owner is not None:
            owner["rounds"].append({k: v for k, v in rnd.items() if k != "at"} | {"n": len(owner["rounds"]) + 1})
    longest = max((r["seconds"] for r in steps_rows), default=0)
    fails = [rnd for r in steps_rows for rnd in r["rounds"] if rnd["verdict"] == "FAIL"]
    for r in steps_rows:
        r["percent"] = round(r["seconds"] / longest * 100) if longest else 0
        r["fail"] = any(rnd["verdict"] == "FAIL" for rnd in r["rounds"])
        for rnd in r["rounds"]:
            rnd["open"] = rnd is fails[-1] if fails else False
    total = sum(r["seconds"] for r in steps_rows)
    return {"rows": rows, "now": now.strftime("%H:%M"),
            "summary": {"seconds": total, "duration": duration(total), "steps": len(steps_rows),
                        "done": sum(r["state"] in ("done", "skipped") for r in steps_rows),
                        "running": sum(r["state"] == "running" for r in steps_rows),
                        "rounds": sum(len(r["rounds"]) for r in steps_rows), "fails": len(fails)}}
