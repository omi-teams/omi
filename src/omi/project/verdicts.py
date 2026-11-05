"""Reviewer verdicts (PASS/FAIL) recorded in a task's `## Usage` table."""

import re


def rows(text, role):
    """PASS or FAIL of each of the role's `## Usage` rows, oldest first."""
    table = [[c.strip() for c in l.strip().strip("|").split("|")] for l in text.partition("\n## Usage")[2].split("\n## ", 1)[0].splitlines()
             if l.startswith("|") and not l.startswith("|---") and not l.startswith("| role")]
    return [r[-1].split()[0] for r in table if r[0] == role and r[-1][:4] in ("PASS", "FAIL")]


def last(text, role, sid=None):
    """Latest verdict of the role, else empty; with `sid` only rows after step `sid` last started (`(verdicts: N)` in its log line)."""
    seen = sid and re.findall(rf"^- {re.escape(sid)} started .*?\(verdicts: (\d+)\)", text.partition("\n## Steps\n")[2].split("\n## ", 1)[0], re.M)
    return (rows(text, role)[int(seen[-1]) if seen else 0:] or [""])[-1]
