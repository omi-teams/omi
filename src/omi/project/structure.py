"""Structure map: parse .omi/structure.md and match file paths to layer, module and responsibility."""

import bisect
import posixpath
import re
import shlex
import subprocess
from pathlib import Path

from ..common import core

LAYERS = ("domain", "application", "adapter-in", "adapter-out", "platform", "shared", "data", "docs", "test", "config")
MAP = ".omi/structure.md"


class StructureError(ValueError):
    """The map is malformed; the message lists every problem with its line number."""


def _glob(pattern):
    """Compiled regex for a glob: ** crosses '/', * and ? do not; the first * after modules/ (any case) is group 'module'."""
    out, named, i = [], False, 0
    while i < len(pattern):
        if pattern.startswith("**", i):
            out.append(".*")
            i += 2
            continue
        c = pattern[i]
        if c == "*":
            if not named and pattern[:i].lower().endswith("modules/"):
                out.append("(?P<module>[^/]+)")
                named = True
            else:
                out.append("[^/]*")
        else:
            out.append("[^/]" if c == "?" else re.escape(c))
        i += 1
    return re.compile("".join(out))


def _rule(line, no, errors):
    parts = [p.strip() for p in line[2:].split("|")] if line.startswith("- ") else []
    if len(parts) != 4 or not core.split(parts[0]) or not all(parts[:3]) or not parts[3].startswith("imports:"):
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
        if line.lstrip().startswith("-"):
            rule = _rule(line.strip(), no, errors)
            if rule:
                rules.append(rule)
    if errors:
        raise StructureError(f"{MAP}: " + "; ".join(errors))
    return rules


def _hit(rules, path):
    path = str(path).replace("\\", "/").removeprefix("./")
    for rule in rules:
        for rx in rule["_re"]:
            m = rx.fullmatch(path)
            if m:
                return rule, m.groupdict().get("module")
    return None, None


def match(rules, path) -> dict | None:
    """First rule whose glob matches the repo-relative path: {layer, module, responsibility}, else None."""
    rule, module = _hit(rules, path)
    return rule and {"layer": rule["layer"], "module": module, "responsibility": rule["responsibility"]}


_JS = r"""(?:\bfrom\s*|\bimport\s*\(?\s*|\brequire\s*\(\s*)['"]([^'"]+)['"]"""
_PHP_REQ = r"""(?:require|include)(?:_once)?\s*\(?\s*['"]([^'"]+)['"]"""
# ext -> [(regex, mode)]; modes: py, dotted (. \ :: separators), path (file path), rust
IMPORTS = {}
for _exts, _res in (
        (".py", [(r"^\s*(?:from\s+(\.*[\w.]*)\s+import\b|import\s+([\w.]+))", "py")]),
        (".js .jsx .ts .tsx .mjs .cjs", [(_JS, "path")]),
        (".go", [(r'^\s*(?:import\s+)?(?:[\w.]+\s+)?"([^"]+)"', "path")]),
        (".java .kt", [(r"^\s*import\s+(?:static\s+)?([\w.]+)", "dotted")]),
        (".cs", [(r"^\s*using\s+(?:static\s+)?([\w.]+)\s*;", "dotted")]),
        (".php", [(r"^\s*use\s+(?:function\s+|const\s+)?([\\\w]+)", "dotted"), (_PHP_REQ, "path")]),
        (".rs", [(r"^\s*(?:pub\s+)?use\s+((?:crate|super|self)(?:::\w+)*)", "rust")]),
        (".rb", [(r"""^\s*require(?:_relative)?\s+['"]([^'"]+)['"]""", "path")]),
        (".c .h .cc .cpp .hpp", [(r'^\s*#\s*include\s+"([^"]+)"', "path")])):
    for _e in _exts.split():
        IMPORTS[_e] = [(re.compile(r, re.M), m) for r, m in _res]
RELATIVE_FIRST = {".rb": True, ".php": True, ".c": True, ".h": True, ".cc": True, ".cpp": True, ".hpp": True}
LEADING_DROP = {".go", ".java", ".kt", ".cs", ".php"}  # package names carry a prefix the repo path lacks
TRAILING_DROP = {".java", ".kt", ".cs", ".php", ".rs"}  # the last segment may be a class or item


def _roots(rules):
    """'' and every ancestor of the literal directory prefix of each map glob (the package roots)."""
    roots = {""}
    for rule in rules:
        for g in rule["globs"]:
            parts = g.split("/")[:-1]
            for i, seg in enumerate(parts):
                if re.search(r"[*?]", seg):
                    parts = parts[:i]
                    break
            roots.update("/".join(parts[:n]) for n in range(1, len(parts) + 1))
    return sorted(roots)


class _Files:
    """Tracked paths: find(path-without-extension) -> a tracked file that path names, else None."""

    def __init__(self, files):
        self.set, self.sorted = set(files), sorted(files)

    def find(self, p):
        if not p or p.startswith("../") or p == "..":
            return None
        if p in self.set:
            return p
        for ext in IMPORTS:
            if p + ext in self.set:
                return p + ext
        i = bisect.bisect_left(self.sorted, p + "/")
        return self.sorted[i] if i < len(self.sorted) and self.sorted[i].startswith(p + "/") else None


def _targets(ext, mode, spec, path, roots):
    """Candidate repo paths (without extension) for an import string, best first."""
    here = posixpath.dirname(path)
    rel, absolute = [], []
    if mode == "py":
        dots = len(spec) - len(spec.lstrip("."))
        parts = [x for x in spec.lstrip(".").split(".") if x]
        if dots and not parts:
            return []  # `from . import x` names the target only after `import`: unresolvable
        if dots:
            base = here
            for _ in range(dots - 1):
                base = posixpath.dirname(base)
            rel = [posixpath.join(base, *parts)]
        else:
            absolute = parts
    elif mode == "rust":
        head, *parts = spec.split("::")
        if head == "crate":
            absolute = parts
        else:
            rel = [posixpath.join(posixpath.dirname(here) if head == "super" else here, *parts)]
    elif mode == "dotted":
        absolute = [x for x in re.split(r"[.\\]|::", spec) if x]
    else:
        if spec.startswith(".") or RELATIVE_FIRST.get(ext):
            rel = [posixpath.normpath(posixpath.join(here, spec))]
        absolute = [x for x in spec.split("/") if x and x != "."] if not spec.startswith(".") else []
    out = list(rel)
    starts = range(len(absolute)) if ext in LEADING_DROP else range(1)
    for lead in starts:
        segs = absolute[lead:]
        ends = range(len(segs), 0, -1) if ext in TRAILING_DROP else range(len(segs), len(segs) + 1)
        for end in ends:
            out.extend(posixpath.join(r, *segs[:end]) for r in roots if segs[:end])
    return out


def _found(files, ext, mode, spec, path, roots):
    for cand in _targets(ext, mode, spec, path, roots):
        hit = files.find(posixpath.normpath(cand))
        if hit:
            return hit
    return None


def scan(rules, root, paths) -> list[tuple[str, str, str]]:
    """(path, rule, import) violations for the repo-relative paths: unmapped, direction, cross-module."""
    files, roots, found = _Files(paths), _roots(rules), []
    tool = any(r["layer"] == "config" and r["responsibility"].startswith("tool:") for r in rules)
    for path in paths:
        src, module = _hit(rules, path)
        if src is None:
            found.append((path, "unmapped", "-"))
            continue
        ext = posixpath.splitext(path)[1]
        if tool or ext not in IMPORTS:
            continue
        try:
            text = (Path(root) / path).read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        for rx, mode in IMPORTS[ext]:
            for m in rx.finditer(text):
                spec = next(g for g in m.groups() if g)
                hit = _found(files, ext, mode, spec, path, roots)
                dst = match(rules, hit) if hit and hit != path else None
                if dst is None:
                    continue  # external or unresolvable
                if dst["layer"] not in src["imports"]:
                    found.append((path, "direction", spec))
                if module and dst["module"] and module != dst["module"] and dst["layer"] != "application":
                    found.append((path, "cross-module", spec))
    return list(dict.fromkeys(found))


def check(code, state=None) -> int:
    """Print `<path>: <rule>: <import>` per violation of the map over git-tracked files; 0 when clean, else 1."""
    code = Path(code)
    rules = load(state or code)
    listed = core.git(code, "ls-files")
    if listed is None:
        raise StructureError(f"{code}: not a git repository")
    paths = [p for p in listed.splitlines() if (code / p).is_file()]
    found = scan(rules, code, paths)
    for rule in rules:
        if rule["layer"] == "config" and rule["responsibility"].startswith("tool:"):
            cmd = rule["responsibility"].removeprefix("tool:").strip()
            try:
                r = subprocess.run(shlex.split(cmd), cwd=code, capture_output=True, encoding="utf-8", errors="replace")
            except OSError as exc:
                raise StructureError(f"{MAP} line {rule['line']}: cannot run '{cmd}' ({exc.strerror or exc})") from exc
            if r.returncode:
                print((r.stdout + r.stderr).rstrip())
                found.append((MAP, "tool", cmd))
    for line in found:
        print(": ".join(line))
    return 1 if found else 0
