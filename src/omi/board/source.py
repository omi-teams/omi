"""Fetch and read immutable origin/main snapshots without touching the checkout."""

import copy
import os
import re
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from ..common import core
from ..state import resolve as state

_LOCK = threading.Lock()
_CACHE = {}
_FETCHES = {}  # home -> {ok, at} of the last completed fetch
_WORKERS = {}  # home -> background fetch thread
_SNAPSHOTS = {}  # home -> latest Snapshot; a poll with an unchanged commit does no git reads
FETCH_TIMEOUT = 15  # seconds; the lock holds other board requests meanwhile


def _repo(url: str) -> str:
    if re.match(r"^[A-Za-z]:[/\\]", url):
        return ""
    if "://" in url:
        parts = urlsplit(url)
        if parts.scheme not in ("https", "http", "ssh", "git"):
            return ""
        return urlunsplit((parts.scheme, parts.netloc.rsplit("@", 1)[-1], parts.path, "", ""))
    match = re.fullmatch(r"(?:[^/@:]+@)?([^/:]+):(.+)", url)
    return f"{match[1]}:{match[2]}" if match else ""


class Snapshot:
    def __init__(self, home: Path, source: dict) -> None:
        self.home = home
        self.source = source.copy()
        tree = core.git(home, "ls-tree", "-rz", "--full-tree", source["sha"])
        if tree is None:
            raise OSError("state snapshot unavailable")
        self.paths = set()
        self._blobs = {}  # shared by copies of this snapshot; filled once under the lock
        self._blobs_lock = threading.Lock()
        for entry in tree.split("\0"):
            if not entry:
                continue
            info, path = entry.split("\t", 1)
            if info.split()[0] in ("100644", "100755"):
                self.paths.add(Path(path))

    def read(self, path: Path) -> str:
        if path not in self.paths:
            raise FileNotFoundError("state file not found")
        with self._blobs_lock:
            if not self._blobs:
                self._blobs.update(self._load())
        if path not in self._blobs:
            raise OSError("state file unavailable")
        return self._blobs[path]

    def _load(self) -> dict[Path, str]:
        """Read every blob through one `git cat-file --batch` process."""
        paths = sorted(self.paths)
        request = "".join(f"{self.source['sha']}:{p.as_posix()}\n" for p in paths)
        try:
            out = subprocess.run(["git", "-C", str(self.home), "cat-file", "--batch"], input=request.encode("utf-8"),
                                 capture_output=True, check=True).stdout
        except (OSError, subprocess.CalledProcessError) as exc:
            raise OSError("state file unavailable") from exc
        blobs, pos = {}, 0
        for path in paths:
            end = out.index(b"\n", pos)
            header = out[pos:end].split()
            pos = end + 1
            if len(header) == 3 and header[1] == b"blob":
                size = int(header[2])
                blobs[path] = out[pos:pos + size].decode("utf-8", errors="replace").strip()
                pos += size + 1
        return blobs

    def files(self, path: Path, pattern: str) -> list[Path]:
        return sorted(p for p in self.paths if p.parent == path and p.match(pattern))

    def root(self, name: str) -> Path:
        root = Path("projects") / name
        if not any(p.is_relative_to(root) for p in self.paths):
            raise FileNotFoundError("project not found")
        return root

    def response(self, value: dict) -> dict:
        # State documents can themselves contain the cache path (e.g. old reports).
        paths = {form for path in (self.home, self.home.resolve())
                 for form in (str(path), path.as_posix(), str(path).replace("/", "\\"), str(path).replace("\\", "/"))}

        def clean(item):
            if isinstance(item, str):
                for path in sorted(paths, key=len, reverse=True):
                    item = item.replace(path, "[state]")
                return item
            if isinstance(item, list):
                return [clean(v) for v in item]
            if isinstance(item, dict):
                return {clean(k): clean(v) for k, v in item.items()}
            return item
        return clean({**value, "source": self.source})


def _fetch(home: Path) -> bool:
    """Fetch origin/main without ever prompting for credentials; False on failure or timeout."""
    try:
        return subprocess.run(["git", "-C", str(home), "fetch", "--no-write-fetch-head", "--no-tags", "origin",
                               "+refs/heads/main:refs/remotes/origin/main"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,  # no pipes: a surviving git-remote-* child would hold them open past the timeout
                              env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"}, timeout=FETCH_TIMEOUT).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _background_fetch(home: Path) -> None:
    ok = _fetch(home)
    with _LOCK:
        _FETCHES[home] = {"ok": ok, "at": datetime.now(timezone.utc).isoformat() if ok else _FETCHES[home]["at"]}


def wait_fetches(timeout: float = FETCH_TIMEOUT + 5) -> None:
    """Join the background fetch threads (tests: a busy repo directory cannot be removed on Windows)."""
    for worker in list(_WORKERS.values()):
        worker.join(timeout)


def version() -> dict:
    """Serve the local origin/main at once; fetch in the background, at most every two seconds."""
    home = state.state_home()
    with _LOCK:
        now = time.monotonic()
        cached = _CACHE.get(home)
        if cached is None or now - cached[0] >= 2:
            last = _FETCHES.setdefault(home, {"ok": False, "at": None})
            sha = core.git(home, "rev-parse", "--verify", "refs/remotes/origin/main^{commit}")
            if not sha:  # nothing local to serve yet: this fetch has to block
                last |= {"ok": _fetch(home)}
                if last["ok"]:
                    last["at"] = datetime.now(timezone.utc).isoformat()
                    sha = core.git(home, "rev-parse", "--verify", "refs/remotes/origin/main^{commit}")
            elif not (_WORKERS.get(home) and _WORKERS[home].is_alive()):
                _WORKERS[home] = threading.Thread(target=_background_fetch, args=(home,), daemon=True)
                _WORKERS[home].start()
            source = {"repo": _repo(core.git(home, "remote", "get-url", "origin") or ""), "sha": sha,
                      "fetched_at": last["at"], "stale": not last["ok"]}
            _CACHE[home] = (time.monotonic(), source)
        if not _CACHE[home][1]["sha"]:
            raise OSError("origin/main unavailable")
        return _CACHE[home][1].copy()


def snapshot() -> Snapshot:
    """Read files from the same revision used by lightweight version requests."""
    home, meta = state.state_home(), version()
    with _LOCK:
        snap = _SNAPSHOTS.get(home)
        if snap is None or snap.source["sha"] != meta["sha"]:
            snap = _SNAPSHOTS[home] = Snapshot(home, meta)
        # Share parsed tree and blobs; only the fetch metadata differs between polls.
        snap = copy.copy(snap)
        snap.source = meta.copy()
        return snap
