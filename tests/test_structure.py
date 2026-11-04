import json
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import helpers  # noqa: F401
from omi.project import structure

HEAD = "---\nid: structure\nsummary: map\n---\n# Map\n"
GOOD = HEAD + """- src/shop/modules/*/domain/** | domain | entities | imports: domain, shared
- src/shop/modules/*/application/** | application | use cases | imports: application, domain, shared
- src/shop/shared/** | shared | kernel | imports: shared
- database/**, README.md | data | migrations | imports: -
- src/** | platform | catch-all | imports: shared
"""


def load(text):
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / ".omi").mkdir()
        (Path(d) / ".omi/structure.md").write_text(text, encoding="utf-8")
        return structure.load(d)


def err(text):
    try:
        load(text)
    except structure.StructureError as exc:
        return str(exc)
    raise AssertionError("no error")


def test_load_and_errors():
    rules = load(GOOD)
    assert [r["layer"] for r in rules] == ["domain", "application", "shared", "data", "platform"]
    assert rules[3]["globs"] == ["database/**", "README.md"] and rules[3]["imports"] == []
    assert rules[1]["imports"] == ["application", "domain", "shared"] and rules[0]["line"] == 6
    assert "line 6" in err(HEAD + "- a/** | domain | x\n") and "line 8: unknown layer" in err(HEAD + "\n- a | domain | x | imports: shared\n- b | nope | x | imports: shared\n")
    assert "line 6: unknown layer 'nope'" in err(HEAD + "- a | nope | x | imports: shared\n")
    assert "line 6: empty imports" in err(HEAD + "- a | domain | x | imports:\n")
    assert "line 6: unknown layer 'zzz' in imports" in err(HEAD + "- a | domain | x | imports: shared, zzz\n")
    assert "id: structure" in err("---\nid: other\n---\n- a | domain | x | imports: -\n")
    assert "line 6: expected" in err(HEAD + "-x | domain | y | imports: -\n")
    assert "line 7: expected" in err(HEAD + "- a | domain | y | imports: -\n-b\n")
    assert "line 6: expected" in err(HEAD + "- , | domain | y | imports: -\n")
    try:
        structure.load("/nonexistent-omi-root")
        raise AssertionError("no error")
    except structure.StructureError:
        pass


def test_match():
    rules = load(GOOD)
    m = structure.match(rules, "src/shop/modules/orders/domain/order.py")
    assert m == {"layer": "domain", "module": "orders", "responsibility": "entities"}
    assert structure.match(rules, "src/shop/modules/cart/application/a/b.py")["module"] == "cart"
    assert structure.match(rules, "src/shop/shared/x.py")["module"] is None
    assert structure.match(rules, "src/shop/modules/orders/other.py")["layer"] == "platform"  # first match wins
    assert structure.match(rules, "README.md")["layer"] == "data"
    assert structure.match(rules, "database/m/0001.sql")["layer"] == "data"
    assert structure.match(rules, "unknown/file.py") is None


MAP = """---
id: structure
---
- {a}/{m}/*/{d}/** | domain | d | imports: domain, shared
- {a}/{m}/*/{p}/** | application | a | imports: application, domain, shared
- {a}/{m}/*/{x}/{i}/** | adapter-in | i | imports: application, domain, shared
- {a}/{s}/** | shared | s | imports: shared
- database/** | data | m | imports: -
"""
LOWER = dict(a="app", m="modules", d="domain", p="application", x="adapters", i="inbound", s="shared")
PASCAL = dict(a="App", m="Modules", d="Domain", p="Application", x="Adapters", i="Inbound", s="Shared")

# (exts, pascal dirs, file names (domain src+target, inbound target, cart use case), domain text, cross text, expected specs)
LANGS = [
    ((".py",), False, ("order", "http", "use"),
     "import os\nfrom app.modules.orders.adapters.inbound import http\nfrom . import x\nfrom app.shared import kernel\n",
     "from app.modules.orders.domain.order import Order\n",
     ["app.modules.orders.adapters.inbound"], ["app.modules.orders.domain.order"]),
    ((".ts", ".js", ".tsx"), False, ("order", "http", "use"),
     "import fs from 'fs';\nimport { h } from '../adapters/inbound/http';\nexport { k } from \"../../../shared/kernel\";\n",
     "const o = require('../../orders/domain/order');\n",
     ["../adapters/inbound/http"], ["../../orders/domain/order"]),
    ((".go",), False, ("order", "http", "use"),
     'package domain\n\nimport (\n\t"fmt"\n\tin "github.com/acme/shop/app/modules/orders/adapters/inbound"\n)\n',
     'package application\n\nimport "github.com/acme/shop/app/modules/orders/domain"\n',
     ["github.com/acme/shop/app/modules/orders/adapters/inbound"], ["github.com/acme/shop/app/modules/orders/domain"]),
    ((".java",), False, ("Order", "Http", "Use"),
     "package com.acme.shop;\n\nimport java.util.List;\nimport static com.acme.shop.app.modules.orders.adapters.inbound.Http.handle;\n",
     "import com.acme.shop.app.modules.orders.domain.Order;\n",
     ["com.acme.shop.app.modules.orders.adapters.inbound.Http.handle"], ["com.acme.shop.app.modules.orders.domain.Order"]),
    ((".kt",), False, ("Order", "Http", "Use"),
     "import kotlin.collections.List\nimport com.acme.shop.app.modules.orders.adapters.inbound.Http\n",
     "import com.acme.shop.app.modules.orders.domain.Order\n",
     ["com.acme.shop.app.modules.orders.adapters.inbound.Http"], ["com.acme.shop.app.modules.orders.domain.Order"]),
    ((".cs",), True, ("Order", "Http", "Use"),
     "using System;\nusing static Acme.Shop.App.Modules.Orders.Adapters.Inbound.Http;\n",
     "using Acme.Shop.App.Modules.Orders.Domain.Order;\n",
     ["Acme.Shop.App.Modules.Orders.Adapters.Inbound.Http"], ["Acme.Shop.App.Modules.Orders.Domain.Order"]),
    ((".php",), True, ("Order", "Http", "Use"),
     "<?php\nuse App\\Modules\\Orders\\Adapters\\Inbound\\Http;\nrequire_once '../Adapters/Inbound/Http.php';\nuse Vendor\\Lib\\Thing;\n",
     "<?php\nuse function App\\Modules\\Orders\\Domain\\Order;\n",
     ["App\\Modules\\Orders\\Adapters\\Inbound\\Http", "../Adapters/Inbound/Http.php"], ["App\\Modules\\Orders\\Domain\\Order"]),
    ((".rs",), False, ("order", "http", "use"),
     "use std::fmt;\npub use crate::app::modules::orders::adapters::inbound::http::Handler;\n",
     "use crate::app::modules::orders::domain::order::Order;\n",
     ["crate::app::modules::orders::adapters::inbound::http::Handler"], ["crate::app::modules::orders::domain::order::Order"]),
    ((".rb",), False, ("order", "http", "use"),
     "require 'json'\nrequire_relative '../adapters/inbound/http'\n",
     "require_relative \"../../orders/domain/order\"\n",
     ["../adapters/inbound/http"], ["../../orders/domain/order"]),
    ((".c", ".cpp"), False, ("order", "http", "use"),
     '#include <stdio.h>\n#include "../adapters/inbound/http.h"\n',
     '# include "../../orders/domain/order.h"\n',
     ["../adapters/inbound/http.h"], ["../../orders/domain/order.h"]),
]


def scan(mapping, files):
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / ".omi").mkdir()
        (Path(d) / ".omi/structure.md").write_text(mapping, encoding="utf-8")
        for name, text in files.items():
            (Path(d) / name).parent.mkdir(parents=True, exist_ok=True)
            (Path(d) / name).write_text(text, encoding="utf-8")
        return structure.scan(structure.load(d), d, list(files))


def test_import_regexes():
    for exts, pascal, (order, http, use), dom, cross, dom_specs, cross_specs in LANGS:
        n = PASCAL if pascal else LOWER
        mapping = MAP.format(**n)
        for ext in exts:
            hdr = ext in (".c", ".cpp")
            base, orders, cart = f"{n['a']}/{n['m']}", "Orders" if pascal else "orders", "Cart" if pascal else "cart"
            F = f"{base}/{orders}/{n['d']}/{order}{ext}"
            C = f"{base}/{cart}/{n['p']}/{use}{ext}"
            files = {F: dom, C: cross, f"{base}/{orders}/{n['x']}/{n['i']}/{http}{ext}": "",
                     f"{n['a']}/{n['s']}/kernel{ext}": ""}
            if hdr:  # includes name headers
                files = {F: dom, C: cross, f"{base}/{orders}/{n['x']}/{n['i']}/{http}.h": "", f"{base}/{orders}/{n['d']}/{order}.h": ""}
            want = [(F, "direction", s) for s in dom_specs] + [(C, "cross-module", s) for s in cross_specs]
            assert scan(mapping, files) == want, (ext, scan(mapping, files))


def test_unmapped_sql_and_unresolved():
    mapping = MAP.format(**LOWER)
    files = {"stray/x.py": "import app.shared.k\n", "database/0001.sql": "import app.modules.orders.domain.x\n",
             "app/shared/k.py": "import app.modules.orders.domain.zzz\nimport nothing.here\nfrom .. import q\n",
             "app/modules/orders/domain/a.py": "from app.shared import k\n"}
    assert scan(mapping, files) == [("stray/x.py", "unmapped", "-")]
    files["app/shared/k.py"] = "from app.modules.orders.domain import a\n"
    assert scan(mapping, files) == [("stray/x.py", "unmapped", "-"), ("app/shared/k.py", "direction", "app.modules.orders.domain")]


def test_check_command():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / ".omi").mkdir()
        (root / ".omi/structure.md").write_text(MAP.format(**LOWER) + "- .omi/**, .gitignore | config | cfg | imports: -\n", encoding="utf-8")
        (root / "app/shared").mkdir(parents=True)
        (root / "app/shared/k.py").write_text("import os\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)

        def run():
            out = StringIO()
            with redirect_stdout(out):
                return structure.check(root), out.getvalue()
        assert run() == (0, "")
        (root / "stray.py").write_text("", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        assert run() == (1, "stray.py: unmapped: -\n")
        (root / "stray.py").unlink()
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        # a native tool named in the map runs instead of the regex and fails the check with its exit code
        (root / "app/shared/k.py").write_text("import app.modules.orders.domain.x\n", encoding="utf-8")
        (root / "app/modules/orders/domain").mkdir(parents=True)
        (root / "app/modules/orders/domain/x.py").write_text("", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        assert run() == (1, "app/shared/k.py: direction: app.modules.orders.domain.x\n")
        text = (root / ".omi/structure.md").read_text(encoding="utf-8")
        (root / ".omi/structure.md").write_text(text + f'- pyproject.toml | config | tool: "{sys.executable}" -c "print(\'boom\'); raise SystemExit(3)" | imports: -\n', encoding="utf-8")
        (root / "pyproject.toml").write_text("", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        code, out = run()
        assert code == 1 and "boom" in out
        assert "app/shared/k.py: direction" not in out and ".omi/structure.md: tool: " in out


def test_baseline_and_changed():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        sh = lambda *a: subprocess.run(["git", "-c", "user.email=a@b", "-c", "user.name=t", *a], cwd=root, check=True, capture_output=True)
        (root / ".omi").mkdir()
        (root / ".omi/structure.md").write_text(MAP.format(**LOWER) + "- .omi/** | config | cfg | imports: -\n", encoding="utf-8")
        (root / "app/shared").mkdir(parents=True)
        (root / "app/shared/k.py").write_text("import os\n", encoding="utf-8")
        sh("init", "-q", "-b", "development")
        sh("add", "-A")
        sh("commit", "-qm", "base")
        sh("checkout", "-qb", "work")
        (root / "stray.py").write_text("", encoding="utf-8")
        sh("add", "-A")

        def run(**kw):
            out = StringIO()
            with redirect_stdout(out):
                return structure.check(root, **kw), out.getvalue()
        assert run() == (1, "stray.py: unmapped: -\n")
        assert run(baseline=True)[0] == 0
        assert json.loads((root / ".omi/structure-baseline.json").read_text(encoding="utf-8")) == ["stray.py|unmapped|-"]
        sh("add", "-A")
        sh("commit", "-qm", "work")
        assert run() == (0, "")  # baselined violation passes
        (root / "other.py").write_text("", encoding="utf-8")
        sh("add", "-A")
        assert run() == (1, "other.py: unmapped: -\n")  # a new one fails
        assert run(changed=True) == (1, "stray.py: unmapped: -\n")  # baseline does not apply to the diff
        (root / "stray.py").unlink()
        (root / "other.py").unlink()
        sh("add", "-A")
        code, out = run()
        assert code == 0 and "remove from .omi/structure-baseline.json: stray.py|unmapped|-" in out


def test_tool_command():
    tool = lambda cmd: HEAD + f"- pyproject.toml | config | tool: {cmd} | imports: -\n"
    assert "line 6: bad tool command (empty command)" in err(tool(""))
    assert "line 6: bad tool command (empty command)" in err(tool('""'))
    try:
        structure.tool_argv('"" \'\'', posix=False)
        raise AssertionError("no error")
    except ValueError as exc:
        assert str(exc) == "empty command"
    assert "line 6: bad tool command (No closing quotation)" in err(tool('python3 -c "x'))
    assert structure.tool_argv(r"C:\Tools\dep.exe --x", posix=False) == [r"C:\Tools\dep.exe", "--x"]
    assert structure.tool_argv(r'"C:\Program Files\dep.exe" check', posix=False) == [r"C:\Program Files\dep.exe", "check"]
    assert structure.tool_argv("a 'b c'", posix=True) == ["a", "b c"]
    assert load(tool("deptool check"))[0]["tool"] == ["deptool", "check"]
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / ".omi").mkdir()
        (root / "pyproject.toml").write_text("", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)

        def run(cmd):
            (root / ".omi/structure.md").write_text(tool(cmd) + "- .omi/** | config | cfg | imports: -\n", encoding="utf-8")
            out = StringIO()
            with redirect_stdout(out):
                return structure.check(root), out.getvalue()
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        assert run(f'"{sys.executable}" -c pass') == (0, "")  # a tool exiting 0 is clean
        try:
            run("omi-no-such-tool-xyz")
            raise AssertionError("no error")
        except structure.StructureError as exc:
            assert "line 6: cannot run 'omi-no-such-tool-xyz'" in str(exc)


def main():
    test_load_and_errors()
    test_match()
    test_import_regexes()
    test_unmapped_sql_and_unresolved()
    test_check_command()
    test_baseline_and_changed()
    test_tool_command()
