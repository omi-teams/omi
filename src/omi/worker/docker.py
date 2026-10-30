"""Docker worker: egress proxy and network, container names and argv, images, running workers, clean."""

import contextlib
import datetime
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from ..common import core
from . import creds, session
from ..state import resolve as state


DEFAULT_ALLOW = ["api.anthropic.com"]
TOOL_API_HOST = {"claude": "api.anthropic.com", "codex": "api.openai.com"}
PROXY_PORT = 3128
PROXY_ALIAS = "omi-proxy"  # DNS name on the per-run network; container names can exceed the 63-char DNS label limit


def network_allow(root):
    """Hosts a worker may reach: .omi/config.json "network_allow" (PO-editable) or the model API only."""
    cfg = Path(root) / ".omi" / "config.json"
    try:
        allow = json.loads(cfg.read_text(encoding="utf-8")).get("network_allow", DEFAULT_ALLOW) if cfg.exists() else DEFAULT_ALLOW
    except (json.JSONDecodeError, AttributeError):
        sys.exit('.omi/config.json is not a JSON object. Nothing changed.')
    if not isinstance(allow, list):
        sys.exit('"network_allow" in .omi/config.json must be a list of strings. Nothing changed.')
    for e in allow:
        if not isinstance(e, str) or not re.fullmatch(r"(\*\.)?[a-z0-9]([a-z0-9.-]*[a-z0-9])?(:\d{1,5})?", e):
            sys.exit(f'bad "network_allow" entry {e!r} in .omi/config.json: use host, *.suffix or host:port. Nothing changed.')
    return list(allow)


CHATGPT_HOSTS = ["chatgpt.com"]  # codex with a ChatGPT login talks to this besides api.openai.com


def allow_for(root, *tools, chatgpt=False):
    """network_allow plus each tool's own API host (deduplicated), so a repo config that lists only one still works."""
    extra = CHATGPT_HOSTS if chatgpt and "codex" in tools else []
    return list(dict.fromkeys([*network_allow(root), *(TOOL_API_HOST[t] for t in tools), *extra]))


def prove_rc(out, rc):
    """--prove exit code: non-zero on any FAIL line or when a CLI check never reported PASS."""
    lines = out.splitlines()
    bad = any(l.startswith("FAIL") for l in lines) or not all(any(l.startswith(f"PASS {c} CLI") for l in lines) for c in TOOL_API_HOST)
    return rc or (1 if bad else 0)


class NameTaken(Exception):
    """docker refused a container or network name that another run already holds."""


def name_taken(err, name):
    """True only for Docker's own conflict message for this exact name (not e.g. "port already in use")."""
    return f'The container name "/{name}" is already in use' in err or f"network with name {name} already exists" in err


@contextlib.contextmanager
def egress(main, name, image, allow):
    """Internal docker network plus a CONNECT-only allowlist proxy (docker/proxy.py, no token, no worktree);
    yields (network, proxy host name on that network). What this run created is removed on exit; hosts the proxy refused are reported.
    A name already in use raises NameTaken and removes nothing, so another run's proxy or network is never touched."""
    net, proxy, repo = f"omi-net-{name}", f"{name}-proxy", repo_label(main)
    labels = ["--label", "omi-worker=1", "--label", f"omi-repo={repo}"]
    script = core.TEMPLATE / "docker" / "proxy.py"
    docker = lambda *a: subprocess.run(["docker", *a], capture_output=True, encoding="utf-8", errors="replace")
    logs, made = "", {"net": False, "proxy": False}
    try:
        r = docker("network", "create", "--internal", *labels, net)
        if r.returncode:
            if name_taken(r.stderr, net):
                raise NameTaken(net)
            sys.exit(f"cannot create the worker network: {r.stderr.strip()}. Nothing changed.")
        made["net"] = True
        proxy_labels = [x for k, v in compose_labels(name, "proxy").items() for x in ("--label", f"{k}={v}")]
        for cmd in (["create", "--name", proxy, *labels, *proxy_labels, "--user", "node", "--read-only", "--cap-drop", "ALL",
                     "--security-opt", "no-new-privileges", "-v", f"{script}:/proxy.py:ro", image,
                     "python3", "/proxy.py", *allow],
                    ["network", "connect", "--alias", PROXY_ALIAS, net, proxy], ["start", proxy]):
            r = docker(*cmd)
            if r.returncode:
                if cmd[0] == "create" and name_taken(r.stderr, proxy):
                    raise NameTaken(proxy)
                sys.exit(f"cannot start the egress proxy (docker {cmd[0]}): {r.stderr.strip()}. Nothing changed.")
            if cmd[0] == "create":
                made["proxy"] = True
        for _ in range(50):
            logs = docker("logs", proxy).stdout
            if "omi-proxy ready" in logs:
                break
            time.sleep(0.2)
        else:
            sys.exit("the egress proxy did not start. Nothing changed.")
        yield net, PROXY_ALIAS
    finally:
        if made["proxy"]:
            logs = docker("logs", proxy).stdout or logs
            docker("rm", "-f", proxy)
        if made["net"]:
            docker("network", "rm", net)
        hosts = list(dict.fromkeys(re.findall(r"^BLOCKED (\S+)$", logs, re.M)))
        for h in hosts[:5]:
            print(f'NETWORK BLOCKED: {h} - add to "network_allow" in .omi/config.json')
        if len(hosts) > 5:
            print(f"... and {len(hosts) - 5} more blocked hosts")


def container_name(repo, role, tid=None, tool="claude", model=None, effort=None, now=None, salt=""):
    """<repo>-<task-id>-<role short>-<tool>-<model>-<effort>-<HHMMSS><salt>, limited to Docker's [a-zA-Z0-9_.-]; model/effort `none` for prove.
    salt: a random suffix, only after a name conflict."""
    stamp = (now or datetime.datetime.now()).strftime("%H%M%S") + salt
    model = model or "none"
    if tool == "claude":
        model = re.sub(r"-(\d+)-(\d+)$", r"-\1.\2", model)
    raw = "-".join(p for p in (repo, tid, re.sub(r"^omi-agent-", "", role), None if model.startswith(tool) else tool, model, effort or "none", stamp) if p)
    return re.sub(r"[^a-zA-Z0-9_.-]", "-", raw)


def compose_labels(name, service):
    """Docker Desktop groups containers by the compose project label; one project per run, named after its agent container."""
    return {"com.docker.compose.project": re.sub(r"[^a-z0-9_-]", "-", name.lower()), "com.docker.compose.service": service}


def repo_label(main):
    return re.sub(r"[^a-zA-Z0-9_.-]", "-", main.name.lower())


CACHE_ENV = ("XDG_CACHE_HOME=/cache", "GOCACHE=/cache/go-build", "GOMODCACHE=/work/.omi-cache/go-mod", "GOTMPDIR=/cache",
             "npm_config_cache=/work/.omi-cache/npm", "PIP_CACHE_DIR=/work/.omi-cache/pip", "GOFLAGS=-modcacherw")


def worker_sizes(main):
    """{"cache_mb", "tmp_mb"} kwargs for worker_argv from .omi/config.json "worker" ({"cache_mb": 2048, "tmp_mb": 512} by default)."""
    cfg = Path(main) / ".omi" / "config.json"
    w = (json.loads(cfg.read_text(encoding="utf-8")) if cfg.exists() else {}).get("worker", {})
    sizes = (w.get("cache_mb", 2048), w.get("tmp_mb", 512)) if isinstance(w, dict) else None
    if sizes is None or not all(isinstance(v, int) and not isinstance(v, bool) and v > 0 for v in sizes):
        sys.exit('"worker.cache_mb" and "worker.tmp_mb" in .omi/config.json must be positive integers. Nothing changed.')
    return dict(zip(("cache_mb", "tmp_mb"), sizes))


def worker_argv(wt, image, cmd, name=None, repo=None, labels=None, ro=False, mounts=(), env_names=(creds.TOKEN_ENV,), network=None, proxy=None, offline=False, cache_mb=2048, tmp_mb=512, extra=()):
    """docker run argv: only the worktree is rw, its .git file ro, non-root, no caps, rootfs ro, no socket.
    The token goes in by name only (-e NAME); its value lives in the child env, never in argv.
    network/proxy: the internal network and the egress proxy container; HTTPS_PROXY is the only way out; offline: no network at all."""
    wt = Path(wt)
    url = f"http://{proxy}:{PROXY_PORT}"
    net = ["--network", network, "-e", f"HTTPS_PROXY={url}", "-e", f"HTTP_PROXY={url}",
           "-e", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1"] if network else ["--network", "none"] if offline else []
    return ["docker", "run", "--rm", "-i", *(["--name", name] if name else []), "--label", "omi-worker=1",
            *(["--label", f"omi-repo={repo}"] if repo else []),
            *[x for k, v in (labels or {}).items() for x in ("--label", f"{k}={v}")],
            "--user", "node", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--tmpfs", f"/tmp:rw,noexec,nosuid,size={tmp_mb}m",
            "--tmpfs", f"/home/node:rw,noexec,nosuid,uid=1000,gid=1000,size={tmp_mb}m",
            "--tmpfs", f"/cache:rw,exec,nosuid,uid=1000,gid=1000,size={cache_mb}m",  # exec: compiled test binaries run from here
            *[x for n in env_names for x in ("-e", n)], "-e", "HOME=/home/node",
            *[x for kv in CACHE_ENV for x in ("-e", kv)], *net,
            "-v", f"{wt}:/work{':ro' if ro else ''}", "-v", f"{wt / '.git'}:/work/.git:ro",
            *[x for m in mounts for x in ("-v", f"{m}:ro")], *extra, "-w", "/work", image, *cmd]


def worker_labels(role, task, model, effort):
    return {"omi-role": role, "omi-task": task or "none", "omi-model": model or "none", "omi-effort": effort or "none",
            "omi-started": datetime.datetime.now().isoformat(timespec="seconds")}


def running_workers(main):
    """Rows (task, role, model, effort, started) of this repo's running worker containers; empty without docker."""
    fmt = "\t".join("{{.Label \"%s\"}}" % k for k in ("omi-task", "omi-role", "omi-model", "omi-effort", "omi-started"))
    try:
        r = subprocess.run(["docker", "ps", "--filter", "label=omi-worker=1", "--filter", f"label=omi-repo={repo_label(main)}",
                            "--format", fmt], capture_output=True, encoding="utf-8", errors="replace")
    except OSError:
        return []
    return [l.split("\t") for l in r.stdout.splitlines() if l.count("\t") == 4] if r.returncode == 0 else []


def full_volumes(main):
    """Lines for this repo's running containers whose /cache or /home/node is over 90% full; best effort, silent without docker."""
    out = []
    try:
        r = subprocess.run(["docker", "ps", "--filter", "label=omi-worker=1", "--filter", f"label=omi-repo={repo_label(main)}",
                            "--format", "{{.Names}}"], capture_output=True, encoding="utf-8", errors="replace", timeout=10)
        for name in r.stdout.split() if r.returncode == 0 else []:
            d = subprocess.run(["docker", "exec", name, "df", "-P", "/cache", "/home/node"], capture_output=True, encoding="utf-8", errors="replace", timeout=10)
            full = []
            for l in d.stdout.splitlines()[1:] if d.returncode == 0 else []:
                f = l.split()
                if len(f) >= 6 and f[4].endswith("%") and f[4][:-1].isdigit() and int(f[4][:-1]) > 90 and f[5] in ("/cache", "/home/node"):
                    full.append(f"{f[5]} {f[4]}")
            if full:
                out.append(f"{name}: {', '.join(full)} full; raise worker.cache_mb / worker.tmp_mb in .omi/config.json")
    except (OSError, subprocess.TimeoutExpired):
        pass
    return out


def age(started):
    try:
        secs = int((datetime.datetime.now() - datetime.datetime.fromisoformat(started)).total_seconds())
    except ValueError:
        return "?"
    h, m = divmod(max(secs, 0) // 60, 60)
    return f"{h}h{m:02d}m" if h else f"{m}m"


def print_workers(root):
    project = state.resolve(root)
    rows = running_workers(project.state if project.detached else project.code)
    if rows:
        print("running workers:")
        for task, role, model, effort, started in rows:
            print(f"  {task} {role} {model} {effort} {age(started)}")


def image_repo(main):
    return f"omi-worker-{repo_label(main)}"


def image_tag(main):
    d = main / "docker"
    if not (d / "Dockerfile").exists():
        d = core.TEMPLATE / "docker"
    return d, f"{image_repo(main)}:" + hashlib.sha256((d / "Dockerfile").read_bytes()).hexdigest()[:12]


def old_images(main, keep):
    """Images of this repo's worker other than `keep`."""
    r = subprocess.run(["docker", "images", "--filter", f"label=omi-repo={repo_label(main)}",
                        "--format", "{{.Repository}}:{{.Tag}}"],
                       capture_output=True, encoding="utf-8", errors="replace")
    return [i for i in r.stdout.split() if i != keep and i.startswith(image_repo(main) + ":")]


def ensure_image(main):
    d, tag = image_tag(main)
    if subprocess.run(["docker", "image", "inspect", tag], capture_output=True).returncode:
        r = subprocess.run(["docker", "build", "-t", tag, "--label", "omi-worker=1",
                            "--label", f"omi-repo={repo_label(main)}", str(d)],
                           capture_output=True, encoding="utf-8", errors="replace")
        if r.returncode:
            print(r.stdout, r.stderr, sep="\n", file=sys.stderr)
            sys.exit("docker build failed.")
        for i in old_images(main, tag):
            subprocess.run(["docker", "rmi", i], capture_output=True)
    return tag


def clean(cwd=".", all_images=False):
    """Remove this repo's worker containers, cached engineer sessions and every worker image except the current one (all_images: that too)."""
    main = state.resolve(core.main_checkout(cwd) or Path(cwd).resolve()).state
    session.clear(repo_label(main))
    r = subprocess.run(["docker", "ps", "-a", "-q", "--filter", "label=omi-worker=1",
                        "--filter", f"label=omi-repo={repo_label(main)}"],
                       capture_output=True, encoding="utf-8", errors="replace")
    ids = r.stdout.split()
    if ids:
        subprocess.run(["docker", "rm", "-f", *ids], capture_output=True)
    r = subprocess.run(["docker", "network", "ls", "-q", "--filter", f"label=omi-repo={repo_label(main)}"],
                       capture_output=True, encoding="utf-8", errors="replace")
    nets = r.stdout.split()
    if nets:
        subprocess.run(["docker", "network", "rm", *nets], capture_output=True)
    imgs = old_images(main, None if all_images else image_tag(main)[1])
    for i in imgs:
        subprocess.run(["docker", "rmi", i], capture_output=True)
    print(f"removed {len(ids)} container(s), {len(nets)} network(s), {len(imgs)} image(s)")


def need_docker():
    if not shutil.which("docker") or subprocess.run(["docker", "info"], capture_output=True).returncode:
        sys.exit("Docker is not running; start Docker Desktop and retry. Nothing changed.")
