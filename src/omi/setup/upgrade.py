"""omi init and upgrade: template copy and released hashes."""

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath

from ..project import catalogs, workflows
from ..common import core


TOOLS = ("git", "gh", "docker", "claude", "codex")
SHAS = Path(__file__).parents[1] / "template_shas.json"
OMI_REPO = "https://github.com/omi-teams/omi"
UPGRADE_SKIP = (".omi/decisions.md", ".omi/config.json")


def norm_sha(data: bytes) -> str:
    """sha256 of the bytes with CRLF folded to LF, so a Windows checkout hashes like Linux."""
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def template_map(tpl: Path = core.TEMPLATE) -> dict[str, Path]:
    """{project posix path: template file}; dot-xxx dirs become .xxx, generated CATALOG.md files are left out."""
    found = {}
    for src in sorted(Path(tpl).rglob("*")):
        if src.is_dir() or "__pycache__" in src.parts or src.suffix == ".pyc" or src.name == "CATALOG.md":
            continue
        parts = ["." + p[4:] if p.startswith("dot-") else p for p in src.relative_to(tpl).parts]
        found[PurePosixPath(*parts).as_posix()] = src
    return found


def template_shas(tpl: Path = core.TEMPLATE) -> dict[str, str]:
    return {rel: norm_sha(src.read_bytes()) for rel, src in template_map(tpl).items()}


def template_shas_cmd(tpl: str | Path, ver: str) -> None:
    """Maintainer step: record the hashes of a released template (an export of its tag) in template_shas.json."""
    known = json.loads(SHAS.read_text(encoding="utf-8")) if SHAS.is_file() else {}
    known[ver] = template_shas(tpl)
    SHAS.write_text(json.dumps(known, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"template-shas {ver}: {len(known[ver])} files")


def template_regen(repo: str | Path = ".") -> None:
    """Maintainer step for an omi checkout (`regenerate` in omi's own config): rebuild the template's agents and workflows
    CATALOG.md from that checkout's template, then its version's entry in its template_shas.json. Writes only under `repo`."""
    repo = Path(repo).resolve()
    tpl, shas = repo / "src" / "omi" / "template", repo / "src" / "omi" / "template_shas.json"
    ver = re.search(r'^version = "([^"]+)"', (repo / "pyproject.toml").read_text(encoding="utf-8"), re.M)
    if not (tpl / "dot-omi").is_dir() or not shas.is_file() or not ver:
        sys.exit(f"template-regen: {repo} is not an omi checkout (src/omi/template, template_shas.json, pyproject version)")
    with tempfile.TemporaryDirectory() as tmp:
        dot = Path(tmp) / ".omi"
        for kind in ("agents", "workflows"):
            shutil.copytree(tpl / "dot-omi" / kind, dot / kind, ignore=shutil.ignore_patterns("CATALOG.md"))
        shutil.copy(tpl / "dot-omi" / "config.json", dot / "config.json")
        catalogs.agents_catalog(tmp)
        workflows.workflows_catalog(tmp)
        for kind in ("agents", "workflows"):
            shutil.copy(dot / kind / "CATALOG.md", tpl / "dot-omi" / kind / "CATALOG.md")
    known = json.loads(shas.read_text(encoding="utf-8"))
    known[ver[1]] = template_shas(tpl)
    shas.write_text(json.dumps(known, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"template-regen {ver[1]}: catalogs and {len(known[ver[1]])} template hashes")


def read_manifest(target: str | Path) -> dict[str, str]:
    f = Path(target) / ".omi" / "manifest.json"
    if not f.is_file():
        return {}
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        data = None
    if not isinstance(data, dict) or not isinstance(data.get("files", {}), dict):
        print(f"warning: invalid manifest {f}; treating as empty")
        return {}
    return data.get("files", {})


def write_manifest(target: str | Path, files: dict[str, str]) -> None:
    f = Path(target) / ".omi" / "manifest.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"version": core.version(), "files": dict(sorted(files.items()))}, indent=2) + "\n", encoding="utf-8", newline="\n")


def released_shas() -> dict[str, set[str]]:
    """{project path: shas of every released template version}; read once per run."""
    known = json.loads(SHAS.read_text(encoding="utf-8")) if SHAS.is_file() else {}
    found = {}
    for files in known.values():
        for rel, sha in files.items():
            found.setdefault(rel, set()).add(sha)
    return found


def backfill(rel: str, sha: str, current: str, released: dict[str, set[str]]) -> str | None:
    """The manifest sha for a file that has none: its own sha when it is a pristine current or released template."""
    return sha if sha == current or sha in released.get(rel, ()) else None


def ensure_gitattributes(target: Path) -> None:
    """Create the project's line-ending policy only when absent."""
    attrs = target / ".gitattributes"
    if upgrade_write_safe(target, ".gitattributes") and not attrs.exists():
        attrs.write_text("* text=auto eol=lf\n", encoding="utf-8", newline="\n")
        print("create .gitattributes (* text=auto eol=lf)")


def ensure_gitignore(target: Path, *, detached: bool = False) -> None:
    """Ignore caches and detached upgrade candidates without duplicating entries."""
    if not upgrade_write_safe(target, ".gitignore"):
        return
    ignore = target / ".gitignore"
    lines = ignore.read_text(encoding="utf-8").splitlines() if ignore.exists() else []
    for name in ("__pycache__", ".omi-cache"):
        if not {name, name + "/", "/" + name + "/"} & set(lines):
            lines.append(name + "/")
            ignore.write_text("".join(line + "\n" for line in lines), encoding="utf-8", newline="\n")
            print(f"update .gitignore ({name}/)")
    if detached and "*.omi-new" not in lines:
        lines.append("*.omi-new")
        ignore.write_text("".join(line + "\n" for line in lines), encoding="utf-8", newline="\n")
        print("update .gitignore (*.omi-new)")


def host_cannot_run(target: Path) -> bool:
    """Stacks that need the worker image to test: Node dependencies or a Docker-based setup (`docker/`, compose file)."""
    return any(next(target.glob(pat), None) is not None for pat in ("package.json", "docker", "docker-compose*", "compose.y*ml"))


def init(target: str | Path = ".", *, detached: bool = False) -> None:
    target = Path(target).resolve()
    manifest_safe = upgrade_write_safe(target, ".omi/manifest.json")
    files = read_manifest(target) if manifest_safe else {}
    current, released = template_shas(), released_shas()
    worker_stack = host_cannot_run(target)  # before the template adds its own docker/
    for rel, src in template_map().items():
        if detached and (rel == "AGENTS.md" or rel.startswith(".claude/")):
            continue
        if not upgrade_write_safe(target, rel):
            continue
        dst = target.joinpath(*rel.split("/"))
        if dst.exists():
            print(f"skip   {rel} (exists)")
            if rel not in files and (b := backfill(rel, norm_sha(dst.read_bytes()), current[rel], released)):
                files[rel] = b
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        files[rel] = current[rel]
        print(f"create {rel}")
        if rel == ".omi/config.json" and worker_stack:
            cfg = json.loads(dst.read_text(encoding="utf-8"))
            cfg["review_test_in_worker"] = True
            dst.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8", newline="\n")
            files[rel] = norm_sha(dst.read_bytes())
    if manifest_safe:
        write_manifest(target, files)
    if upgrade_write_safe(target, ".omi/version"):
        (target / ".omi" / "version").write_text(core.version() + "\n", encoding="utf-8", newline="\n")
        print(f"stamp  .omi/version ({core.version()})")
    ensure_gitattributes(target)
    ensure_gitignore(target)
    fill_host_test(target, detached=detached)
    for catalog in (catalogs.skills_catalog, catalogs.agents_catalog, workflows.workflows_catalog, catalogs.rules_catalog, catalogs.references_catalog, catalogs.plans_catalog):
        catalog(target)
    if not detached and not (target / ".git").exists():
        subprocess.run(["git", "init", "-q", "-b", "main", str(target)], check=True)
        print("git init (branch main)")
    print("tools: " + ", ".join(f"{t} {'ok' if shutil.which(t) else 'MISSING'}" for t in TOOLS))
    print("next: open Claude Code or Codex here and type omi-idea")


def fill_host_test(target: Path, *, detached: bool = False) -> None:
    """Set an empty `host_test` to run docker/host-test.sh when the project (or its detached state) holds that script."""
    cfg, script = target / ".omi" / "config.json", target / "docker" / "host-test.sh"
    if not script.is_file() or not cfg.is_file() or not upgrade_write_safe(target, ".omi/config.json"):
        return
    data = json.loads(cfg.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("host_test"):
        return
    data["host_test"] = f'sh "{script.as_posix()}"' if detached else "sh docker/host-test.sh"  # host tests run in the task worktree
    cfg.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"host_test: {data['host_test']}")


def merge_keys(old: dict, new: dict) -> dict:
    """`old` plus every key `new` has and `old` lacks (recursively); existing values stay."""
    for k, v in new.items():
        if k not in old:
            old[k] = v
        elif isinstance(old[k], dict) and isinstance(v, dict):
            merge_keys(old[k], v)
    return old


def protected(rel: str) -> bool:
    if rel in UPGRADE_SKIP:
        return True
    if rel.startswith(".omi/tasks/"):
        return rel != ".omi/tasks/_template.md"
    return rel.startswith(".omi/plans/PLAN-") and rel != ".omi/plans/PLAN-000.md"


def upgrade_write_safe(target: Path, rel: str, quiet: bool = False) -> bool:
    """Skip links (including parent directories) and destinations outside the project; `quiet` prints nothing."""
    dst = target / rel
    if (any(p.is_symlink() for p in (dst, *dst.parents) if p.is_relative_to(target))
            or not dst.resolve().is_relative_to(target)):
        if not quiet:
            print(f"skip (symlink): {rel}")
        return False
    return True


def stale_template_hint(target: str | Path, *, detached: bool = False) -> None:
    """Report manifest-recorded files that apply can safely update between releases."""
    target = Path(target).resolve()
    if not upgrade_write_safe(target, ".omi/manifest.json", True):
        return
    files = read_manifest(target)
    if not files:
        return
    count = 0
    for rel, src in template_map().items():
        base = files.get(rel)
        if not base or protected(rel) or (detached and (rel == "AGENTS.md" or rel.startswith(".claude/"))):
            continue
        if norm_sha(src.read_bytes()) == base or not upgrade_write_safe(target, rel, True):
            continue
        dst = target / rel
        if dst.is_file() and norm_sha(dst.read_bytes()) == base:
            count += 1
    if count:
        print(f"{count} unmodified template files are stale; run `python -m omi upgrade --apply`")


def project_json(project) -> Path:
    """Project settings: the detached manifest, else .omi/project.json."""
    return project.state / "project.json" if project.detached else project.state / ".omi" / "project.json"


def dockerfile_hint(project) -> list[str]:
    """Lines for `omi status` while docker/Dockerfile differs from a template the PO/Coordinator has not reviewed."""
    dockerfile, template = (project.state / "docker" / "Dockerfile").resolve(), core.TEMPLATE / "docker" / "Dockerfile"
    sha = norm_sha(template.read_bytes())
    try:
        reviewed = json.loads(project_json(project).read_text(encoding="utf-8")).get("dockerfile_reviewed")
    except (OSError, ValueError, AttributeError):
        reviewed = None
    if not dockerfile.is_file() or norm_sha(dockerfile.read_bytes()) == sha or reviewed == sha:
        return []
    return [f"docker/Dockerfile differs from the omi {core.version()} template; review it (omi init never overwrites it)",
            f"  see the diff: git diff --no-index {template} {dockerfile}\n  merge by hand; omi init and upgrade never overwrite it",
            "  reviewed? `python -m omi dockerfile reviewed` (warns again when the template changes)"]


def dockerfile_reviewed(project) -> None:
    """`omi dockerfile reviewed`: store the current template's sha so status stops repeating the Dockerfile warning."""
    path = project_json(project)
    try:
        data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    except ValueError as exc:
        sys.exit(f"invalid {path}: {exc}. Nothing changed.")
    if not isinstance(data, dict):
        sys.exit(f"invalid {path}: expected a JSON object. Nothing changed.")
    data["dockerfile_reviewed"] = norm_sha((core.TEMPLATE / "docker" / "Dockerfile").read_bytes())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Dockerfile review recorded in {path}; status warns again when the omi template changes")


def upgrade_apply(target: str | Path = ".", *, detached: bool = False) -> int:
    target = Path(target).resolve()
    # parse the project config before any file changes, so a broken one leaves the project untouched
    cfg = target / ".omi" / "config.json"
    cfg_safe = upgrade_write_safe(target, ".omi/config.json")
    try:
        old_cfg = json.loads(cfg.read_text(encoding="utf-8")) if cfg_safe and cfg.is_file() else None
        if cfg_safe and cfg.is_file() and not isinstance(old_cfg, dict):
            sys.exit(f"invalid JSON in {cfg}: expected an object; fix it, nothing was changed")
    except json.JSONDecodeError as e:
        sys.exit(f"invalid JSON in {cfg}: {e}; fix it, nothing was changed")
    manifest_safe = upgrade_write_safe(target, ".omi/manifest.json")
    files = read_manifest(target) if manifest_safe else {}
    current, released = template_shas(), released_shas()
    counts = {"created": 0, "updated": 0, "kept": 0}
    for rel, src in template_map().items():
        if detached and (rel == "AGENTS.md" or rel.startswith(".claude/")):
            continue
        if protected(rel):
            continue
        if not upgrade_write_safe(target, rel):
            continue
        dst = target.joinpath(*rel.split("/"))
        new = src.read_bytes()
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(new)
            files[rel] = current[rel]
            counts["created"] += 1
            print(f"create {rel}")
            continue
        sha = norm_sha(dst.read_bytes())
        base = files.get(rel) or backfill(rel, sha, current[rel], released)
        if sha == current[rel]:
            files[rel] = sha
        elif base == sha:
            dst.write_bytes(new)
            files[rel] = current[rel]
            counts["updated"] += 1
            print(f"update {rel}")
        else:
            if upgrade_write_safe(target, rel + ".omi-new"):
                candidate = dst.with_name(dst.name + ".omi-new")
                stale = candidate.exists()
                candidate.write_bytes(new)
                if detached:
                    print(f"review {rel}.omi-new (Coordinator: merge by hand)")
                if stale:
                    print(f"replaced stale {rel}.omi-new")
            counts["kept"] += 1
            print(f"kept (modified): {rel}")
    tpl_cfg = json.loads(template_map()[".omi/config.json"].read_text(encoding="utf-8"))
    if cfg_safe:
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text(json.dumps(merge_keys(old_cfg, tpl_cfg) if old_cfg is not None else tpl_cfg, indent=2) + "\n", encoding="utf-8", newline="\n")
    if manifest_safe:
        write_manifest(target, files)
    if upgrade_write_safe(target, ".omi/version"):
        (target / ".omi" / "version").write_text(core.version() + "\n", encoding="utf-8", newline="\n")
    for kind, catalog in (("skills", catalogs.skills_catalog), ("agents", catalogs.agents_catalog), ("workflows", workflows.workflows_catalog),
                          ("rules", catalogs.rules_catalog), ("references", catalogs.references_catalog), ("plans", catalogs.plans_catalog)):
        if upgrade_write_safe(target, f".omi/{kind}/CATALOG.md"):
            catalog(target)
    ensure_gitattributes(target)
    ensure_gitignore(target, detached=detached)
    fill_host_test(target, detached=detached)
    print(f"upgrade {core.version()}: {counts['created']} created, {counts['updated']} updated, {counts['kept']} kept (see *.omi-new)")
    return 0


def valid_repo(repo: object) -> bool:
    """https://, ssh:// or git@host:path; no whitespace and no leading `-`, so git and pip never read it as an option."""
    return isinstance(repo, str) and bool(re.fullmatch(r"(?:https|ssh)://[^\s-]\S*|\w[\w.-]*@\w[\w.-]*:\S+", repo))


def omi_repo(root: str | Path = ".") -> str:
    cfg = Path(root) / ".omi" / "config.json"
    try:
        data = json.loads(cfg.read_text(encoding="utf-8")) if cfg.is_file() else {}
    except json.JSONDecodeError as e:
        sys.exit(f"invalid JSON in {cfg}: {e}")
    if not isinstance(data, dict):
        sys.exit(f"invalid JSON in {cfg}: expected an object; fix it, nothing was changed")
    repo = data.get("omi_repo", OMI_REPO)
    if not valid_repo(repo):
        sys.exit(f"invalid omi_repo in {cfg}: {repo!r} (use https://, ssh:// or git@host:path)")
    return repo


def release_tag(tag: str) -> bool:
    """Release tags use vX.Y.Z with major < 1000; vYYYY.MM.DD tags are dates."""
    return bool(re.fullmatch(r"v\d+\.\d+\.\d+", tag)) and core.semver(tag)[0] < 1000


def latest_tag(repo: str) -> str | None:
    """Highest vX.Y.Z tag of the remote (SemVer order; date tags and rc tags are ignored)."""
    r = subprocess.run(["git", "ls-remote", "--tags", "--", repo], capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        sys.exit(f"git ls-remote failed: {r.stderr.strip()}")
    tags = set(re.findall(r"refs/tags/(v\d+\.\d+\.\d+)$", r.stdout, re.M))
    return max((tag for tag in tags if release_tag(tag)), key=core.semver, default=None)


def upgrade_cmd(rest: list[str], root: str | Path = ".", *, detached: bool = False) -> int:
    requested = core.flag(rest, "--to")
    if "--to" in rest and (not requested or not release_tag(requested)):
        sys.exit("usage: omi upgrade [--check | --to vX.Y.Z]")
    if "--apply" in rest:
        return upgrade_apply(root, detached=detached)
    repo = omi_repo(root)
    if repo != OMI_REPO:
        if "--check" in rest:
            print(f"repo: {repo} (not the default)")
        elif core.flag(rest, "--repo") != repo:
            sys.exit(f"omi_repo is not the default; confirm with --repo {repo}")
    latest = latest_tag(repo) if not requested or "--check" in rest else requested
    if not latest:
        sys.exit(f"no vX.Y.Z tag in {repo}")
    if "--check" in rest:
        print(f"omi {core.version()} -> {latest[1:]}" if core.semver(latest) > core.semver(core.version()) else "up to date")
        stale_template_hint(root, detached=detached)
        return 0
    tag = requested or latest
    if "://" not in repo:
        repo = "ssh://" + repo.replace(":", "/", 1)
    rc = subprocess.run([sys.executable, "-m", "pip", "install", "--user", "--upgrade", f"git+{repo}@{tag}"]).returncode
    return rc or subprocess.run([sys.executable, "-m", "omi", "upgrade", "--apply"]).returncode
