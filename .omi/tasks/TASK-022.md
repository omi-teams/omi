---
id: TASK-022
title: Skill standard, validator and authoring skill
status: in-progress
depends: TASK-021
scope: src/omi/__init__.py, src/omi/template/**, .omi/skills/authoring/**, tests/**, .omi/skills/CATALOG.md
---
## Goal
Every omi-skill follows one contract and is checked by a command, so quality does not depend on the author.

## Acceptance criteria
- [ ] Contract (frontmatter + sections): id, group, when to use / not use, inputs, steps, outputs and evidence, stop/escalate conditions, tools needed, tokens, source (repo, commit/tag, file, license, use = reference|adapt|rewrite).
- [ ] `python -m omi skills --check` validates every skill: required parts present, size under the 2000-token cap, source recorded, no skill that widens permissions or scope.
- [ ] Skill `authoring/write-skill` (adapted from Anthropic skill-creator, Apache-2.0, notice kept) fits the 2000-token cap and covers: trigger wording, short body, references split out, and a baseline comparison before acceptance.
- [ ] Tests cover a valid skill and each failure; `python tests/test_omi.py` passes.

## Checkpoint
Done: contract + validate_skill/check_all_skills + `skills --check` in src/omi/__init__.py; authoring/write-skill; test_skills_check.
Not done: nothing.
Tests: python3 tests/test_omi.py ok
Review round 1: all 4 fixes done (source_ref check + tests, pinned SHA, notice, ponytail comment). tests ok, skills --check ok.
Next: TASK-023

## Review round 1 (fix these, nothing else)
1. `skills --check` must reject `source_ref` that is a branch name (main, master, develop, trunk, HEAD) or anything that is neither a 7-40 char hex SHA nor a tag like `v1.2`/`1.2.3`; add a test case.
2. Pin `write-skill` to anthropics/skills commit dbd4588f9e1033efb41dad4bef2f7947c8993d44 (upstream skill file: skills/skill-creator/SKILL.md).
3. Notice in write-skill: add the license URL https://www.apache.org/licenses/LICENSE-2.0; do not invent a copyright line - write "Copyright Anthropic, PBC (see upstream LICENSE.txt at the pinned commit)".
4. Add a `# ponytail:` comment on the widening-phrase check: heuristic, weak against evasion; the frontmatter key check is the real guard.
