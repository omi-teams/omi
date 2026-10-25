---
id: TASK-026
title: Skill group - stack extensions (UI, QA web, data)
status: planned
depends: TASK-022, TASK-046
scope: .omi/skills/ui/**, .omi/skills/qa-web/**, .omi/skills/data/**, src/omi/template/dot-omi/skills/**, .omi/decisions.md
---
## Goal
Stack-specific skills that load only when a task declares them.

## Acceptance criteria
- [ ] UI: one skill per need after the TASK-020 overlap resolution (Taste MIT, UI UX Pro Max, Vercel web guidelines); accessibility basics included.
- [ ] QA web: browser regression with screenshot evidence, from Playwright CLI (Apache-2.0).
- [ ] Data: query/index/schema/row-level-permission review, from Supabase and PostgreSQL docs; not tied to Supabase.
- [ ] Large reference data (palettes, rule lists) stays in reference files outside SKILL.md and counts toward the task budget only when declared.
- [ ] Each passes `--check`, records source, commit, file, license; catalog regenerated; template copy identical.

- [ ] Every new skill id starts with `omi-` (e.g. `omi-ui-direction`, `omi-web-qa`, `omi-data-review`).

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-029
