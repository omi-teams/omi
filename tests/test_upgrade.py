import os
import io
import shutil
import json
import contextlib
import importlib.metadata
import importlib.util
import tomllib
import subprocess
import sys
import tempfile
from pathlib import Path
from helpers import omi


def test_version_stamp_package_hook():
    import fnmatch, glob
    want = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    assert want == "0.5.0" and omi.common.core.version() == want
    real = importlib.metadata.version
    importlib.metadata.version = lambda n: "9.9.9"
    try:
        assert omi.common.core.version() == want  # source checkout: pyproject.toml beats stale metadata
        real_file = omi.common.core.__file__
        with tempfile.TemporaryDirectory() as d:
            omi.common.core.__file__ = str(Path(d) / "a" / "b" / "omi" / "core.py")  # no pyproject next to the code
            try:
                assert omi.common.core.version() == "9.9.9"  # installed: package metadata
            finally:
                omi.common.core.__file__ = real_file
    finally:
        importlib.metadata.version = real

    def missing(n):
        raise importlib.metadata.PackageNotFoundError(n)
    importlib.metadata.version = missing
    try:
        assert omi.common.core.version() == want  # source checkout: pyproject.toml
        buf = io.StringIO()
        buf.reconfigure = lambda **kw: None
        with contextlib.redirect_stdout(buf):
            omi.app.cli.main(["--version"])
            omi.app.cli.main(["version"])
        assert buf.getvalue() == f"omi {want}\nlatest: python -m omi upgrade --check\n" * 2
        assert "how to check for a newer one" in omi.app.cli.USAGE
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            omi.setup.upgrade.init(root)
            assert (root / ".omi" / "version").read_text().strip() == want
            (root / ".omi" / "version").write_text("0.1.0\n")
            omi.setup.upgrade.init(root)
            assert (root / ".omi" / "version").read_text().strip() == want
            def st():
                b = io.StringIO()
                with contextlib.redirect_stdout(b):
                    omi.app.cli.status(root)
                return b.getvalue()
            out = st()
            assert f"omi {want} (project {want})" in out and "upgrade --apply" not in out
            (root / ".omi" / "version").write_text("0.1.0\n")
            out = st()
            assert f"omi {want} (project 0.1.0)" in out and f"run `python -m omi upgrade --apply` to bring the project files to omi {want}" in out
            omi.setup.upgrade.upgrade_apply(root)
            assert (root / ".omi" / "version").read_text().strip() == want
            (root / ".omi" / "version").unlink()
            assert "upgrade --apply" in st()
    finally:
        importlib.metadata.version = real
    assert omi.common.core.semver("0.10.0") > omi.common.core.semver("0.9.5")
    # package-data globs cover every template file (checked on a temp copy, never write in the repo)
    cfg = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["tool"]["setuptools"]
    pats, excl = cfg["package-data"]["omi"], cfg["exclude-package-data"]["omi"]
    with tempfile.TemporaryDirectory() as tmp:
        pkg = Path(tmp) / "omi"
        shutil.copytree(omi.common.core.TEMPLATE, pkg / "template")
        pyc = pkg / "template" / "docker" / "__pycache__"
        pyc.mkdir(exist_ok=True)
        (pyc / "x.pyc").write_bytes(b"")
        covered = {Path(p) for pat in pats for p in glob.glob(str(pkg / pat), recursive=True)}
        covered = {p for p in covered if not any(fnmatch.fnmatch(p.relative_to(pkg).as_posix(), e) for e in excl)}
        files = {p for p in (pkg / "template").rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
        real = omi.common.core.TEMPLATE
        omi.common.core.TEMPLATE = pkg / "template"
        try:
            with tempfile.TemporaryDirectory() as d, contextlib.redirect_stdout(io.StringIO()):
                omi.setup.upgrade.init(d)
                assert not list(Path(d).rglob("__pycache__")) and not list(Path(d).rglob("*.pyc"))
        finally:
            omi.common.core.TEMPLATE = real
        assert pyc / "x.pyc" not in covered and (pkg / "template" / "docker" / "proxy.py") in covered
        assert files <= covered, sorted(files - covered)
        assert any(p.suffix == ".sh" for p in files) and any("references" in p.parts and "skills" in p.parts for p in files)
    # post-run.sh runs the configured test command first
    with tempfile.TemporaryDirectory() as d:
        omi.setup.upgrade.init(d)
        hook = str(Path(d) / ".omi" / "hooks" / "post-run.sh")
        (Path(d) / "go.mod").write_text("module x\n")  # would pick go test without config
        cfg = Path(d) / ".omi" / "config.json"
        c = json.loads(cfg.read_text())
        c["test"] = "exit 7"
        cfg.write_text(json.dumps(c))
        assert subprocess.run([omi.worker.run.host_bash() or "sh", hook], cwd=d, env={**os.environ, "OMI_PROJECT_STATE": d}).returncode == 7


def test_upgrade():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        omi.setup.upgrade.init(root)
        man = json.loads((root / ".omi" / "manifest.json").read_text(encoding="utf-8"))
        assert man["version"] == omi.common.core.version() and man["files"][".claude/settings.json"] == omi.setup.upgrade.template_shas()[".claude/settings.json"]
        # a project without manifest: pristine files are backfilled, edited ones are not
        (root / ".omi" / "manifest.json").unlink()
        (root / "docker" / "prove.sh").write_bytes((root / "docker" / "prove.sh").read_bytes().replace(b"\n", b"\r\n"))
        (root / "AGENTS.md").write_text("mine\n", encoding="utf-8")
        omi.setup.upgrade.init(root)
        files = json.loads((root / ".omi" / "manifest.json").read_text(encoding="utf-8"))["files"]
        assert "docker/prove.sh" in files and "AGENTS.md" not in files
        # a released template (fake tag dir) counts as pristine
        old = root / "oldtpl"
        shutil.copytree(omi.common.core.TEMPLATE, old, ignore=shutil.ignore_patterns("__pycache__"))
        (old / "docker" / "Dockerfile").write_text("FROM old\n", encoding="utf-8")
        real = omi.setup.upgrade.SHAS
        omi.setup.upgrade.SHAS = root / "shas.json"
        try:
            omi.setup.upgrade.template_shas_cmd(old, "0.0.1")
            assert omi.setup.upgrade.released_shas()["docker/Dockerfile"] and "docker/Dockerfile" in json.loads(omi.setup.upgrade.SHAS.read_text(encoding="utf-8"))["0.0.1"]
            (root / "docker" / "Dockerfile").write_text("FROM old\n", encoding="utf-8")
            (root / ".omi" / "manifest.json").unlink()
            (root / ".omi" / "agents" / "omi-agent-engineer.md").unlink()
            (root / ".omi" / "tasks" / "TASK-001.md").write_text("task\n", encoding="utf-8")
            (root / ".omi" / "decisions.md").write_text("mine\n", encoding="utf-8")
            cfg = root / ".omi" / "config.json"
            c = json.loads(cfg.read_text(encoding="utf-8"))
            c["test"] = "pytest"
            del c["network_allow"]
            cfg.write_text(json.dumps(c), encoding="utf-8")
            omi.setup.upgrade.init(root)
            ref = root / ".omi" / "references" / "postgres-conventions.md"
            ref.write_text(ref.read_text(encoding="utf-8") + "\nmine\n", encoding="utf-8")
            edited = ref.read_text(encoding="utf-8")
            (root / "docker" / "Dockerfile").write_text("FROM old\n", encoding="utf-8")
            (root / ".omi" / "manifest.json").unlink()
            out = io.StringIO()
            loads, load = [], omi.setup.upgrade.released_shas
            omi.setup.upgrade.released_shas = lambda: loads.append(1) or load()
            try:
                with contextlib.redirect_stdout(out):
                    omi.setup.upgrade.upgrade_apply(root)
            finally:
                omi.setup.upgrade.released_shas = load
            assert loads == [1], "template_shas.json is read once per run"
        finally:
            omi.setup.upgrade.SHAS = real
        text = out.getvalue()
        assert (root / ".omi" / "agents" / "omi-agent-engineer.md").is_file()
        assert (root / "docker" / "Dockerfile").read_bytes() == (omi.common.core.TEMPLATE / "docker" / "Dockerfile").read_bytes()
        assert "kept (modified): .omi/references/postgres-conventions.md" in text
        assert (root / ".omi" / "references" / "postgres-conventions.md.omi-new").is_file()
        assert (root / ".omi" / "references" / "postgres-conventions.md").read_text(encoding="utf-8") == edited
        assert (root / ".omi" / "tasks" / "TASK-001.md").read_text(encoding="utf-8") == "task\n"
        assert (root / ".omi" / "decisions.md").read_text(encoding="utf-8") == "mine\n"
        c = json.loads((root / ".omi" / "config.json").read_text(encoding="utf-8"))
        assert c["test"] == "pytest" and c["network_allow"] == ["api.anthropic.com"]
        assert (root / ".omi" / "version").read_text(encoding="utf-8").strip() == omi.common.core.version()
        # a broken config.json stops the upgrade before any file changes
        (root / "docker" / "Dockerfile").unlink()
        (root / ".omi" / "manifest.json").unlink()
        cfg.write_text("{broken", encoding="utf-8")
        try:
            omi.setup.upgrade.upgrade_apply(root)
        except SystemExit as exc:
            assert "invalid JSON" in str(exc) and "nothing was changed" in str(exc)
        else:
            raise AssertionError("upgrade_apply accepted invalid config.json")
        assert not (root / "docker" / "Dockerfile").exists() and not (root / ".omi" / "manifest.json").exists()
        assert cfg.read_text(encoding="utf-8") == "{broken"


def test_upgrade_gitattributes():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        omi.setup.upgrade.upgrade_cmd(["--apply"], root)
        attrs = root / ".gitattributes"
        assert attrs.read_text(encoding="utf-8") == "* text=auto eol=lf\n"
        attrs.write_text("custom\n", encoding="utf-8")
        omi.setup.upgrade.upgrade_cmd(["--apply"], root)
        assert attrs.read_text(encoding="utf-8") == "custom\n"


def test_upgrade_non_object_config():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        cfg = root / ".omi" / "config.json"
        cfg.parent.mkdir()
        for value in ([], [1], None, "config", 42, True):
            cfg.write_text(json.dumps(value), encoding="utf-8")
            before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            try:
                omi.setup.upgrade.upgrade_apply(root)
            except SystemExit as exc:
                assert "expected an object" in str(exc) and "nothing was changed" in str(exc)
            else:
                raise AssertionError(f"accepted non-object config: {value!r}")
            assert before == {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            assert sorted(p.relative_to(root).as_posix() for p in root.rglob("*")) == [".omi", ".omi/config.json"]


def test_upgrade_stale_candidate():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        dst = root / "AGENTS.md"
        dst.write_text("local edits\n", encoding="utf-8")
        candidate = root / "AGENTS.md.omi-new"
        with contextlib.redirect_stdout(io.StringIO()) as out:
            omi.setup.upgrade.upgrade_apply(root)
        assert "replaced stale AGENTS.md.omi-new" not in out.getvalue()
        candidate.write_text("previous candidate\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            omi.setup.upgrade.upgrade_apply(root)
        assert "replaced stale AGENTS.md.omi-new" in out.getvalue()
        assert candidate.read_bytes() == (omi.common.core.TEMPLATE / "AGENTS.md").read_bytes()
        assert dst.read_text(encoding="utf-8") == "local edits\n"


def test_upgrade_protected():
    assert omi.setup.upgrade.protected(".omi/plans/PLAN-001.md") and not omi.setup.upgrade.protected(".omi/plans/PLAN-000.md")
    assert omi.setup.upgrade.protected(".omi/tasks/TASK-001.md") and not omi.setup.upgrade.protected(".omi/tasks/_template.md")
    assert omi.setup.upgrade.protected(".omi/decisions.md") and omi.setup.upgrade.protected(".omi/config.json") and not omi.setup.upgrade.protected("AGENTS.md")
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        with contextlib.redirect_stdout(io.StringIO()):
            omi.setup.upgrade.init(root)
        plans = root / ".omi" / "plans"
        old = "---\nid: PLAN-000\ntitle: Old\nstatus: done\n---\n"
        mine = "---\nid: PLAN-001\ntitle: Mine\nstatus: active\n---\n"
        (plans / "PLAN-000.md").write_text(old, encoding="utf-8")
        (plans / "PLAN-001.md").write_text(mine, encoding="utf-8")
        files = omi.setup.upgrade.read_manifest(root)
        files[".omi/plans/PLAN-000.md"] = omi.setup.upgrade.norm_sha(old.encode())
        omi.setup.upgrade.write_manifest(root, files)
        with contextlib.redirect_stdout(io.StringIO()):
            omi.setup.upgrade.upgrade_apply(root)
        assert (plans / "PLAN-000.md").read_bytes() == (omi.common.core.TEMPLATE / "dot-omi" / "plans" / "PLAN-000.md").read_bytes()
        assert (plans / "PLAN-001.md").read_text(encoding="utf-8") == mine


def test_upgrade_symlink_files():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "project"
        with contextlib.redirect_stdout(io.StringIO()):
            omi.setup.upgrade.init(root)
        outside = Path(d) / "outside.md"
        outside.write_bytes(b"old template\n")
        decisions = root / ".omi" / "decisions.md"
        decisions.write_bytes(b"project decisions\n")
        ref = root / ".omi" / "references" / "postgres-conventions.md"
        ref.write_bytes(ref.read_bytes() + b"\nlocal change\n")
        prove = root / "docker" / "prove.sh"
        prove.write_bytes(prove.read_bytes() + b"\nlocal change\n")
        agents = root / "AGENTS.md"
        agents.unlink()
        settings = root / ".claude" / "settings.json"
        settings.unlink()
        links = {ref.with_name(ref.name + ".omi-new"): Path("../decisions.md"),
                 prove.with_name(prove.name + ".omi-new"): outside,
                 agents: outside, settings: Path(d) / "missing.json"}
        try:
            for link, dest in links.items():
                link.symlink_to(dest)
        except OSError:
            print("skip upgrade symlink files: symlink creation unavailable")
            return
        files = omi.setup.upgrade.read_manifest(root)
        files["AGENTS.md"] = omi.setup.upgrade.norm_sha(outside.read_bytes())
        omi.setup.upgrade.write_manifest(root, files)
        edited = {p: p.read_bytes() for p in (ref, prove)}
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            assert omi.setup.upgrade.upgrade_apply(root) == 0
        assert decisions.read_bytes() == b"project decisions\n"
        assert outside.read_bytes() == b"old template\n"
        assert not (Path(d) / "missing.json").exists()
        for link in links:
            assert link.is_symlink()
            assert f"skip (symlink): {link.relative_to(root).as_posix()}" in out.getvalue()
        for p, content in edited.items():
            assert p.read_bytes() == content
        assert omi.setup.upgrade.read_manifest(root)["AGENTS.md"] == files["AGENTS.md"]


def test_upgrade_symlink_metadata():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "project"
        with contextlib.redirect_stdout(io.StringIO()):
            omi.setup.upgrade.init(root)
        outside = Path(d) / "outside.txt"
        outside.write_bytes(b"preserve even invalid JSON\n")
        rels = [".omi/config.json", ".omi/manifest.json", ".omi/version"]
        rels += [f".omi/{kind}/CATALOG.md" for kind in ("skills", "agents", "workflows", "rules", "references", "plans")]
        try:
            for rel in rels:
                link = root / rel
                link.unlink()
                link.symlink_to(outside)
        except OSError:
            print("skip upgrade symlink metadata: symlink creation unavailable")
            return
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            assert omi.setup.upgrade.upgrade_apply(root) == 0
        assert outside.read_bytes() == b"preserve even invalid JSON\n"
        for rel in rels:
            assert (root / rel).is_symlink()
            assert f"skip (symlink): {rel}" in out.getvalue()


def test_upgrade_symlink_parents():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "project"
        with contextlib.redirect_stdout(io.StringIO()):
            omi.setup.upgrade.init(root)
        outside = Path(d) / "outside"
        (root / "docker").rename(outside)
        # A missing destination through a linked parent must not be created either.
        (outside / "proxy.py").unlink()
        # An internal directory link could otherwise overwrite protected task files.
        rules = root / ".omi" / "rules"
        shutil.rmtree(rules)
        tasks = root / ".omi" / "tasks"
        (tasks / "python.md").write_bytes(b"protected task data\n")
        try:
            (root / "docker").symlink_to(outside, target_is_directory=True)
            rules.symlink_to(tasks, target_is_directory=True)
        except OSError:
            print("skip upgrade symlink parents: symlink creation unavailable")
            return
        before = {p: p.read_bytes() for base in (outside, tasks) for p in base.rglob("*") if p.is_file()}
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            assert omi.setup.upgrade.upgrade_apply(root) == 0
        after = {p: p.read_bytes() for base in (outside, tasks) for p in base.rglob("*") if p.is_file()}
        assert before == after
        assert "skip (symlink): docker/proxy.py" in out.getvalue()
        assert "skip (symlink): .omi/rules/python.md" in out.getvalue()
        assert "skip (symlink): .omi/rules/CATALOG.md" in out.getvalue()
        # A link above all omi state files must also prevent metadata and catalog writes.
        (root / ".omi").rename(Path(d) / "outside-omi")
        (root / ".omi").symlink_to(Path(d) / "outside-omi", target_is_directory=True)
        state = Path(d) / "outside-omi"
        before = {p: p.read_bytes() for p in state.rglob("*") if p.is_file()}
        with contextlib.redirect_stdout(io.StringIO()):
            assert omi.setup.upgrade.upgrade_apply(root) == 0
        assert before == {p: p.read_bytes() for p in state.rglob("*") if p.is_file()}


def test_omi_repo_validation():
    for ok in (omi.setup.upgrade.OMI_REPO, "ssh://git@host/x/y.git", "git@github.com:omi-teams/omi.git"):
        assert omi.setup.upgrade.valid_repo(ok), ok
    bad = ("--upload-pack=touch /tmp/x", "-oProxyCommand=x", "ssh://-oProxyCommand=x/y", "https://x/ y",
           "file:///tmp/repo", "/tmp/repo", "git@-oProxy:x", "ext::sh -c x", "", 7, None)
    for value in bad:
        assert not omi.setup.upgrade.valid_repo(value), value
    calls = []
    real = subprocess.run
    subprocess.run = lambda cmd, **kw: calls.append(cmd)
    try:
        with tempfile.TemporaryDirectory() as d:
            cfg = Path(d) / ".omi" / "config.json"
            cfg.parent.mkdir()
            for value in ("--upload-pack=touch /tmp/x", "https://x/ y"):
                cfg.write_text(json.dumps({"omi_repo": value}), encoding="utf-8")
                for args in (["--check"], [], ["--to", "v0.2.0"]):
                    try:
                        omi.setup.upgrade.upgrade_cmd(args, d)
                    except SystemExit as exc:
                        assert "invalid omi_repo" in str(exc)
                    else:
                        raise AssertionError(f"accepted omi_repo {value!r}")
            assert calls == [], "an invalid omi_repo must fail before git or pip runs"
    finally:
        subprocess.run = real


def test_omi_repo_non_object_config():
    calls = []
    real = subprocess.run
    subprocess.run = lambda cmd, **kw: calls.append(cmd)
    try:
        with tempfile.TemporaryDirectory() as d:
            cfg = Path(d) / ".omi" / "config.json"
            cfg.parent.mkdir()
            for value in ([], [1], None, "config", 42):
                cfg.write_text(json.dumps(value), encoding="utf-8")
                for args in (["--check"], [], ["--to", "v0.2.0"]):
                    try:
                        omi.setup.upgrade.upgrade_cmd(args, d)
                    except SystemExit as exc:
                        assert "expected an object" in str(exc), exc
                    else:
                        raise AssertionError(f"accepted non-object config {value!r}")
            assert calls == [], "a non-object config must fail before git or pip runs"
    finally:
        subprocess.run = real


def test_upgrade_cmd():
    calls = []
    ls = "a\trefs/tags/v0.2.0\nb\trefs/tags/v0.10.0\nc\trefs/tags/v0.10.0^{}\nd\trefs/tags/v2026.10.26\ne\trefs/tags/v0.9.0\nf\trefs/tags/v1000.0.0\ng\trefs/tags/rc-20261026-d55dcd3\n"

    def run(cmd, **kw):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, ls, "")

    real = subprocess.run
    subprocess.run = run
    try:
        assert omi.setup.upgrade.latest_tag("https://x/y") == "v0.10.0"
        assert calls[0] == ["git", "ls-remote", "--tags", "--", "https://x/y"]
        with tempfile.TemporaryDirectory() as d:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                omi.setup.upgrade.upgrade_cmd(["--check"], d)
            assert out.getvalue().strip() == f"omi {omi.common.core.version()} -> 0.10.0"
            calls.clear()
            assert omi.setup.upgrade.upgrade_cmd(["--to", "v0.9.0"], d) == 0
            assert calls == [
                [sys.executable, "-m", "pip", "install", "--user", "--upgrade", f"git+{omi.setup.upgrade.OMI_REPO}@v0.9.0"],
                [sys.executable, "-m", "omi", "upgrade", "--apply"],
            ]
            cfg = Path(d) / ".omi" / "config.json"
            cfg.parent.mkdir()
            cfg.write_text(json.dumps({"omi_repo": "git@host:team/repo.git"}), encoding="utf-8")
            calls.clear()
            assert omi.setup.upgrade.upgrade_cmd(["--to", "v0.9.0", "--repo", "git@host:team/repo.git"], d) == 0
            assert calls == [
                [sys.executable, "-m", "pip", "install", "--user", "--upgrade", "git+ssh://git@host/team/repo.git@v0.9.0"],
                [sys.executable, "-m", "omi", "upgrade", "--apply"],
            ]
            calls.clear()
            with contextlib.redirect_stdout(io.StringIO()):
                assert omi.setup.upgrade.upgrade_cmd(["--check", "--to", "v0.9.0"], d) == 0
            assert calls == [["git", "ls-remote", "--tags", "--", "git@host:team/repo.git"]]
            for args in (["--to"], ["--to", "--check"], ["--to", "v2026.10.26"], ["--to", "v1000.0.0"]):
                calls.clear()
                try:
                    omi.setup.upgrade.upgrade_cmd(args, d)
                except SystemExit as exc:
                    assert str(exc) == "usage: omi upgrade [--check | --to vX.Y.Z]"
                else:
                    raise AssertionError(f"accepted invalid upgrade arguments: {args}")
                assert calls == [], "invalid arguments must fail before any subprocess"
    finally:
        subprocess.run = real


def test_upgrade_repo_confirmation():
    calls = []

    def run(cmd, **kw):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "a\trefs/tags/v0.10.0\n", "")

    real = subprocess.run
    subprocess.run = run
    try:
        with tempfile.TemporaryDirectory() as d:
            cfg = Path(d) / ".omi" / "config.json"
            cfg.parent.mkdir()
            for repo, pip_repo in (("https://example.com/team/omi", "https://example.com/team/omi"),
                                   ("ssh://git@host/team/omi", "ssh://git@host/team/omi"),
                                   ("git@host:team/omi", "ssh://git@host/team/omi")):
                cfg.write_text(json.dumps({"omi_repo": repo}), encoding="utf-8")
                for args in ([], ["--to", "v0.9.0"], ["--repo"], ["--repo", omi.setup.upgrade.OMI_REPO],
                             ["--to", "v0.9.0", "--repo", "https://example.com/other"]):
                    calls.clear()
                    try:
                        omi.setup.upgrade.upgrade_cmd(args, d)
                    except SystemExit as exc:
                        assert str(exc) == f"omi_repo is not the default; confirm with --repo {repo}"
                    else:
                        raise AssertionError(f"installed from unconfirmed repo: {args}")
                    assert calls == [], "confirmation is required before any subprocess"
                calls.clear()
                with contextlib.redirect_stdout(io.StringIO()) as out:
                    assert omi.setup.upgrade.upgrade_cmd(["--check"], d) == 0
                assert out.getvalue().splitlines() == [f"repo: {repo} (not the default)", f"omi {omi.common.core.version()} -> 0.10.0"]
                assert calls == [["git", "ls-remote", "--tags", "--", repo]]
                for args, tag in ((["--repo", repo], "v0.10.0"),
                                  (["--to", "v0.9.0", "--repo", repo], "v0.9.0")):
                    calls.clear()
                    assert omi.setup.upgrade.upgrade_cmd(args, d) == 0
                    expected = [] if "--to" in args else [["git", "ls-remote", "--tags", "--", repo]]
                    assert calls == expected + [
                        [sys.executable, "-m", "pip", "install", "--user", "--upgrade", f"git+{pip_repo}@{tag}"],
                        [sys.executable, "-m", "omi", "upgrade", "--apply"],
                    ]
    finally:
        subprocess.run = real


def test_upgrade_skill_repo_confirmation():
    skill = (omi.common.core.TEMPLATE / "dot-claude/skills/omi-upgrade/SKILL.md").read_text(encoding="utf-8")
    assert "repo" in skill and "pick-list" in skill
    assert "confirm" in skill and "non-default" in skill and "--repo <url>" in skill
    assert "--check" in skill and "--to <tag>" in skill and ".omi-new" in skill
    assert "development" in skill and "tests" in skill
    assert "older than" in skill and "python -m omi upgrade --apply" in skill and "steps 4-5" in skill


def test_status_drift_hints():
    def status_text(root):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            omi.app.cli.status(root)
        return buf.getvalue()

    with tempfile.TemporaryDirectory() as d:
        root = Path(d).resolve()
        omi.setup.upgrade.init(root)
        text = status_text(root)
        assert "needs omi" not in text and "docker/Dockerfile differs" not in text, text
        (root / ".omi" / "version").write_text("99.0.0\n", encoding="utf-8")
        assert 'this project needs omi 99.0.0; install it: python -m pip install --user "git+https://github.com/omi-teams/omi@v99.0.0"' in status_text(root)
        df = root / "docker" / "Dockerfile"
        crlf = df.read_bytes().replace(b"\n", b"\r\n")
        df.write_bytes(crlf)
        assert "docker/Dockerfile differs" not in status_text(root), "CRLF is not a difference"
        df.write_bytes(crlf + b"RUN true\r\n")
        assert f"docker/Dockerfile differs from the omi {omi.common.core.version()} template; review it (omi init never overwrites it)" in status_text(root)
        assert f"git diff --no-index {omi.common.core.TEMPLATE / 'docker' / 'Dockerfile'} docker/Dockerfile" in status_text(root) and "merge by hand" in status_text(root)
        df.unlink()
        assert "docker/Dockerfile differs" not in status_text(root)
        real = omi.common.core.main_checkout, omi.worker.docker.full_volumes
        main = root / "main"
        queried = []
        omi.common.core.main_checkout = lambda _: main
        omi.worker.docker.full_volumes = lambda path: queried.append(path) or ["cache warning"]
        try:
            assert "cache warning" in status_text(root)
            assert queried == [main], queried
        finally:
            omi.common.core.main_checkout, omi.worker.docker.full_volumes = real


def main():
    test_upgrade_gitattributes()
    test_version_stamp_package_hook()
    test_upgrade()
    test_upgrade_non_object_config()
    test_upgrade_stale_candidate()
    test_upgrade_protected()
    test_upgrade_symlink_files()
    test_upgrade_symlink_metadata()
    test_upgrade_symlink_parents()
    test_omi_repo_validation()
    test_omi_repo_non_object_config()
    test_upgrade_cmd()
    test_upgrade_repo_confirmation()
    test_upgrade_skill_repo_confirmation()
    test_status_drift_hints()


if __name__ == "__main__":
    main()
