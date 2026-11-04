import tempfile
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


def main():
    test_load_and_errors()
    test_match()
