---
id: TASK-085
title: Per-step tool/model/effort in a task, and omi upgrade adds .gitattributes
status: in-progress
depends:
plan: PLAN-001
scope: src/omi/__init__.py, tests/test_omi.py, .omi/tasks/_template.md, src/omi/template/dot-omi/tasks/_template.md, AGENTS.md, src/omi/template/AGENTS.md, README.md
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: sonnet
effort: medium
workflow: omi-flow-feature
step: build
---
## Goal
Close the open parts of gaps #9 and #19 (omi-board session 97bfceb1) before releasing 0.3.0. #9: TASK-083 lets the task's own role use the task's tool/model/effort, but other steps (architect, security) still need `--tool/--model/--effort` typed by hand. #19: `omi init` creates `.gitattributes`, but `omi upgrade --apply` does not, so existing projects never get it.

## Acceptance criteria
- [ ] A task can set `step_settings: <step>=<tool>/<model>/<effort>, ...` in its frontmatter (one line, e.g. `step_settings: architect=codex/opus/high, security=claude/opus/high`; any of the three parts may be empty, e.g. `review=claude//`). When `omi run <role> <ID>` runs the role of the task's current step and that step id is listed, those values are used. Precedence: `--tool/--model/--effort` > step_settings of the current step > task `tool/model/effort` (write role or the task's own role, as today) > role file > defaults. A malformed entry stops with a message showing the expected form. Tested, including a read role (architect, security-reviewer) and precedence.
- [ ] `omi upgrade --apply` creates `.gitattributes` with `* text=auto eol=lf` when missing and never overwrites an existing one (same rule as `omi init`, one shared helper). Tested.
- [ ] Both `_template.md` copies document `step_settings:` in one comment line; AGENTS.md (root and template) "Tool per run" sentence mentions it in the precedence order; README one line.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done: Addressed review round 1: protected `tool` and `step_settings` in FRONT_OWNED, validated every configured step against the task workflow (including tasks without a current step), and corrected the Vietnamese README model and quota guidance. Added regression coverage for reverted tool/later-step settings, unknown step ids with the workflow's valid ids, and README corrections. Existing acceptance tests cover read roles, precedence, shared create-only .gitattributes behavior, and both documentation copies.
Not done: Windows host validation of these review fixes (Linux container only); Coordinator previously reported the pre-review implementation passed on Windows.
Tests: PASS — targeted test_step_settings_format_and_docs and test_tool_choice_and_quota_switch; PASS — python3 tests/test_omi.py (exit 0, final ok).
Next: Coordinator reviews the scoped diff, runs the final suite on Windows, and commits on the host.

## Steps
- plan started 2026-10-27 11:18
- plan done 2026-10-27 11:18
- build started 2026-10-27 11:18
- build done 2026-10-27 11:24
- review started 2026-10-27 11:24
- review failed 2026-10-27 11:27
- build started 2026-10-27 11:27

## Reports
2026-10-27 11:22 omi-agent-engineer (codex):
> DONE — implementation complete; checkpoint updated; no commit.
> Files: src/omi/__init__.py, tests/test_omi.py, both task templates, both AGENTS.md files, README.md, TASK-085.md.
> Suggested commit: `feat: support per-step run settings and upgrade gitattributes`
> Tests: full Linux suite passed; additional precedence regression tests passed.
> Open issue: Windows host validation remains for Coordinator.
2026-10-27 11:23 hook post-run passed:
> [... truncated ...]
> ok
2026-10-27 11:26 omi-agent-reviewer (claude):
> VERDICT: FAIL
> - src/omi/__init__.py:592 `step_settings` is missing from `FRONT_OWNED`. The template calls it "Coordinator-owned", but `revert_front` won't restore it if an agent edits it. `model` and `effort` are protected, and `tool` is not (existing gap). An agent could rewrite `step_settings` in its task file and change the tool, model or effort of later steps. -> Add `"step_settings"` to `FRONT_OWNED` and add a test that an agent edit gets reverted, like the existing `model: haiku` revert test. Consider adding `tool` too.
> - src/omi/__init__.py:2227 `parse_step_settings` accepts only lowercase `[a-z0-9-]` step ids and never checks that an id exists in the task's workflow. A typo such as `architet=codex//` is silently ignored and the run uses other settings. -> Optionally warn or stop when a listed step id isn't in the workflow (low severity).
> 
> AC: Per-step `step_settings` with precedence and malformed-entry error ✓ `parse_step_settings` and `run_role` (`__init__.py:2192-2285`) apply CLI > current-step > eligible task > role. Tests cover architect and security (read roles), each CLI field overriding alone, empty parts inheriting, non-current steps and roles being ignored, and malformed input exiting with the expected form. One uncovered edge: a role that is not the task's own role and not the current step's role ignores `step_settings`, which matches the spec.
> AC: `omi upgrade --apply` creates `.gitattributes` without overwriting ✓ the shared `ensure_gitattributes` is used by both `init` and `upgrade_apply`. `test_upgrade_gitattributes` checks that it creates the file and keeps a custom one.
> [... truncated ...]
> Scope: all changed files are in `scope`, plus the task file (normal). The `## Reports` section of the task file contains junk hook output ("create AGENTS.md…", a Docker port conflict) that should be cleaned up.
2026-10-27 11:29 omi-agent-engineer (codex):
> DONE — addressed all review fixes; checkpoint updated.
> Files changed: `src/omi/__init__.py`, `tests/test_omi.py`, `README.md`, `.omi/tasks/TASK-085.md`.
> Suggested commit: `fix: protect and validate per-step run settings`
> Tests: Linux full suite and targeted regression tests PASS.
> Open issue: final Windows host validation remains for Coordinator. No commit made.
2026-10-27 11:31 hook post-run passed:
> Conflict. The container name "/tmpv_bsaux5-TASK-001-engineer-codex-gpt-x-medium-042945" is already in useBind for 0.0.0.0:8080 failed: port is already in usecreate AGENTS.md
> create docker/Dockerfile
> create docker/prove.sh
> create docker/proxy.py
> create .claude/settings.json
> create .claude/skills/omi-idea/SKILL.md
> create .claude/skills/omi-release/SKILL.md
> create .claude/skills/omi-status/SKILL.md
> create .claude/skills/omi-task/SKILL.md
> create .claude/skills/omi-upgrade/SKILL.md
> create .omi/agents/omi-agent-architect.md
> create .omi/agents/omi-agent-designer-ui.md
> create .omi/agents/omi-agent-devops.md
> create .omi/agents/omi-agent-docs-writer.md
> create .omi/agents/omi-agent-engineer.md
> create .omi/agents/omi-agent-qa-tester.md
> create .omi/agents/omi-agent-researcher.md
> create .omi/agents/omi-agent-reviewer.md
> create .omi/agents/omi-agent-security-reviewer.md
> create .omi/hooks/post-run.sh
> create .omi/plans/PLAN-000.md
> create .omi/references/nextjs-app-router.md
> create .omi/references/postgres-conventions.md
> create .omi/rules/docker.md
> create .omi/rules/go.md
> create .omi/rules/nextjs.md
> create .omi/rules/postgres.md
> create .omi/rules/python.md
> create .omi/skills/.gitkeep
> create .omi/skills/data/omi-skill-data-review/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-docker-worker-pitfalls/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-incident/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-release-checklist/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-rollback/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-windows-powershell/SKILL.md
> create .omi/skills/qa-web/omi-skill-web-qa/SKILL.md
> create .omi/skills/quality/omi-skill-ci-workflow-audit/SKILL.md
> create .omi/skills/quality/omi-skill-debug-root-cause/SKILL.md
> create .omi/skills/quality/omi-skill-diff-security-review/SKILL.md
> create .omi/skills/quality/omi-skill-simplify-review/SKILL.md
> create .omi/skills/quality/omi-skill-verify-evidence/SKILL.md
> create .omi/skills/ui/omi-skill-ui-a11y-review/SKILL.md
> [... truncated ...]
> ok

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 980713 | 8138 | 946048 | 232s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 8 | 2242 | 118798 | 129s | - | FAIL ef7965e |
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 551745 | 3723 | 518912 | 150s | 1/1 omi-skill-lean-implementation | - |
