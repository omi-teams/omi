"""Board frontend: no innerHTML or external resources, files ship as package data."""
import fnmatch
import re
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from pathlib import Path

import helpers  # noqa: F401

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "src" / "omi" / "board" / "web"
FILES = ("index.html", "app.css", "app.js")


def test_files_safe():
    for name in FILES:
        text = (WEB / name).read_text(encoding="utf-8")
        assert not re.search(r"https?://|//cdn|@import|@font-face", text), name
    js = (WEB / "app.js").read_text(encoding="utf-8")
    assert not re.search(r"innerHTML|outerHTML|insertAdjacentHTML|document\.write|eval\(", js)
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert 'lang="vi"' in html and 'name="viewport"' in html
    assert not re.search(r"<script(?![^>]*\bsrc=)|<style|style=", html)
    assert "@media (min-width: 768px)" in (WEB / "app.css").read_text(encoding="utf-8")


def test_package_data():
    # setuptools may be absent; check that the package-data globs cover every web file.
    patterns = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["setuptools"]["package-data"]["omi"]
    for name in FILES:
        rel = f"board/web/{name}"
        assert (WEB / name).is_file() and any(fnmatch.fnmatch(rel, p) for p in patterns), name


def test_wheel_ships_web():
    if subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True).returncode:
        print("skip test_wheel_ships_web: pip missing")
        return
    with tempfile.TemporaryDirectory() as tmp:
        run = subprocess.run([sys.executable, "-m", "pip", "wheel", ".", "--no-deps", "-w", tmp],
                             cwd=ROOT, capture_output=True, text=True)
        assert run.returncode == 0, run.stderr
        wheel = next(Path(tmp).glob("*.whl"))
        names = zipfile.ZipFile(wheel).namelist()
    for name in FILES:
        assert f"omi/board/web/{name}" in names, name


def test_app_js_behaviors():
    js = (WEB / "app.js").read_text(encoding="utf-8")
    for needle in ("Thử lại", "Cập nhật lần cuối", "document.hidden", "localStorage"):
        assert needle in js, needle
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert 'role="status"' in html and 'id="refresh"' in html and "Làm mới" in html


def main():
    test_files_safe()
    test_package_data()
    test_wheel_ships_web()
    test_app_js_behaviors()


if __name__ == "__main__":
    main()
