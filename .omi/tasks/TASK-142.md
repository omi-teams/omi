---
id: TASK-142
title: Agile squad - ask the PO only on cost, security or real need
status: planned
depends: TASK-121
plan:
scope: src/omi/template/AGENTS.md, src/omi/template/dot-claude/skills/**, src/omi/template/dot-omi/workflows/**, src/omi/project/tasks.py, src/omi/project/workflows.py, src/omi/template_shas.json, AGENTS.md, .claude/skills/**, .omi/workflows/**, tests/test_tools.py, tests/test_tasks.py, tests/test_content.py, .omi/tasks/TASK-142.md
role: omi-agent-engineer
skills: []
refs: []
tool:
model:
effort:
step_settings:
workflow: omi-flow-feature
step:
---
## Goal
In every omi project the squad runs on its own: the Coordinator asks the PO only for extra running cost, high security risk or a call only the PO can make; architecture questions go to the architect role; merges into `development` after review PASS and green CI need no PO question.

## Acceptance criteria
- [ ] `## The PO decides` in the template AGENTS.md lists only: anything that costs extra money, high security risk (auth, secrets, data exposure), product scope changes, UAT, merges into `staging`/`main`, and going past the fix-round limit (enforced in code by TASK-139). It says the Coordinator decides and reports everything else (tool/model/effort, next task, small review nits), architecture questions go to `omi-agent-architect`, and pick-lists are used only for the PO decisions above.
- [ ] `## Task-start tool choice` (AGENTS.md template and omi-task skill): the Coordinator picks tool, concrete model and effort itself, spreads tasks evenly across Claude Code and Codex, records them in the task and states them in its report; no PO question.
- [ ] The `accept` step of `omi-flow-feature`, `-ui`, `-sensitive`, `bugfix` and `refactor` passes without a PO line when the last review-type step passed: `omi step <ID> done` on accept records `Auto accept: review PASS` under `## Steps`. A workflow or task can keep `gate: po` for security-sensitive work: `omi-flow-feature-sensitive` keeps the PO gate. Tested.
- [ ] omi-task skill step 8 continues with the next task (same tool rules) instead of asking the PO; it stops only on a PO decision above, QUOTA, or no planned task.
- [ ] Repo copies match the template; `template_shas.json` updated; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next: supersedes the "Approve / Alternative" wording from TASK-121. PO 2026-10-31: "chỉ hỏi PO những quyết định quan trọng liên quan đến chi phí ..., bảo mật cao, ... merge không cần hỏi khi review đã passed, ... kiến trúc thì hỏi architect".
