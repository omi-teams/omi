"""Workflows: step definitions, validation and CATALOG.md."""

import re
import sys
from pathlib import Path

from . import catalogs
from ..common import core


WORKFLOW_TOKENS = 2000  # per workflow file (bytes/4)
DEFAULT_WORKFLOW = "omi-flow-feature"
STEP_KEYS = ("id", "role", "skills", "input", "output", "gate", "stop")  # optional `stage:` runs read-only review steps together
GATES = ("none", "review", "auto", "po")
COORDINATOR = "coordinator"  # a step the Coordinator does itself (plan, PO acceptance); no role file


def workflows_dir(root):
    d = Path(root) / ".omi" / "workflows"
    return d if any(f.name != "CATALOG.md" for f in d.glob("*.md")) else core.TEMPLATE / "dot-omi" / "workflows"


def workflow_steps(text):
    """Steps from the frontmatter: lines `- id: x | role: r | skills: a, b | input: .. | output: .. | gate: g | stop: ..`
    under `steps:`."""
    front = text.split("---", 2)[1] if text.startswith("---") else ""
    steps, inside = [], False
    for line in front.splitlines():
        if re.match(r"steps\s*:", line):
            inside = True
        elif inside and line.strip().startswith("- "):
            parts = [p.partition(":") for p in line.strip()[2:].split("|")]
            steps.append({k.strip(): v.strip() for k, _, v in parts})
        elif line.strip():
            inside = False
    return steps


def step_skill_ids(root, step, m=None):
    """The step role's default skills, the step's skills and the task's own skills; the role must exist."""
    if step["role"] == COORDINATOR:
        return catalogs.task_skills(step)
    role = catalogs.get_role(root, step["role"])
    own = catalogs.task_skills(m or {}) if role["access"] == "write" else []  # task skills are for the implementer (as in run_role)
    return list(dict.fromkeys([*catalogs.task_skills(role), *catalogs.task_skills(step), *own]))


def validate_workflow(root, f):
    """Problems of one workflow file, as a list of strings (empty = valid)."""
    m = core.meta(f)
    errs = [f"missing frontmatter `{k}`" for k in ("id", "summary") if not m.get(k)]
    if m.get("id") and m["id"] != f.stem:
        errs.append(f"id `{m['id']}` differs from file name")
    if not f.stem.startswith("omi-flow-"):
        errs.append(f"id `{f.stem}` must start with `omi-flow-`")
    steps = workflow_steps(m["_text"])
    if not steps:
        errs.append("no steps under `steps:`")
    seen = set()
    for i, s in enumerate(steps, 1):
        sid = s.get("id") or f"#{i}"
        missing = [k for k in STEP_KEYS if k not in s or (k != "skills" and not s[k])]
        errs += [f"step {sid}: missing `{k}`" for k in missing]
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", sid):
            errs.append(f"step {sid}: id must be lowercase letters, digits and dashes")
        if sid in seen:
            errs.append(f"step {sid}: duplicate id")
        seen.add(sid)
        if s.get("gate") and s["gate"] not in GATES:
            errs.append(f"step {sid}: gate `{s['gate']}` is not one of {'|'.join(GATES)}")
        if "role" not in missing:
            try:
                catalogs.check_skills(root, step_skill_ids(root, s))
            except SystemExit as e:
                errs.append(f"step {sid}: {e}")
    stages = [s.get("stage") for s in steps]
    for name in dict.fromkeys(filter(None, stages)):
        at = [i for i, st in enumerate(stages) if st == name]
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name) or at != list(range(at[0], at[-1] + 1)):
            errs.append(f"stage {name}: lowercase id, steps listed one after another")
        for s in (steps[i] for i in at):
            try:
                read = catalogs.get_role(root, s["role"])["access"] == "read"
            except (SystemExit, KeyError):
                read = False
            if s.get("gate") != "review" or not read:
                errs.append(f"step {s.get('id')}: only read-only review steps share a stage")
    n = core.tokens(f)
    if n > WORKFLOW_TOKENS:
        errs.append(f"{n} tokens, at most {WORKFLOW_TOKENS} per workflow")
    return errs


def stage_of(steps, sid):
    """The steps sharing step `sid`'s `stage:` in workflow order, else just that step ([] for an unknown id)."""
    cur = next((s for s in steps if s.get("id") == sid), None)
    return [s for s in steps if cur.get("stage") and s.get("stage") == cur["stage"]] or [cur] if cur else []


SENSITIVE_SCOPE = (r".*migration.*", r"auth([-_.*].*)?", r"secrets?", r"\.github")  # scope path segments (regex, fullmatch) that want omi-flow-feature-sensitive
FAST_LANE, SMALL_FILES = "omi-flow-bugfix-fast", 3  # the fast lane takes bugs touching at most 3 non-test files


def sensitive_segments(m):
    """Path segments of the task's scope that match SENSITIVE_SCOPE."""
    segs = dict.fromkeys(seg for g in core.split(m.get("scope")) for seg in g.lower().split("/"))
    return [seg for seg in segs if any(re.fullmatch(p, seg) for p in SENSITIVE_SCOPE)]


def task_size(m):
    """Non-test files the task names (`## File plan` paths, else scope entries); None when a scope glob hides the count."""
    plan = re.findall(r"^- (?:edit|create) (\S+)", m.get("_text", "").partition("\n## File plan\n")[2].split("\n## ", 1)[0], re.M)
    paths = plan or core.split(m.get("scope"))
    if not paths or not plan and any(ch in p for p in paths for ch in "*?["):
        return None
    return len([p for p in paths if not re.search(r"(^|/)tests?/|(^|/)test_[^/]*$|_test\.\w+$|\.test\.\w+$", p)])


def warn_lane(m):
    """Warn (never fail) when a small bug outside sensitive scope takes the slow bugfix lane, or sensitive scope the fast lane."""
    size, sensitive = task_size(m), sensitive_segments(m)
    if m.get("workflow") == FAST_LANE and sensitive:
        print(f"WARN: {FAST_LANE} on sensitive scope ({', '.join(sensitive)}) - use omi-flow-bugfix or omi-flow-feature-sensitive")
    elif m.get("workflow") == "omi-flow-bugfix" and m.get("type") == "bug" and size is not None and size <= SMALL_FILES and not sensitive:
        print(f"WARN: bug touching {size} non-test file(s) - consider the fast lane {FAST_LANE}")


def workflow_files(root):
    return [f for f in sorted(workflows_dir(root).glob("*.md")) if f.name != "CATALOG.md"]


def get_workflow(root, wid):
    """Steps of a valid workflow; exits on an unknown or invalid one."""
    files = {f.stem: f for f in workflow_files(root)}
    if wid not in files:
        sys.exit(f"unknown workflow `{wid}`: workflow ids start with omi-flow-; known workflows are "
                 f"{', '.join(files) or 'none'}. Nothing changed.")
    errs = validate_workflow(root, files[wid])
    if errs:
        sys.exit(f"workflow {wid}: " + "; ".join(errs))
    return workflow_steps(core.meta(files[wid])["_text"])


def workflows_catalog(root):
    """Write .omi/workflows/CATALOG.md: `- id: when to use [step > step] [~N tokens]`."""
    lines = ["# Workflow catalog", "", "<!-- generated by `python -m omi workflows`; do not edit -->"]
    for f in workflow_files(root):
        m = core.meta(f)
        order = " > ".join(s.get("id", "?") for s in workflow_steps(m["_text"]))
        lines.append(f"- {f.stem}: {' '.join(m.get('summary', '').split()) or '(no summary)'} [{order}] [~{core.tokens(f)} tokens]")
    out = Path(root) / ".omi" / "workflows" / "CATALOG.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {out} ({len(lines) - 3} workflows)")


def check_all_workflows(root):
    """Validate every workflow and that the catalog lists exactly them; exits non-zero listing all problems."""
    files = workflow_files(root)
    bad = [f"{f.stem}: {e}" for f in files for e in validate_workflow(root, f)]
    cat = workflows_dir(root) / "CATALOG.md"
    listed = set(re.findall(r"^- (\S+?):", cat.read_text(encoding="utf-8"), re.M)) if cat.exists() else set()
    if listed != {f.stem for f in files}:
        bad.append("CATALOG.md is stale; run `python -m omi workflows`")
    if bad:
        sys.exit("workflows check failed:\n" + "\n".join(bad))
    print(f"workflows ok ({len(files)} checked)")
