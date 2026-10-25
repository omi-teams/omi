# Verification (TASK-004)

Claude Code 2.1.302, 2026-10-25.

| Check | Result | Evidence |
|---|---|---|
| SessionStart hook injects `omi status` | PASS | Output present at session start with no tool call (coordinator). |
| `engineer` / `reviewer` listed as agent types | PASS | Both appear in the Agent tool's type list. |
| Main checkout Write blocked while worktree exists | PASS | `OMI: src/omi/_guard_probe.py is product code; TASK-004 is running, write inside its worktree.` |
| Engineer model matches frontmatter (`sonnet`) | PASS | System prompt model ID: `claude-sonnet-5-5`. |
| Out-of-scope Write in worktree blocked | PASS | Write `src/omi/_probe.py` -> `OMI: src/omi/_probe.py is outside the scope of TASK-004. Stop and report NEEDS SCOPE to the Coordinator.` File not created. |
| In-scope Write in worktree allowed | PASS | This file, `docs/verification.md`. |
| `/omi-status` `!` injection | PASS | PO typed `/omi-status`; status arrived in the prompt with no tool call. |
| Reviewer model matches frontmatter (`sonnet`, read-only tools) | PASS | Model ID `claude-sonnet-5-5`; tools Read, Grep, Glob, Bash. |

# Verification (TASK-007): resume and Claude-to-Codex handover

Claude Code 2.1.302, Codex 0.164.0 (ChatGPT login, default model, effort low), Windows 11, 2026-10-25.
Throwaway repos, task "add `calc.py` with `add`/`sub` plus tests"; step 1 (`add`) committed in `task/TASK-001` worktree with a Checkpoint, step 2 (`sub`) left undone.

| Check | Result | Evidence |
|---|---|---|
| Claude resume: reads Checkpoint + `omi status` drift | PASS | `claude -p --model haiku "omi-task TASK-001"`: read SKILL.md and task file, said "this is a resume: worktree exists with step 1 done", ran `git status` / `git log development..HEAD` in the worktree. |
| Claude resume: step 1 not redone | PASS | Engineer prompt asked only for `sub()`; diff added only `sub` + `test_sub`; `add` commit untouched. |
| Claude resume: task finished | PASS | Reviewer run, `status: done`, no-remote squash merge into `development`, `python -m unittest` = 2 tests OK. |
| Codex resume: follows AGENTS.md, reads Checkpoint, no redo | PASS | Ran `python -m omi status`, read the omi-task skill and agent files, verified worktree vs checkpoint, replied in Vietnamese per AGENTS.md; never touched `add`. |
| Codex runs roles with `codex exec` | FAIL then PASS after fix | Before: with `codex` not on PATH, Codex used its built-in subagents (collab_tool_call) or stopped. After the AGENTS.md fix: `where.exe codex` failed, it located the exe and launched `codex exec ... 'Act as engineer. Follow .claude/agents/engineer.md ...'`. |
| Codex finishes the task end to end | FAIL (environment) | Not reached. Codex's Windows `workspace-write` sandbox: `.git` of the worktree is read-only (`index.lock: Permission denied`, cannot commit), nested `codex exec` cannot find its home dir. Not an AGENTS.md issue. |

## Failures and notes
- First Codex runs failed on sandbox, not instructions: `python` not on PATH (fixed by `-c windows.sandbox="unelevated"`), "dubious ownership" git error.
- `--dangerously-skip-permissions` / `danger-full-access` were not used (blocked by the session's safety classifier), so Codex end-to-end completion is unverified. Needs a PO run with approvals or full access: `codex exec -s danger-full-access "omi-task TASK-001"` in a sandbox repo.
- Claude run needed `--permission-mode acceptEdits --allowedTools "Bash(git:*) Bash(python:*) Agent Read Edit Write Glob Grep"`; haiku's engineer sub-run was denied some Bash and the coordinator completed the tests and commits itself.
- Fix: `src/omi/template/AGENTS.md` Roles line now says to run roles via the shell command `codex exec` (never built-in subagents) and to locate `codex` with `where.exe codex` (Windows) or `command -v codex` if not on PATH. Root `AGENTS.md` carries the same line.
