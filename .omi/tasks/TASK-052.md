---
id: TASK-052
title: Skill budget by tokens only
status: in-progress
depends: TASK-044
scope: src/omi/__init__.py, tests/**, AGENTS.md, src/omi/template/**, .omi/tasks/_template.md, .omi/skills/workflow/omi-skill-task-brief/**
role: omi-agent-engineer
skills: []  # step build adds omi-skill-lean-implementation
workflow: omi-flow-feature
step: build
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
Done: count limit removed (code, texts, template copies); tests updated; review round 1 findings fixed (total-over-6000 case in check_skills test and in workflow step test via get_workflow, which `omi step` uses)
Not done: -
Tests: python3 tests/test_omi.py ok
Next: review

## Steps
- plan started 2026-10-25 23:10
- plan done 2026-10-25 23:10
- build started 2026-10-25 23:10
- build done 2026-10-25 23:21
- review started 2026-10-25 23:21
- review failed 2026-10-25 23:22
- build started 2026-10-25 23:22

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 0 | 0 | 0 | 201s | 0/1 | - |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 18 | 2649 | 211364 | 48s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 10 | 1951 | 122083 | 38s | - | PASS bbc37dc |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 16 | 2119 | 182212 | 34s | 1/1 omi-skill-lean-implementation | - |
