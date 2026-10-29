"""User-level Coordinator integration and its reversible install manifest."""

import base64
import hashlib
import json
from pathlib import Path

from . import core, state


HOOK = {"hooks": [{"type": "command", "command": "python -m omi session-start"}]}
START, END = "<!-- omi -->", "<!-- /omi -->"


def coordinator_rules() -> str:
    """Share the packaged Coordinator rules between both user integrations."""
    rules = (core.TEMPLATE / "AGENTS.md").read_text(encoding="utf-8")
    rules = rules.replace(".claude/skills/", "~/.claude/skills/")
    rules = rules.replace("## State (files in the repo are the only source of truth)",
                          "## State (files in detached state are the only source of truth)")
    return ("These Coordinator instructions apply only in an attached omi repository. "
            "Run `python -m omi session-start`; if it prints nothing, ignore this block. "
            "Resolve the attached state directory with `python -m omi status`; "
            "all .omi/ and docs/product.md paths below refer to that state directory, "
            "not the code checkout.\n\n" + rules)


def _object(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, ValueError) as exc:
        raise state.StateError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise state.StateError(f"{path}: expected a JSON object")
    return value


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _json(path: Path, data: dict) -> None:
    _write(path, (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def _block(text: str) -> str:
    if text.count(START) != text.count(END) or text.count(START) > 1:
        raise state.StateError("malformed omi block in ~/.codex/AGENTS.md")
    if START not in text:
        return ""
    begin, end = text.index(START), text.index(END)
    if end < begin:
        raise state.StateError("malformed omi block in ~/.codex/AGENTS.md")
    return text[begin:end + len(END)]


def install_user(remove: bool = False) -> None:
    """Install or remove only tracked user integration, preserving unrelated content."""
    home = Path.home()
    manifest = home / ".omi" / "install-user.json"
    record = _object(manifest)
    settings = home / ".claude" / "settings.json"
    agents = home / ".codex" / "AGENTS.md"
    if record:
        fields = {"skills": dict, "directories": list, "settings_created": bool,
                  "agents_created": bool, "hooks_created": bool, "session_created": bool,
                  "hook_added": bool, "block_before": str, "prefix": str, "backup_created": bool}
        if any(not isinstance(record.get(key), kind) for key, kind in fields.items()) or "settings_before" not in record:
            raise state.StateError(f"invalid install manifest {manifest}")
        for rel, item in record["skills"].items():
            path = Path(rel)
            if (path.is_absolute() or ".." in path.parts or path.parts[:2] != (".claude", "skills")
                    or not isinstance(item, dict) or not isinstance(item.get("sha256"), str) or "before" not in item):
                raise state.StateError(f"invalid install manifest {manifest}")
        for rel in record["directories"]:
            path = Path(rel)
            if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] not in (".claude", ".codex", ".omi"):
                raise state.StateError(f"invalid install manifest {manifest}")
    config = _object(settings)
    hooks = config.get("hooks", {})
    if not isinstance(hooks, dict) or not isinstance(hooks.get("SessionStart", []), list):
        raise state.StateError(f"{settings}: expected hooks object and SessionStart list")
    text = agents.read_bytes().decode("utf-8") if agents.exists() else ""
    old_block = _block(text)
    if remove:
        if not record:
            print("omi user integration not installed")
            return
        for rel, item in record["skills"].items():
            path = home / rel
            if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]:
                if item["before"] is None:
                    path.unlink()
                else:
                    path.write_bytes(base64.b64decode(item["before"]))
            elif path.exists():
                print(f"keep modified: {path}")
        if record["hook_added"] and HOOK in hooks.get("SessionStart", []):
            hooks["SessionStart"].remove(HOOK)
        if record["session_created"] and not hooks.get("SessionStart"):
            hooks.pop("SessionStart", None)
        if record["hooks_created"] and not hooks:
            config.pop("hooks", None)
        if record["settings_created"] and not config:
            settings.unlink(missing_ok=True)
        elif settings.exists():
            original = record["settings_before"]
            if original is not None and config == json.loads(base64.b64decode(original)):
                settings.write_bytes(base64.b64decode(original))
            else:
                _json(settings, config)
        backup = settings.with_name("settings.json.omi-bak")
        if record["backup_created"] and backup.exists() and base64.b64encode(backup.read_bytes()).decode("ascii") == record["settings_before"]:
            backup.unlink()
        if old_block:
            owned = record["prefix"] + old_block
            text = text.replace(owned if owned in text else old_block, record["block_before"], 1)
            if not text and record["agents_created"]:
                agents.unlink(missing_ok=True)
            else:
                _write(agents, text.encode("utf-8"))
        manifest.unlink()
        for rel in record["directories"]:
            try:
                (home / rel).rmdir()
            except OSError:
                pass  # Leave directories that now contain user files.
        print("removed omi user integration")
        return
    sources = sorted((core.TEMPLATE / "dot-claude" / "skills").rglob("*"))
    sources = [p for p in sources if p.is_file()]
    payloads = {str(Path(".claude/skills") / p.relative_to(core.TEMPLATE / "dot-claude/skills")): p.read_bytes()
                for p in sources}
    if not record:
        record = {"skills": {}, "settings_created": not settings.exists(), "agents_created": not agents.exists(),
                  "hooks_created": "hooks" not in config, "session_created": "SessionStart" not in hooks,
                  "hook_added": HOOK not in hooks.get("SessionStart", []), "block_before": old_block,
                  "prefix": "" if old_block or not text else "\n\n", "directories": [],
                  "settings_before": base64.b64encode(settings.read_bytes()).decode("ascii") if settings.exists() else None,
                  "backup_created": settings.exists() and not settings.with_name("settings.json.omi-bak").exists() and HOOK not in hooks.get("SessionStart", [])}
    # Read all originals before writing anything, including on an upgrade.
    for rel, data in payloads.items():
        path = home / rel
        item = record["skills"].get(rel)
        if item and path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise state.StateError(f"modified installed skill: {path}; preserve or remove it before reinstalling")
        if not item:
            record["skills"][rel] = {"before": base64.b64encode(path.read_bytes()).decode("ascii") if path.exists() else None}
        record["skills"][rel]["sha256"] = hashlib.sha256(data).hexdigest()
    for path in [settings, agents, manifest, *(home / rel for rel in payloads)]:
        for parent in path.parents:
            if parent == home:
                break
            rel = str(parent.relative_to(home))
            if not parent.exists() and rel not in record["directories"]:
                record["directories"].append(rel)
    record["directories"].sort(key=lambda p: len(Path(p).parts), reverse=True)
    for rel, data in payloads.items():
        _write(home / rel, data)
    updated = {**config, "hooks": {**hooks, "SessionStart": [*hooks.get("SessionStart", [])]}}
    if HOOK not in updated["hooks"]["SessionStart"]:
        updated["hooks"]["SessionStart"].append(HOOK)
    if updated != config:
        backup = settings.with_name("settings.json.omi-bak")
        if settings.exists() and not backup.exists():
            _write(backup, settings.read_bytes())
        _json(settings, updated)
    block = START + "\n" + coordinator_rules().rstrip() + "\n" + END
    text = text.replace(old_block, block, 1) if old_block else text + record["prefix"] + block
    _write(agents, text.encode("utf-8"))
    _json(manifest, record)
    print("installed omi user integration")
