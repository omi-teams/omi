---
id: TASK-140
title: Complete first review and host tests before review
status: planned
depends: TASK-139
plan:
scope: src/omi/worker/run.py, src/omi/template/dot-omi/config.json, src/omi/template/dot-omi/agents/omi-agent-reviewer.md, src/omi/template/dot-omi/agents/omi-agent-security-reviewer.md, src/omi/template/AGENTS.md, src/omi/template/dot-claude/skills/omi-task/SKILL.md, src/omi/template_shas.json, .omi/config.json, .omi/agents/**, AGENTS.md, .claude/skills/omi-task/SKILL.md, tests/test_worker.py, tests/test_content.py, .omi/tasks/TASK-140.md
role: omi-agent-engineer
skills: []
refs: []
tool:
model:
effort:
step_settings:
workflow: omi-flow-feature-sensitive
step:
---
## Goal
Reviewers report every finding in round 1 instead of drip-feeding new ones each round, and host-only failures (e.g. Windows) show up before a review round is spent. In TASK-120, every security round found a new case of the same problem, and rounds 2-3 were Windows host failures found only after review PASS.

## Acceptance criteria
- [ ] Reviewer and security-reviewer prompts: round 1 walks a fixed checklist (trust boundaries, host OS differences incl. Windows, interrupt/Ctrl-C and cleanup, file permissions and links, secrets in outputs) and lists every finding at once. A later round only checks the earlier findings were fixed; a new finding there must be tagged `NEW-SEVERE` with a reason why round 1 could not see it, otherwise it goes under `Known issues`, not FAIL.
- [ ] `host_test` in `.omi/config.json` (template default empty = skip). `python -m omi host-test <ID>` runs `host_test` on the host in the worktree; a failure prints `HOST TEST FAILED` plus the output tail, exits non-zero, and records a `Host test FAIL` row that counts toward `max_fix_rounds`. The omi-task skill runs it after the Coordinator's diff check and commit (step 4) and before the reviewer, because the host executes the engineer's code; the AGENTS.md template names that trust boundary. `omi run omi-agent-reviewer` refuses to start while the last host test for the current commit failed or is missing (when `host_test` is set). Tested.
- [ ] The repo's own `.omi/config.json` sets `host_test` to the full test command used for `Host:` checks today.
- [ ] Repo copies match the template; `template_shas.json` updated; all tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next:
