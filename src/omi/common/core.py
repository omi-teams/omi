"""Shared helpers: package paths, platform, git and worktrees, frontmatter, version, argv flags."""

import importlib.metadata
import os
import re
import subprocess
import sys
import time
import tomllib
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

if os.name == "nt":
    import ctypes
    import msvcrt
else:
    import fcntl


TEMPLATE = Path(__file__).parents[1] / "template"
WINDOWS = sys.platform == "win32"


def write_text(path, text):
    """Write UTF-8 text with LF endings on every OS."""
    Path(path).write_text(text, encoding="utf-8", newline="\n")


def git(cwd, *args):
    r = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, encoding="utf-8", errors="replace")
    return r.stdout.strip() if r.returncode == 0 else None


def split(value):
    return [x.strip() for x in (value or "").split(",") if x.strip()]


def read_task(path):
    """Task file text without a leading UTF-8 BOM."""
    return Path(path).read_text(encoding="utf-8-sig")


def meta(path):
    return parse(read_task(path))


def parse(text):
    """Frontmatter of a task file as a dict, plus the raw text under '_text'."""
    text = text.removeprefix("\ufeff")
    m = {"_text": text}
    if text.startswith("---"):
        key = None
        for line in text.split("---", 2)[1].splitlines():
            item = line.strip()
            if key and item.startswith("- "):  # YAML block list -> comma list
                item = item[2:].split("#")[0].strip()
                m[key] = f"{m[key]}, {item}" if m[key] else item
                continue
            k, sep, value = line.partition(":")
            if sep:
                key = k.strip()
                m[key] = value.split("#")[0].strip()
    return m


def tokens(*files):
    return sum(-(-len(Path(f).read_bytes()) // 4) for f in files)


def version():
    """The one version lives in pyproject.toml; a source checkout wins over (possibly stale) editable-install metadata."""
    pp = Path(__file__).parents[3] / "pyproject.toml"
    if pp.is_file():
        proj = tomllib.loads(pp.read_text(encoding="utf-8")).get("project", {})
        if proj.get("name") == "omi-squad":
            return proj["version"]
    try:
        return importlib.metadata.version("omi-squad")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"  # read-only package mount in a hook container: no pyproject, no dist metadata


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


def pid_alive(pid: object) -> bool:
    """True while process `pid` runs (never signals it: os.kill(pid, 0) would terminate it on Windows)."""
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return False
    if os.name == "nt":
        kernel = ctypes.windll.kernel32
        handle = kernel.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        code = ctypes.c_ulong()
        try:
            return bool(kernel.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == 259  # STILL_ACTIVE
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    try:  # Linux: a killed but unreaped process (zombie) still answers kill 0
        return Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").rsplit(")", 1)[1].split()[0] != "Z"
    except (OSError, IndexError):
        return True


@contextmanager
def file_lock(path: Path, timeout: float) -> Iterator[None]:
    """Hold an exclusive OS lock on `path` (created if missing); TimeoutError when it stays held for `timeout` seconds."""
    # OS locks release on process exit; keep the file so waiters share one inode.
    with Path(path).open("a+", encoding="utf-8", newline="\n") as handle:
        if os.name == "nt" and Path(path).stat().st_size == 0:
            handle.write("\0")
            handle.flush()
        deadline = time.monotonic() + timeout
        while True:
            try:
                if os.name == "nt":
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as exc:
                if time.monotonic() >= deadline:
                    raise TimeoutError(str(exc)) from exc
                time.sleep(0.05)
        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
