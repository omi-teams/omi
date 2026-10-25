---
id: TASK-011
title: Distill core omi-skills from pilot gaps
status: planned
depends: TASK-009
scope: src/omi/template/dot-claude/skills/**, src/omi/template/AGENTS.md, .omi/decisions.md
---
## Goal
Add only the skills and workflows the TASK-009 pilot proved missing, distilled from the sources in `../omi-squad/docs/research/omi-skills-reference-landscape.md`, with source, commit and license recorded.

## Acceptance criteria
- [ ] Each new skill cites a concrete pilot gap; nothing is added speculatively.
- [ ] Each skill records its source repo, commit/tag, file and license; CC-BY-SA content is either attributed or rewritten.
- [ ] Candidates considered include core skills (brainstorm/AC, verification, diff security review) and the change-request workflow; rejected ones are logged in `.omi/decisions.md` with the reason.
- [ ] Skills load on demand; AGENTS.md grows by at most a few lines.

## Checkpoint
Done:
Not done:
Tests:
Next:
