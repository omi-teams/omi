---
id: TASK-078
title: Role prompts and init defaults - scope is write-only, batched NEEDS SCOPE, LF, quiet telemetry, allowlist by stack
status: planned
depends: TASK-077
scope: .omi/agents/**, .omi/skills/**, src/omi/template/**, src/omi/__init__.py, tests/**, docker/**, .claude/skills/omi-idea/SKILL.md
role: omi-agent-engineer
skills: []
refs:
plan: PLAN-001
tool:
model: sonnet
effort: low
workflow: omi-flow-feature
step:
---
## Goal
Gaps #2 #12 #13 #16 #19 #20 (omi-board session 97bfceb1).

## Acceptance criteria
- [ ] #16 #20 `omi-agent-engineer.md` (root and template) says: read any file you need; `scope` limits only what you write; when you need more scope, list every extra path at once in one `NEEDS SCOPE` report, and check which existing tests your change affects. `omi-skill-task-brief` (root and template) reminds the Coordinator to put affected tests in scope.
- [ ] #12 When the tool is codex, `omi run` appends one line to the prompt about known codex worker limits (deleting files with `rm` may be refused: use `git rm` or `python3 -c "import os; os.remove(...)"`). Tested on the codex argv.
- [ ] #19 `omi init` creates `.gitattributes` with `* text=auto eol=lf` when missing (never overwrites). Tested.
- [ ] #13 The proxy (template `docker/proxy.py` and this repo's `docker/proxy.py`) still blocks known codex/claude telemetry hosts (`ab.chatgpt.com`, `*.oaiusercontent.com`, `statsig.anthropic.com`, `sentry.io`) but does not print BLOCKED lines for them. Tested.
- [ ] #2 `.claude/skills/omi-idea/SKILL.md` (root and template) has a stack -> `network_allow` table (npm: registry.npmjs.org; Go: proxy.golang.org, sum.golang.org, storage.googleapis.com; Python: pypi.org, files.pythonhosted.org) and says to propose it to the PO when the stack is chosen.
- [ ] Skill and agent catalogs regenerated; `python -m omi skills --check` passes; all tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next:
