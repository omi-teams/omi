"""Step results as comments on the task's pull request (`task/<ID>`); every failure is a warning, never an error."""

import datetime
import re
import shutil
import subprocess

from ..common import core
from ..project import tasks


def _section(text: str, heading: str) -> str:
    return text.partition('\n## ' + heading + '\n')[2].split('\n## ', 1)[0]


def acceptance_body(tid: str, text: str, review_roles: tuple[str, ...]) -> str:
    """Publish task metadata and review verdicts, never raw worker/hook reports."""
    meta = core.parse(text)
    goal = _section(text, 'Goal').strip().split('\n\n', 1)[0]
    summary = goal or 'Complete the reviewed changes and acceptance workflow.'
    files = core.split(meta.get('files'))
    changes = '\n'.join('- ' + path for path in files) or 'Changed paths were not recorded in the task.'
    usage = '\n'.join(line for line in _section(text, 'Usage').splitlines() if line.startswith('|'))
    hosts = '\n'.join(line for line in _section(text, 'Checkpoint').splitlines() if line.startswith('Host:'))
    steps = []
    for line in _section(text, 'Steps').splitlines():
        event = re.match(r'^- [a-z0-9-]+ (?:started|done|skipped|failed) \d{4}-\d\d-\d\d \d\d:\d\d', line)
        if event:
            steps.append(event[0])
        elif line == 'Auto accept: review PASS':
            steps.append(line)
    verdicts, reviewer = [], ''
    for line in _section(text, 'Reports').splitlines():
        entry = re.match(r'^(\d{4}-\d\d-\d\d \d\d:\d\d) (\S+)', line)
        if entry:
            reviewer = f'{entry[1]} {entry[2]}' if entry[2] in review_roles else ''
        verdict = re.fullmatch(r'>\s*VERDICT: (PASS|FAIL)\s*', line)
        if reviewer and verdict:
            verdicts.append(f'{reviewer} VERDICT: {verdict[1]}')
    verification = '\n'.join([usage, hosts, *steps, *verdicts])
    known = _section(text, 'Known issues').strip() or 'None recorded in the task.'
    return tasks.clean_text(f'## Summary\n{tid}: {summary}\n\n## Changes\n{changes}\n\n'
                            '## Not in this PR\nChanges outside the task scope, unrelated work and follow-up tasks.\n\n'
                            f'## Verification\n{verification}\n\n## Known issues\n{known}\n')


def header(step, agent, verdict, when=None):
    """`**Step:** ... · **Agent:** ... · **Time:** ... · **Verdict:** ...`; agent is `role (tool/model/effort)` or `Coordinator`."""
    when = when or f"{datetime.datetime.now():%Y-%m-%d %H:%M}"
    return f"**Step:** {step} · **Agent:** {agent} · **Time:** {when} · **Verdict:** {verdict}"


def post(wt, tid, text):
    """Comment `text` on the open PR of `task/<ID>`; True if posted, False if skipped (no remote or PR) or failed (warns)."""
    if not core.git(wt, "remote"):
        return False
    gh = shutil.which("gh")
    if not gh:
        print("WARNING: gh not found; the step result was not posted to the PR")
        return False
    run = lambda *a, **kw: subprocess.run([gh, "pr", *a], cwd=wt, capture_output=True, encoding="utf-8", errors="replace", **kw)  # noqa: E731
    try:
        if run("view", f"task/{tid}", "--json", "state", "-q", ".state").stdout.strip() != "OPEN":
            return False
        r = run("comment", f"task/{tid}", "--body-file", "-", input=tasks.clean_text(text))
    except OSError as e:
        print(f"WARNING: could not post the step result to the PR: {e}")
        return False
    if r.returncode:
        print(f"WARNING: could not post the step result to the PR: {(r.stderr or r.stdout).strip()}")
    return r.returncode == 0


def post_report(wt, tid, step, role, tool, model, effort, verdict, report):
    return post(wt, tid, header(step, f"{role} ({tool}/{model}/{effort or 'n/a'})", verdict) + "\n\n" + report)


def post_hook(wt, tid, event, res):
    """One short line for a hook result: name, pass/fail, last line of its output."""
    rc, out = res
    last = (out or "").strip().splitlines()[-1:] or ["(no output)"]
    return post(wt, tid, header(f"hook {event}", "omi hook (Docker)", "pass" if rc == 0 else "fail") + f"\n\n{last[0]}")
