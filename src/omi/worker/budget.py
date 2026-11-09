"""Run limits: the token budget per role and the reviewer's one `AC:` line per acceptance criterion."""

import re
import statistics

from ..project import scope, tasks


def missing_ac(text, report):
    """Acceptance criteria a review report covers with neither an `AC:` line nor its `HOST:` line ([] once it has one line per criterion)."""
    rows = re.findall(r"^- \[[ xX]\] (.+)$", text.partition("\n## Acceptance criteria\n")[2].split("\n## ", 1)[0], re.M)
    acs = [a for l in re.findall(r"^[ \t]*(?:[-*] )?AC: ?.*$", report or "", re.M)
           if not re.match(r"AC\d+\b", a := re.sub(r"^[ \t]*(?:[-*] )?AC: ?", "", l))]  # `AC: AC1 ✓` short forms count as missing
    host = " ".join(re.findall(r"^[ \t]*(?:[-*] )?HOST:?[ \t]+(.+)$", report or "", re.M))
    hosted = [row for row in rows if row in host]
    gap = [row for row in rows if row not in hosted and not any(a.startswith(row) for a in acs)]
    return [] if len(acs) + len(hosted) >= len(rows) else gap


def token_budget(root, role, found=None):
    """`token_budget` {role: input tokens} from .omi/config.json, else 3x the median input of the role's last 20 runs
    (`found`: the tasks, read when None); None without a budget or under 5 runs."""
    budget = scope.config(root, "token_budget", {})
    value = budget.get(role) if isinstance(budget, dict) else None
    if isinstance(value, int) and not isinstance(value, bool):
        return value if value > 0 else None
    runs = [int(r[3]) for m in (tasks.tasks(root) if found is None else found).values()
            for r in tasks.usage_rows(m.get("_text", "")) if r[0] == role and len(r) > 3 and r[3].isdigit()][-20:]
    return int(3 * statistics.median(runs)) if len(runs) >= 5 else None  # ponytail: a handful of runs is no baseline


def over_budget(text, budget_of):
    """`role input>budget` for each `## Usage` row whose input tokens pass `budget_of(role)`."""
    return [f"{r[0].removeprefix('omi-agent-')} {r[3]}>{b}" for r in tasks.usage_rows(text)
            if len(r) > 3 and r[3].isdigit() and (b := budget_of(r[0])) and int(r[3]) > b]
