---
id: TASK-052
title: Skill budget by tokens only
status: planned
depends: TASK-044
scope: src/omi/__init__.py, tests/**, AGENTS.md, src/omi/template/**, .omi/tasks/_template.md, .omi/skills/workflow/omi-skill-task-brief/**
role: omi-agent-engineer
skills: []  # step build adds omi-skill-lean-implementation
workflow: omi-flow-feature
step:
---
## Goal
A run's skills are limited by tokens only (2000 per skill, 6000 per run); the "3 skills" count limit is gone.

### Brief
- `src/omi/__init__.py:70` `SKILL_LIMITS`: drop `"skills": 3` and the check that raises "N skills declared, at most 3" in `check_skills`; keep `tokens` and `skill_tokens` and the `.omi/config.json` `"skill_limits"` override (an old `"skills"` key there is ignored, not an error).
- Text: `AGENTS.md` line 19 "Budget: 3 skills, 6000 tokens" -> "Budget: 6000 tokens per run, 2000 per skill"; same in `src/omi/template/AGENTS.md` (identical); `.omi/tasks/_template.md` and its template copy `skills:` comment; `omi-skill-task-brief` step 7 "at most 3 `skills`" -> "skills within the token budget" (root `.omi/skills/...` and template copy identical; run `python -m omi skills --check`).
- Tests: `python3 tests/test_omi.py`; replace the 4-skills refusal test with one that 4 small skills pass and a 6001-token total fails.

## Acceptance criteria
- [ ] No skill-count limit in code or text; token limits unchanged and still enforced (tests).
- [ ] Root and template copies identical; `python -m omi skills --check` passes.
- [ ] `python3 tests/test_omi.py` passes.

## Checkpoint
Done:
Not done:
Tests:
Next:
