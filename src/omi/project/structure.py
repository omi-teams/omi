"""Structure map: parse .omi/structure.md and match file paths to layer, module and responsibility."""

import re
from pathlib import Path

from ..common import core

LAYERS = ("domain", "application", "adapter-in", "adapter-out", "platform", "shared", "data", "docs", "test", "config")
MAP = ".omi/structure.md"


class StructureError(ValueError):
    """The map is malformed; the message lists every problem with its line number."""


def _glob(pattern):
    """Compiled regex for a glob: ** crosses '/', * and ? do not; the first * after modules/ is group 'module'."""
    out, named, i = [], False, 0
    while i < len(pattern):
        if pattern.startswith("**", i):
            out.append(".*")
            i += 2
            continue
        c = pattern[i]
        if c == "*":
            if not named and pattern[:i].endswith("modules/"):
                out.append("(?P<module>[^/]+)")
                named = True
            else:
                out.append("[^/]*")
        else:
            out.append("[^/]" if c == "?" else re.escape(c))
        i += 1
    return re.compile("".join(out))


def _rule(line, no, errors):
    parts = [p.strip() for p in line[2:].split("|")]
    if len(parts) != 4 or not all(parts[:3]) or not parts[3].startswith("imports:"):
        errors.append(f"line {no}: expected '- <glob>[, <glob>] | <layer> | <responsibility> | imports: <layers>'")
        return None
    globs, layer, resp, imports = parts[0], parts[1], parts[2], parts[3].removeprefix("imports:").strip()
    if layer not in LAYERS:
        errors.append(f"line {no}: unknown layer '{layer}'")
        return None
    if not imports:
        errors.append(f"line {no}: empty imports field (use '-' for none)")
        return None
    allowed = [] if imports == "-" else core.split(imports)
    bad = [x for x in allowed if x not in LAYERS]
    if bad:
        errors.append(f"line {no}: unknown layer '{bad[0]}' in imports")
        return None
    return {"globs": core.split(globs), "layer": layer, "responsibility": resp, "imports": allowed,
            "line": no, "_re": [_glob(g) for g in core.split(globs)]}


def load(root) -> list[dict]:
    """Rules of <root>/.omi/structure.md in file order; raises StructureError on any format problem."""
    path = Path(root) / MAP
    try:
        text = core.read_task(path)
    except OSError as exc:
        raise StructureError(f"{MAP}: cannot read ({exc.strerror or exc})") from exc
    if core.parse(text).get("id") != "structure":
        raise StructureError(f"{MAP}: frontmatter must have 'id: structure'")
    rules, errors = [], []
    body = text.split("---", 2)[2] if text.startswith("---") and text.count("---") >= 2 else text
    first = text.count("\n", 0, len(text) - len(body)) + 1
    for no, line in enumerate(body.splitlines(), first):
        if line.lstrip().startswith("- "):
            rule = _rule(line.strip(), no, errors)
            if rule:
                rules.append(rule)
    if errors:
        raise StructureError(f"{MAP}: " + "; ".join(errors))
    return rules


def match(rules, path) -> dict | None:
    """First rule whose glob matches the repo-relative path: {layer, module, responsibility}, else None."""
    path = str(path).replace("\\", "/").removeprefix("./")
    for rule in rules:
        for rx in rule["_re"]:
            m = rx.fullmatch(path)
            if m:
                return {"layer": rule["layer"], "module": m.groupdict().get("module"),
                        "responsibility": rule["responsibility"]}
    return None
