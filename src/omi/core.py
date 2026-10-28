"""Shared helpers: package paths, platform, git and worktrees, frontmatter, version, argv flags."""

import importlib.metadata
import re
import subprocess
import sys
import tomllib
from pathlib import Path


TEMPLATE = Path(__file__).parent / "template"
WINDOWS = sys.platform == "win32"


def git(cwd, *args):
    r = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, encoding="utf-8", errors="replace")
    return r.stdout.strip() if r.returncode == 0 else None


def split(value):
    return [x.strip() for x in (value or "").split(",") if x.strip()]


def meta(path):
    return parse(path.read_text(encoding="utf-8"))


def parse(text):
    """Frontmatter of a task file as a dict, plus the raw text under '_text'."""
    m = {"_text": text}
    if text.startswith("---"):
        for line in text.split("---", 2)[1].splitlines():
            key, sep, value = line.partition(":")
            if sep:
                m[key.strip()] = value.split("#")[0].strip()
    return m


def tokens(*files):
    return sum(-(-len(Path(f).read_bytes()) // 4) for f in files)


def version():
    """The one version lives in pyproject.toml; a source checkout wins over (possibly stale) editable-install metadata."""
    pp = Path(__file__).parents[2] / "pyproject.toml"
    if pp.is_file():
        proj = tomllib.loads(pp.read_text(encoding="utf-8")).get("project", {})
        if proj.get("name") == "omi-squad":
            return proj["version"]
    return importlib.metadata.version("omi-squad")


def semver(v):
    return tuple(int(n) for n in re.findall(r"\d+", v.split("-")[0].split("+")[0])[:3])


def task_worktrees(root):
    """{task id: worktree path} for every checked-out task/* branch."""
    found = {}
    for block in (git(root, "worktree", "list", "--porcelain") or "").split("\n\n"):
        info = dict(line.split(" ", 1) for line in block.splitlines() if " " in line)
        branch = info.get("branch", "").removeprefix("refs/heads/")
        if branch.startswith("task/"):
            found[branch[5:]] = info["worktree"]
    return found


def main_checkout(wt):
    common = git(wt, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(common).parent if common else None


def flag(rest, name):
    return rest[rest.index(name) + 1] if name in rest[:-1] else None
