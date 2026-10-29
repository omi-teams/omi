"""omi github: branches and rulesets through the gh CLI."""

import json
import re
import shutil
import subprocess
import sys


def rulesets(checks=()):
    """{name: payload} of the GitHub rulesets omi github applies; checks = required check-run names."""
    def ruleset(name, refs, rules, bypass, target="branch"):
        kind = "heads" if target == "branch" else "tags"
        return {"name": name, "target": target, "enforcement": "active", "bypass_actors": bypass,
                "conditions": {"ref_name": {"include": [f"refs/{kind}/{r}" for r in refs], "exclude": []}},
                "rules": [{"type": t, **({"parameters": p} if p else {})} for t, p in rules]}
    admin = [{"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always"}]
    pr = {"required_approving_review_count": 0, "dismiss_stale_reviews_on_push": False,
          "require_code_owner_review": False, "require_last_push_approval": False,
          "required_review_thread_resolution": False}
    status = [("required_status_checks", {"required_status_checks": [{"context": c} for c in checks],
                                           "strict_required_status_checks_policy": False})] if checks else []
    return {r["name"]: r for r in (
        ruleset("omi-development", ["development"], [("deletion", None), ("non_fast_forward", None)], []),
        ruleset("omi-po-only", ["staging", "main"],
                [("deletion", None), ("non_fast_forward", None), ("update", None),
                 ("pull_request", pr), *status], admin),
        # creating rc-* tags stays allowed (omi-release); moving or deleting them is admin only
        ruleset("omi-tags", ["rc-*", "v*"], [("update", None), ("deletion", None)], admin, "tag"))}


class GhError(SystemExit):
    """gh api failure; status is the HTTP status from gh's own output (never from argv), or None."""
    def __init__(self, msg, status=None):
        super().__init__(msg)
        self.status = status


def gh(*args, body=None):
    r = subprocess.run(["gh", "api", *args, *(["--input", "-"] if body else [])],
                       input=json.dumps(body) if body else None, capture_output=True, encoding="utf-8", errors="replace")
    if r.returncode:
        out = r.stderr.strip() or r.stdout.strip()
        m = re.search(r"HTTP (\d{3})", out)
        raise GhError(f"gh api {' '.join(args)} failed: {out}", int(m.group(1)) if m else None)
    return json.loads(r.stdout) if r.stdout.strip() else None


def ci_checks(repo):
    """Sorted check-run names of the newest development commit (of the last 20) with completed runs.

    [] only if development has none; any other gh error aborts."""
    try:
        commits = gh(f"repos/{repo}/commits?sha=development&per_page=20")
    except GhError as e:
        if e.status == 404:
            return []
        raise SystemExit(f"cannot read CI checks on development; required checks left untouched. {e}")
    for c in commits or []:
        try:
            runs = gh(f"repos/{repo}/commits/{c['sha']}/check-runs?per_page=100")["check_runs"]
        except GhError as e:
            if e.status == 404:
                continue
            raise SystemExit(f"cannot read CI checks on development; required checks left untouched. {e}")
        if any(r.get("status") == "completed" for r in runs):
            return sorted({r["name"] for r in runs})
    return []


def same(live, want):
    """True if live holds everything we send (GitHub adds extra fields); lists compare in any order."""
    if isinstance(want, dict):
        return isinstance(live, dict) and all(k in live and same(live[k], v) for k, v in want.items())
    if isinstance(want, list):
        return isinstance(live, list) and len(live) == len(want) and all(
            any(same(l, w) for l in live) for w in want)
    return live == want


def accounts():
    """(logins, active) from local gh state (no network); None if gh cannot tell."""
    r = subprocess.run(["gh", "auth", "status", "--json", "hosts"], capture_output=True, encoding="utf-8", errors="replace")
    try:
        hs = json.loads(r.stdout)["hosts"].get("github.com", [])
    except (ValueError, KeyError):
        return None
    if r.returncode and hs:
        return None
    return [h["login"] for h in hs], next((h["login"] for h in hs if h.get("active")), "")


def github(po=False):
    if not shutil.which("gh"):
        sys.exit("gh is not installed (https://cli.github.com); omi github needs it.")
    if not po:
        return apply_github()
    before = accounts()
    prev = before[1] if before else ""
    if not prev:
        sys.exit("no active squad gh account (or gh auth status failed); log in as the squad account first. Nothing changed.")
    repo_info()  # squad account: a private repo exits here, before the PO logs in
    try:
        r = subprocess.run(["gh", "auth", "login", "--web", "-h", "github.com"])
        now = accounts()
        if r.returncode:
            sys.exit("gh auth login failed; cleaning up.")
        if now is None:
            sys.exit("cannot read gh accounts after login; cleaning up.")
        if not set(now[0]) - set(before[0]) and now[1] == prev:
            sys.exit(f"logged in as {prev}, the same as the squad account; the PO must log in with their own account. Nothing changed.")
        apply_github()
    finally:
        left = []
        try:
            cur = accounts()
            for u in (set(cur[0]) - set(before[0])) if cur else ():
                try:
                    subprocess.run(["gh", "auth", "logout", "-h", "github.com", "-u", u])
                except BaseException:  # keep going: the switch below must still run
                    pass
        finally:
            try:
                cur = accounts()  # logout already switches back when another account exists
                if not cur or cur[1] != prev:
                    subprocess.run(["gh", "auth", "switch", "-h", "github.com", "-u", prev])
            finally:
                cur = accounts()
                left = sorted(set(cur[0]) - set(before[0])) if cur else ["(unknown: gh auth status failed)"]
                if left:
                    sys.exit(f"WARNING: PO credentials may still be stored in gh: {left}. Run `gh auth logout -u <login>` now, then `gh auth switch -u {prev}`.")
                if cur[1] != prev:
                    sys.exit(f"WARNING: the active gh account is {cur[1] or '(none)'}, not the squad account {prev}. Run `gh auth switch -u {prev}` now.")
                print(f"active gh account: {cur[1]}")


def repo_info():
    """nameWithOwner via the active gh account; exits if the repo is unreadable or private."""
    r = subprocess.run(["gh", "repo", "view", "--json", "nameWithOwner,visibility", "--jq", ".nameWithOwner+\" \"+.visibility"],
                       capture_output=True, encoding="utf-8", errors="replace")
    if r.returncode:
        sys.exit(f"cannot read repo from gh: {r.stderr.strip()}")
    repo, vis = r.stdout.split()
    if vis.upper() == "PRIVATE":
        sys.exit(f"{repo} is private; rulesets need a public repo on the GitHub Free plan. Make it public (or upgrade), then rerun. Nothing changed.")
    return repo


def apply_github():
    repo = repo_info()
    if not gh(f"repos/{repo}")["permissions"]["admin"]:
        sys.exit(f"the gh token has no admin on {repo}; nothing changed. Use an admin token.")
    try:
        gh(f"repos/{repo}/git/ref/heads/staging")
        print("ok     branch staging exists")
    except SystemExit:  # ponytail: any lookup failure counts as missing; POST then reports a real error
        sha = gh(f"repos/{repo}/git/ref/heads/main")["object"]["sha"]
        gh("-X", "POST", f"repos/{repo}/git/refs", body={"ref": "refs/heads/staging", "sha": sha})
        print("create branch staging (from main)")
    checks = ci_checks(repo)
    print(f"checks  required on staging/main: {', '.join(checks)}" if checks else
          "no CI check runs on development yet; staging/main get no required checks. Rerun omi github after CI has run.")
    existing = {x["name"]: x["id"] for x in gh(f"repos/{repo}/rulesets")}
    for name, payload in rulesets(checks).items():
        if name in existing:
            if same(gh(f"repos/{repo}/rulesets/{existing[name]}"), {k: v for k, v in payload.items() if k != "name"}):
                print(f"unchanged ruleset {name}")
                continue
            gh("-X", "PUT", f"repos/{repo}/rulesets/{existing[name]}", body=payload)
            print(f"update ruleset {name}")
        else:
            gh("-X", "POST", f"repos/{repo}/rulesets", body=payload)
            print(f"create ruleset {name}")
    print("WARNING: admins bypass the staging/main rule. If the squad uses an admin account, set it back to Write.")
