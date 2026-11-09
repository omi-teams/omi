"""Run limits: the token budget per role and the reviewer's one `AC:` line per acceptance criterion."""

import re
import statistics

from ..project import scope, tasks
from . import tools


CRITERIA_PATTERN = r"^- \[[ xX]\] (.+)$"


def criteria(text: str) -> list[str]:
    """Exact acceptance criterion rows in task order."""
    return re.findall(CRITERIA_PATTERN, text.partition("\n## Acceptance criteria\n")[2].split("\n## ", 1)[0], re.M)


def report_skeleton(text: str, role: str, access: str, step_id: str) -> str:
    """Prefill the parser contract, preserving criterion text (including status symbols)."""
    if access == "write":
        lines = ["DONE | BLOCKED | NEEDS SCOPE", "Files: <files changed>",
                 "Tests: <command, result, skipped checks>", "Open issues: <none or details>",
                 f"{tools.COMMIT_KEY}: <type>(<area>): <summary>"]
        if step_id in tools.REPRODUCE_STEPS:
            lines.append(f"{tools.REPRODUCED_KEY}: <test> failed before the fix")
    elif role in (*tasks.REVIEW_ROLES, "omi-agent-qa-tester"):
        lines = [f"{tools.VERDICT_KEYS[0]}: {' | '.join(tools.VERDICTS)}",
                 *[f"AC: {row} <{'|'.join(tools.AC_STATUSES)}> <evidence>" for row in criteria(text)],
                 "HOST: none", "ROOT: same | new | n/a"]
    else:
        return ""
    return "\n".join(lines)


def skeleton_prompt(text: str, role: str, access: str, step_id: str) -> str:
    """The prompt tail that hands the agent its report skeleton ("" for roles without one)."""
    skeleton = report_skeleton(text, role, access, step_id)
    if not skeleton:
        return ""
    return ("\nReport skeleton: copy these lines into your final report; choose one status and fill the placeholders. "
            "Keep the labels and use bare lines without bullets or backticks.\n"
            + ("Keep criterion text verbatim and in order. Add findings before HOST; replace HOST: none with any host items. "
               "Keep ROOT last. Include every criterion even when this exceeds a template's line limit.\n" if access != "write" else "")
            + skeleton)


def missing_ac(text, report):
    """Acceptance criteria a review report covers with neither an `AC:` line nor its `HOST:` line ([] once it has one line per criterion)."""
    rows = criteria(text)
    acs = [a for l in re.findall(r"^[ \t]*(?:[-*] )?AC: ?.*$", report or "", re.M)
           if not re.match(r"AC\d+\b", a := re.sub(r"^[ \t]*(?:[-*] )?AC: ?", "", l))]  # `AC: AC1 ✓` short forms count as missing
    host = " ".join(re.findall(r"^[ \t]*(?:[-*] )?HOST:?[ \t]+(.+)$", report or "", re.M))
    hosted = [row for row in rows if row in host]
    gap = [row for row in rows if row not in hosted and not any(a.startswith(row) for a in acs)]
    return [] if len(acs) + len(hosted) >= len(rows) else gap


CACHE_WEIGHT = 0.1  # a cache read costs about a tenth of uncached input


def token_count(input_tokens: int | None, cache_tokens: int | None, codex: bool = False) -> int:
    """Input-equivalent tokens: uncached input in full plus cache reads at CACHE_WEIGHT.
    Claude input excludes its cache tokens; Codex input already includes them."""
    used, cache = input_tokens or 0, cache_tokens or 0
    return round((max(used - cache, 0) if codex else used) + cache * CACHE_WEIGHT)


def token_budget(root, role: str, found: dict | None = None, tool: str | None = None) -> int | None:
    """`token_budget` {role: input-equivalent tokens} from .omi/config.json, else 3x the role's last 20 runs' median (of `tool`, when given).
    Units: uncached input plus cache reads at CACHE_WEIGHT (Codex model ends `(codex)`; its input includes cache).
    (`found`: the tasks, read when None); None without a budget or under 5 runs."""
    budget = scope.config(root, "token_budget", {})
    value = budget.get(role) if isinstance(budget, dict) else None
    if isinstance(value, int) and not isinstance(value, bool):
        return value if value > 0 else None
    runs = [token_count(int(r[3]), int(r[5]) if len(r) > 5 and r[5].isdigit() else None, r[1].endswith("(codex)"))
            for m in (tasks.tasks(root) if found is None else found).values()
            for r in tasks.usage_rows(m.get("_text", "")) if r[0] == role and len(r) > 3 and r[3].isdigit()
            and (tool is None or ("codex" if r[1].endswith("(codex)") else "claude") == tool)][-20:]
    return int(3 * statistics.median(runs)) if len(runs) >= 5 else None  # ponytail: a handful of runs is no baseline


def over_budget(text, budget_of):
    """`role input_equivalent>budget` for each Usage row (cache reads at CACHE_WEIGHT)."""
    return [f"{r[0].removeprefix('omi-agent-')} {used}>{b}" for r in tasks.usage_rows(text)
            if len(r) > 3 and r[3].isdigit() and (b := budget_of(r[0], "codex" if r[1].endswith("(codex)") else "claude"))
            and (used := token_count(int(r[3]), int(r[5]) if len(r) > 5 and r[5].isdigit() else None, r[1].endswith("(codex)"))) > b]
