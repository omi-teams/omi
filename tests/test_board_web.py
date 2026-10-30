"""Board frontend: no innerHTML or external resources, files ship as package data."""
import fnmatch
import re
import tomllib
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


def main():
    test_files_safe()
    test_package_data()


if __name__ == "__main__":
    main()
