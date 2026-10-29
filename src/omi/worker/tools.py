"""Agent tools (claude, codex): models, efforts, command lines, quota and usage parsing, files the agent read."""

import json
import posixpath
import re
import shlex
import sys
from pathlib import Path

from ..common import core


DEFAULT_MODELS = {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5", "opus": "claude-opus-5-5"}
CODEX_ID = r"(gpt|o\d|codex)[a-zA-Z0-9_.-]*"


def resolve_model(root, model, tool="claude"):
    """Full model ID for an alias from .omi/config.json "models" (codex: "codex_models"; PO-editable); full IDs pass through."""
    cfg = Path(root) / ".omi" / "config.json"
    key, base, full = ("codex_models", {}, CODEX_ID) if tool == "codex" else ("models", DEFAULT_MODELS, r"claude-[a-zA-Z0-9_.-]+")
    models = base | (json.loads(cfg.read_text(encoding="utf-8")).get(key, {}) if cfg.exists() else {})
    if not model:
        sys.exit("no model: pass --model or set `model` in the omi-agent-engineer agent. Nothing changed.")
    resolved = models.get(model, model)
    if isinstance(resolved, str) and resolved != "codex-default" and re.fullmatch(full, resolved):
        return resolved
    sys.exit(f"unknown {tool} model alias '{model}': add a concrete ID to \"{key}\" in .omi/config.json. Nothing changed.")


def resolve_effort(effort: str | None, tool: str) -> str:
    """Require an explicit CLI effort; preserve the selected level."""
    levels = {"low", "medium", "high", "xhigh", "max"}
    if tool == "codex":
        levels |= {"none", "ultra"}
    if effort not in levels:
        sys.exit(f"missing or invalid {tool} effort entry: set `effort` in the task or role, or pass --effort. Nothing changed.")
    return effort


# usage/quota stop messages of each CLI, matched only in its own final error events (not in tool output)
QUOTA_PATTERNS = {
    "claude": r"usage limit reached|hit your (usage )?limit|\d+-hour limit reached|weekly limit reached|credit balance is too low",
    "codex": r"hit your usage limit|usage_limit_reached|insufficient_quota|exceeded your current quota|quota exceeded",
}


def error_texts(tool, out):
    """Error messages from the CLI's own events: claude `result` with is_error, codex `error` / `turn.failed`."""
    texts = []
    for line in (out or "").splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if not isinstance(ev, dict):
            continue
        if tool == "claude" and ev.get("type") == "result" and ev.get("is_error"):
            texts.append(str(ev.get("result") or ""))
        elif tool == "codex" and ev.get("type") in ("error", "turn.failed"):
            err = ev.get("error")
            texts.append(str(ev.get("message") or "") + " " + str(err.get("message") if isinstance(err, dict) else err or ""))
    return texts


def quota_hit(tool, out, rc):
    return bool(rc) and any(re.search(QUOTA_PATTERNS[tool], t, re.I) for t in error_texts(tool, out))


def engineer_cmd(agent_text, task_rel, model=None, effort=None, skills=""):
    m = core.parse(agent_text)
    body = agent_text.split("---", 2)[2].strip() if agent_text.startswith("---") else agent_text
    return ["claude", "-p", f"Task file: {task_rel if task_rel.startswith("/") else "/work/" + task_rel}\nWorktree: /work{skills}",
            "--append-system-prompt", body,
            "--model", model or m.get("model", "sonnet"), "--effort", effort or m.get("effort", "medium"),
            # the container is the boundary, not prompts; project hooks (omi guard) cannot run in it
            "--permission-mode", "bypassPermissions", "--setting-sources", "user", "--output-format", "stream-json", "--verbose"]


CODEX_LIMITS = ("Known codex worker limit: deleting files with `rm` may be refused; use `git rm` "
                "or `python3 -c \"import os; os.remove(...)\"`.")


def codex_cmd(agent_text, task_rel, model, effort, skills=""):
    body = agent_text.split("---", 2)[2].strip() if agent_text.startswith("---") else agent_text
    # the container is the boundary; codex's own sandbox cannot nest in it
    # project_doc_max_bytes=0: codex must not load the Coordinator's AGENTS.md; the role prompt is all it sees
    return ["codex", "exec", "-c", "project_doc_max_bytes=0", "-m", model,
            "-c", f"model_reasoning_effort={effort}",
            "--dangerously-bypass-approvals-and-sandbox", "--json", f"{body}\n\nTask file: {task_rel if task_rel.startswith("/") else "/work/" + task_rel}\nWorktree: /work{skills}\n{CODEX_LIMITS}"]


READERS = ("cat", "sed", "head", "tail", "less", "nl", "rg", "grep")
SHELLS = ("bash", "sh", "zsh", "dash")
# options whose value is the next token (not a file)
VALUE_OPTS = {"head": ("-n", "-c"), "tail": ("-n", "-c"), "grep": ("-A", "-B", "-C", "-m"), "rg": ("-A", "-B", "-C", "-m", "-g", "-t")}


def shell_tokens(command):
    """shlex tokens of a command line; `;`, `&&`, `|`, newlines, `(`, `>` etc. come out as their own tokens."""
    for text in (command, command.replace("'", " ").replace('"', " ")):
        lex = shlex.shlex(text, posix=True, punctuation_chars=";&|()<>\n")
        lex.whitespace, lex.whitespace_split = " \t\r", True
        try:
            return list(lex)
        except ValueError:
            continue
    return []


def read_commands(command, cwd=None):
    """File operands of the read commands (cat, sed, head, ...) in a shell command line; ls, rm, echo do not count.
    Shell wrappers (`/bin/bash -lc '...'`, `env bash -c`) are unwrapped, redirect targets are writes, `sed -i` is
    a write, a grep/rg/sed pattern or script is not a file, and relative paths are resolved against `cd` targets
    (and `cwd`) seen earlier in the command."""
    found, seg = [], []
    for tok in shell_tokens(command) + [";"]:
        if tok and set(tok) <= set(";&|()<>\n") and not set(tok) & set("<>"):
            found += _segment_reads(seg, cwd)
            if seg and seg[0] == "cd" and len(seg) > 1:
                cwd = posixpath.normpath(posixpath.join(cwd or "", seg[1]))
            seg = []
        else:
            seg.append(tok)
    return found


def _segment_reads(toks, cwd):
    """read_commands for one simple command (tokens without separators)."""
    files, words, it = [], [], iter(toks)
    for t in it:
        if t and set(t) <= set("<>&"):
            target = next(it, "")
            if words and words[-1].isdigit():  # fd number of `2>`
                words.pop()
            if t == "<":
                files.append(target)
        else:
            words.append(t)
    while words and (words[0].startswith("-") or re.fullmatch(r"\w+=.*", words[0]) or posixpath.basename(words[0]) == "env"):
        words.pop(0)
    if not words:
        return []
    name, args = posixpath.basename(words[0]), words[1:]
    if name in SHELLS:
        script = next((args[i + 1] for i, a in enumerate(args[:-1]) if re.fullmatch(r"-\w*c\w*", a)), None)
        return read_commands(script, cwd) if script is not None else []
    if name not in READERS:
        return []
    if name == "sed" and any(re.match(r"-\w*i", a) or a.startswith("--in-place") for a in args):
        return []
    operands, pattern, i = [], name in ("grep", "rg", "sed"), 0
    while i < len(args):
        a = args[i]
        if a == "--":
            operands += args[i + 1:]
            break
        if name in ("grep", "rg", "sed") and a in ("-e", "-f", "--regexp", "--expression", "--file"):
            pattern = False
            if a in ("-f", "--file") and i + 1 < len(args):
                operands.append(args[i + 1])
            i += 2
            continue
        if a in VALUE_OPTS.get(name, ()):
            i += 2
            continue
        if not a.startswith("-") or a == "-":
            operands.append(a)
        i += 1
    files += operands[1:] if pattern else operands
    return [posixpath.normpath(posixpath.join(cwd or "", f)) for f in files if f and f != "-"]


def opened_files(tool, out):
    """Paths the agent opened, from the tool-call log: Claude Read calls, file operands of read commands (Claude Bash, Codex)."""
    found = []
    for line in (out or "").splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if not isinstance(e, dict):
            continue
        if tool == "claude" and e.get("type") == "assistant" and isinstance(e.get("message"), dict):
            for c in e["message"].get("content") or []:
                if not isinstance(c, dict) or c.get("type") != "tool_use":
                    continue
                args = c.get("input") or {}
                if c.get("name") == "Read":
                    found.append(str(args.get("file_path") or ""))
                elif c.get("name") == "Bash":
                    found += read_commands(str(args.get("command") or ""))
        elif tool == "codex" and isinstance(e.get("item"), dict) and e["item"].get("type") == "command_execution":
            found += read_commands(str(e["item"].get("command") or ""), e["item"].get("cwd") or e.get("cwd"))
    return found


def parse_usage(tool, out):
    """(result text, input, output, cache) from harness output; numbers are None when it gave none."""
    rows = []
    for line in (out or "").splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            pass
    if not rows and out:
        try:
            rows = [json.loads(out)]
        except ValueError:
            pass
    rows = [r for r in rows if isinstance(r, dict)]
    if tool == "claude":
        r = next((r for r in reversed(rows) if isinstance(r.get("usage"), dict)), None)
        if not r:
            return None, None, None, None
        u = r["usage"]
        return (r.get("result"), u.get("input_tokens"), u.get("output_tokens"),
                (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0))
    done = [r["usage"] for r in rows if r.get("type") == "turn.completed" and isinstance(r.get("usage"), dict)]
    text = next((r["item"].get("text") for r in reversed(rows)
                 if isinstance(r.get("item"), dict) and r["item"].get("type") == "agent_message"), None)
    if not done:
        return text, None, None, None
    return (text, sum(u.get("input_tokens") or 0 for u in done), sum(u.get("output_tokens") or 0 for u in done),
            sum(u.get("cached_input_tokens") or 0 for u in done))


def verdict_of(report):
    """The last `VERDICT: PASS|FAIL` line of a report, or None."""
    found = re.findall(r"^\W*VERDICT:\W*(PASS|FAIL)", report or "", re.M)
    return found[-1] if found else None
