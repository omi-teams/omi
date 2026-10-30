"""Step results as comments on the task's pull request (`task/<ID>`); every failure is a warning, never an error."""

import datetime
import shutil
import subprocess

from ..common import core


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
        r = run("comment", f"task/{tid}", "--body-file", "-", input=text)
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
    return post(wt, tid, header(f"hook {event}", "Coordinator", "pass" if rc == 0 else "fail") + f"\n\n{last[0]}")
