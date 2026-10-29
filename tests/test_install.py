import io
import json
import contextlib
import tempfile
from pathlib import Path
from unittest.mock import patch
from helpers import omi


def test_install_user():
    with tempfile.TemporaryDirectory() as d, patch("pathlib.Path.home", return_value=Path(d)):
        home = Path(d)
        settings = home / ".claude/settings.json"
        agents = home / ".codex/AGENTS.md"
        settings.parent.mkdir()
        agents.parent.mkdir()
        original = b'{"model":"mine", "hooks":{"SessionStart":[{"hooks":[{"type":"command","command":"echo mine"}]}],"Stop":[]}}\r\n'
        settings.write_bytes(original)
        agents.write_bytes(b"My rules\r\n")
        skill = home / ".claude/skills/omi-task/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_bytes(b"user skill")
        with contextlib.redirect_stdout(io.StringIO()):
            omi.setup.install.install_user()
            snapshot = {p.relative_to(home): p.read_bytes() for p in home.rglob("*") if p.is_file()}
            omi.setup.install.install_user()
        assert snapshot == {p.relative_to(home): p.read_bytes() for p in home.rglob("*") if p.is_file()}
        config = json.loads(settings.read_text(encoding="utf-8"))
        assert config["model"] == "mine" and config["hooks"]["Stop"] == []
        assert len(config["hooks"]["SessionStart"]) == 2
        assert settings.with_name("settings.json.omi-bak").read_bytes() == original
        text = agents.read_text(encoding="utf-8")
        assert text.count("<!-- omi -->") == 1 and omi.setup.install.coordinator_rules().rstrip() in text
        for source in (omi.common.core.TEMPLATE / "dot-claude/skills").rglob("*"):
            if source.is_file():
                assert (home / ".claude/skills" / source.relative_to(omi.common.core.TEMPLATE / "dot-claude/skills")).read_bytes() == source.read_bytes()
        with contextlib.redirect_stdout(io.StringIO()):
            omi.setup.install.install_user(remove=True)
        assert settings.read_bytes() == original and agents.read_bytes() == b"My rules\r\n"
        assert skill.read_bytes() == b"user skill"
        assert sorted(p.relative_to(home).as_posix() for p in home.rglob("*") if p.is_file()) == [
            ".claude/settings.json", ".claude/skills/omi-task/SKILL.md", ".codex/AGENTS.md"]


def test_install_user_removal_preserves_edits():
    with tempfile.TemporaryDirectory() as d, patch("pathlib.Path.home", return_value=Path(d)):
        home = Path(d)
        with contextlib.redirect_stdout(io.StringIO()):
            omi.setup.install.install_user()
        settings = home / ".claude/settings.json"
        config = json.loads(settings.read_text(encoding="utf-8"))
        config["new"] = True
        config["hooks"]["SessionStart"].append({"hooks": []})
        settings.write_text(json.dumps(config), encoding="utf-8")
        agents = home / ".codex/AGENTS.md"
        agents.write_text(agents.read_text(encoding="utf-8") + "\nUser addition", encoding="utf-8")
        skill = home / ".claude/skills/omi-task/SKILL.md"
        skill.write_text("edited", encoding="utf-8")
        try:
            omi.setup.install.install_user()
        except omi.state.resolve.StateError as exc:
            assert "modified installed skill" in str(exc)
        else:
            raise AssertionError("overwrote edited skill")
        with contextlib.redirect_stdout(io.StringIO()):
            omi.setup.install.install_user(remove=True)
        assert skill.read_text(encoding="utf-8") == "edited"
        assert json.loads(settings.read_text(encoding="utf-8")) == {"new": True, "hooks": {"SessionStart": [{"hooks": []}]}}
        assert agents.read_text(encoding="utf-8") == "\nUser addition"
    with tempfile.TemporaryDirectory() as d, patch("pathlib.Path.home", return_value=Path(d)):
        with contextlib.redirect_stdout(io.StringIO()):
            omi.setup.install.install_user()
            omi.setup.install.install_user(remove=True)
        assert not list(Path(d).iterdir()), "fresh install must undo its files and empty directories"


def test_install_user_existing_integration():
    with tempfile.TemporaryDirectory() as d, patch("pathlib.Path.home", return_value=Path(d)):
        home = Path(d)
        settings = home / ".claude/settings.json"
        settings.parent.mkdir()
        original = json.dumps({"hooks": {"SessionStart": [omi.setup.install.HOOK]}}).encode("utf-8")
        settings.write_bytes(original)
        backup = settings.with_name("settings.json.omi-bak")
        backup.write_bytes(b"older backup")
        agents = home / ".codex/AGENTS.md"
        agents.parent.mkdir()
        before = "Before\n<!-- omi -->old rules<!-- /omi -->\nAfter"
        agents.write_text(before, encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            omi.setup.install.install_user()
            with patch("omi.setup.install.coordinator_rules", return_value="Updated rules"):
                omi.setup.install.install_user()
            assert agents.read_text(encoding="utf-8") == "Before\n<!-- omi -->\nUpdated rules\n<!-- /omi -->\nAfter"
            omi.setup.install.install_user(remove=True)
        assert agents.read_text(encoding="utf-8") == before
        assert settings.read_bytes() == original and backup.read_bytes() == b"older backup"


def test_install_user_invalid_input():
    with tempfile.TemporaryDirectory() as d, patch("pathlib.Path.home", return_value=Path(d)):
        home = Path(d)
        settings = home / ".claude/settings.json"
        settings.parent.mkdir()
        for bad in ("{", "[]", '{"hooks":[]}', '{"hooks":{"SessionStart":{}}}'):
            settings.write_text(bad, encoding="utf-8")
            try:
                omi.setup.install.install_user()
            except omi.state.resolve.StateError:
                pass
            else:
                raise AssertionError(bad)
            assert settings.read_text(encoding="utf-8") == bad
            assert not (home / ".omi/install-user.json").exists()
        settings.write_text("{}", encoding="utf-8")
        agents = home / ".codex/AGENTS.md"
        agents.parent.mkdir()
        agents.write_text("<!-- omi -->broken", encoding="utf-8")
        try:
            omi.setup.install.install_user()
        except omi.state.resolve.StateError:
            pass
        else:
            raise AssertionError("accepted broken block")
        assert settings.read_text(encoding="utf-8") == "{}"


def test_install_user_recorded_interpreter():
    for platform, executable, quoted in (
            ("linux", "/opt/my python/bin/python3", "'/opt/my python/bin/python3'"),
            ("win32", r"C:\Program Files\Python\python.exe", '"C:\\Program Files\\Python\\python.exe"')):
        with tempfile.TemporaryDirectory() as d, patch("pathlib.Path.home", return_value=Path(d)):
            home = Path(d)
            with contextlib.redirect_stdout(io.StringIO()):
                with patch("omi.setup.install.sys.executable", executable), patch("omi.setup.install.sys.platform", platform):
                    omi.setup.install.install_user()
                manifest = json.loads((home / ".omi/install-user.json").read_text(encoding="utf-8"))
                hook = manifest["hook"]
                assert hook["hooks"][0]["command"] == quoted + " -m omi session-start"
                snapshot = {p.relative_to(home): p.read_bytes() for p in home.rglob("*") if p.is_file()}
                with patch("omi.setup.install.sys.executable", "/another/python"):
                    omi.setup.install.install_user()
                    assert snapshot == {p.relative_to(home): p.read_bytes() for p in home.rglob("*") if p.is_file()}
                    omi.setup.install.install_user(remove=True)
            assert not list(home.iterdir())


def test_install_user_legacy_manifest():
    with tempfile.TemporaryDirectory() as d, patch("pathlib.Path.home", return_value=Path(d)):
        home = Path(d)
        with contextlib.redirect_stdout(io.StringIO()):
            omi.setup.install.install_user()
            manifest = home / ".omi/install-user.json"
            record = json.loads(manifest.read_text(encoding="utf-8"))
            del record["hook"]
            manifest.write_text(json.dumps(record), encoding="utf-8")
            settings = home / ".claude/settings.json"
            settings.write_text(json.dumps({"hooks": {"SessionStart": [omi.setup.install.LEGACY_HOOK]}}), encoding="utf-8")
            omi.setup.install.install_user()
            assert json.loads(settings.read_text(encoding="utf-8"))["hooks"]["SessionStart"] == [omi.setup.install.LEGACY_HOOK]
            omi.setup.install.install_user(remove=True)
        assert not list(home.iterdir())


def test_install_user_write_failure():
    for fail_at in (1, 3):  # Manifest write failure, then failure after one skill write.
        with tempfile.TemporaryDirectory() as d, patch("pathlib.Path.home", return_value=Path(d)):
            home = Path(d)
            write = omi.setup.install._write
            calls = []

            def failing_write(path, data):
                calls.append(path)
                if len(calls) == fail_at:
                    raise OSError("injected write failure")
                write(path, data)

            with patch("omi.setup.install._write", side_effect=failing_write):
                try:
                    omi.setup.install.install_user()
                except OSError as exc:
                    assert str(exc) == "injected write failure"
                else:
                    raise AssertionError("write failure was not injected")
            assert calls[0] == home / ".omi/install-user.json"
            if fail_at == 1:
                assert not list(home.rglob("SKILL.md"))
            else:
                record = json.loads(calls[0].read_text(encoding="utf-8"))
                assert all(item["before"] is None for item in record["skills"].values())
                assert len(list(home.rglob("SKILL.md"))) == 1
            with contextlib.redirect_stdout(io.StringIO()):
                omi.setup.install.install_user()
                omi.setup.install.install_user(remove=True)
            assert not list(home.iterdir()), "retry must not adopt partially installed skills as user originals"


def test_install_user_invalid_manifest_cli():
    with tempfile.TemporaryDirectory() as d, patch("pathlib.Path.home", return_value=Path(d)):
        home = Path(d)
        with contextlib.redirect_stdout(io.StringIO()):
            omi.setup.install.install_user()
        manifest = home / ".omi/install-user.json"
        valid = manifest.read_text(encoding="utf-8")
        skill = next(iter(json.loads(valid)["skills"]))
        cases = [({}, None, None)]
        for field, bad_values in {
                "settings_before": ["!!!notbase64", 42, "W10=", "e30=\n", "////"],
                "directories": [[None], [42], ["../escape"]],
                "hook": [[], {"hooks": [None]}, {"hooks": [{"type": "command", "command": 1}]}],
                "skills": [{".claude/skills/x": {"sha256": "bad", "before": None}}],
                "hook_added": [1]}.items():
            cases.extend((None, field, value) for value in bad_values)
        for field, values in {"before": ["!!!notbase64", [], "////é"], "sha256": [None, "bad"]}.items():
            for value in values:
                record = json.loads(valid)
                record["skills"][skill][field] = value
                cases.append((record, None, None))
        record = json.loads(valid)
        del record["skills"][skill]["before"]
        cases.append((record, None, None))
        for record, field, value in cases:
            if record is None:
                record = json.loads(valid)
                record[field] = value
            manifest.write_text(json.dumps(record), encoding="utf-8")
            snapshot = {p.relative_to(home): p.read_bytes() for p in home.rglob("*") if p.is_file()}
            for args in (["install-user"], ["install-user", "--remove"]):
                output = io.StringIO()
                output.reconfigure = lambda **kw: None
                with contextlib.redirect_stdout(output):
                    try:
                        omi.main(args)
                    except SystemExit as exc:
                        message = str(exc)
                        assert message.startswith("OMI: invalid install manifest "), message
                        assert len(message.splitlines()) == 1
                    else:
                        raise AssertionError(f"accepted malformed manifest: {record}")
                assert output.getvalue() == ""
                assert snapshot == {p.relative_to(home): p.read_bytes() for p in home.rglob("*") if p.is_file()}


def main():
    test_install_user_recorded_interpreter()
    test_install_user_legacy_manifest()
    test_install_user_write_failure()
    test_install_user_invalid_manifest_cli()
    test_install_user()
    test_install_user_removal_preserves_edits()
    test_install_user_invalid_input()
    test_install_user_existing_integration()


if __name__ == "__main__":
    main()
