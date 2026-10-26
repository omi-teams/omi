---
id: TASK-072
title: Coordinator picks model and effort per task in the task file
status: done
depends: TASK-071
scope: src/omi/__init__.py, tests/**, src/omi/template/**, .omi/tasks/_template.md, AGENTS.md
role: omi-agent-engineer
skills: []
tool:
workflow: omi-flow-feature
step: accept
---
## Goal
The Coordinator records its model choice in the task file (`model:` alias haiku|sonnet|opus or a full ID, `effort:`), so it survives resume and the quota switch; `omi run` resolves the alias for whichever tool runs. Order: `omi run --model/--effort` > task `model/effort` > role.

## Acceptance criteria
- [x] `model:` and `effort:` in the task frontmatter override the role's; `--model/--effort` override both. Tested for claude and codex.
- [x] An alias resolves through `models` for claude and `codex_models` for codex, also after a quota switch to the other tool; the container name and the Usage row show the resolved model, not the alias. Tested.
- [x] A codex alias missing from `codex_models` still runs with `codex-default` and `omi run` prints one warning line naming the alias. Tested.
- [x] `model` and `effort` are in `.omi/tasks/_template.md` (root and template) and are Coordinator-owned frontmatter (agents cannot change them).
- [x] Template and root `AGENTS.md` say in one line that the Coordinator sets `model`/`effort` per task from the quota rules.
- [x] A task's `tool:` (and `model`/`effort`) apply only to its write role (the implementer); read roles such as the reviewer keep their role's tool, so a codex-built task gets a claude review by default. `omi run --tool` still overrides. Tested.
- [x] When an agent CLI exits non-zero for a reason other than a usage limit, `omi run` prints its error events (claude `result` is_error, codex `error`/`turn.failed`) and the exit code, and writes them to `## Reports`. Tested.
- [x] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Review round 1 PASS; the PO asked to fix two small points first (PO: "Sửa 2 điểm nhỏ trước"). Windows host: tests ok (Coordinator).
- Quota-switch fallback: after `models[other] = resolve_model(main, am.get("model"), other)` also warn when it resolved to `codex-default`, naming the alias actually used (`am.get("model")`). Test: task model is a full claude ID, claude hits its limit, role alias missing from `codex_models` -> one WARNING naming that alias.
- Test the codex error path: a codex run exiting non-zero with an `error` event and a `turn.failed` event (not a usage limit) prints both messages and `exit code N`, and writes them to `## Reports`.
Done: all criteria implemented + tested; both review-round fixes (fallback warning, codex error-path test) done.
Not done: -
Tests: python3 tests/test_omi.py ok (Linux worker and Windows host).
Next: Coordinator review/commit.

## Steps
PO approval accept: Nghiệm thu, merge (Recommended)
- plan started 2026-10-26 14:32
- plan done 2026-10-26 14:32
- build started 2026-10-26 14:32
- build done 2026-10-26 14:34
- review started 2026-10-26 14:34
- review failed 2026-10-26 14:36
- build started 2026-10-26 14:36
- build done 2026-10-26 14:37
- review started 2026-10-26 14:37
- review done 2026-10-26 14:39
- accept started 2026-10-26 14:39
- accept done 2026-10-26 14:39

## Reports
2026-10-26 14:34 omi-agent-engineer (claude):
> DONE (not run on the Windows host; the Linux tests pass).
> 
> - **Files changed:** `src/omi/__init__.py`, `tests/test_omi.py`, `.omi/tasks/_template.md`, `src/omi/template/dot-omi/tasks/_template.md`, `AGENTS.md`, `src/omi/template/AGENTS.md`, `.omi/tasks/TASK-072.md` (Checkpoint).
> - **Behaviour:**
>   - **Precedence:** a write role now takes `tool`, `model` and `effort` in the order `omi run` flags, then the task file, then the role. A read role keeps its own `tool` and ignores the task's `model`/`effort`.
>   - **Coordinator-owned:** `model` and `effort` are now Coordinator-owned frontmatter, so agent edits to them are reverted.
>   - **Codex alias:** a codex alias missing from `codex_models` runs with `codex-default` and prints one `WARNING` line naming the alias. This also covers the switch after a quota hit.
>   - **Failures:** when the CLI exits non-zero for a reason other than a usage limit, `omi run` prints its error events and `exit code N`, and writes both to `## Reports`.
> - **Docs:** one `AGENTS.md` line in each copy (root and template) says the Coordinator sets `model`/`effort` per task. `model:` and `effort:` are added to both task templates.
> - **Tests:** `python3 tests/test_omi.py` passes on Linux. New cases are in `test_tool_choice_and_quota_switch`.
> - **Commit message:** `feat(run): Coordinator sets model and effort per task; surface CLI errors`
> - **Open issue:** the Windows host test run is still needed.
2026-10-26 14:34 hook post-run passed:
> Conflict. The container name "/tmpwjc5grup-TASK-001-engineer-codex-gpt-x-medium-073410" is already in useBind for 0.0.0.0:8080 failed: port is already in usewrote /tmp/tmp8mmyb4c2/.omi/skills/CATALOG.md (2 skills)
> create AGENTS.md
> create docker/Dockerfile
> create docker/__pycache__/proxy.cpython-313.pyc
> create docker/prove.sh
> create docker/proxy.py
> create .claude/settings.json
> create .claude/skills/omi-idea/SKILL.md
> create .claude/skills/omi-release/SKILL.md
> create .claude/skills/omi-status/SKILL.md
> create .claude/skills/omi-task/SKILL.md
> create .omi/agents/CATALOG.md
> create .omi/agents/omi-agent-architect.md
> create .omi/agents/omi-agent-designer-ui.md
> create .omi/agents/omi-agent-devops.md
> create .omi/agents/omi-agent-docs-writer.md
> create .omi/agents/omi-agent-engineer.md
> create .omi/agents/omi-agent-qa-tester.md
> create .omi/agents/omi-agent-researcher.md
> create .omi/agents/omi-agent-reviewer.md
> create .omi/agents/omi-agent-security-reviewer.md
> create .omi/config.json
> create .omi/decisions.md
> create .omi/hooks/post-run.sh
> create .omi/plans/CATALOG.md
> create .omi/plans/PLAN-000.md
> create .omi/references/CATALOG.md
> create .omi/references/nextjs-app-router.md
> create .omi/references/postgres-conventions.md
> create .omi/rules/CATALOG.md
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
> [... truncated ...]
> ok
2026-10-26 14:35 omi-agent-reviewer (claude):
> VERDICT: PASS
> - src/omi/__init__.py:~1994 The quota-switch fallback (`resolve_model(main, am.get("model"), other)`) can return `codex-default` for the role's alias with no warning. This happens when the task or flag model is a full claude ID, and the role's alias is missing from `codex_models`. The "missing codex alias" warning is not printed on that path. -> Call `warn_default(other)` after the fallback assignment, using the alias that was resolved.
> - src/omi/__init__.py:1858 `write = am["access"] == "write"` treats any non-write access value as a read role, so it ignores the task's tool, model and effort. This is correct for the current roles (write and read). -> No change needed unless a third access level is added.
> 
> AC: `model:`/`effort:` in the task override the role's, and the `--model/--effort` flags override both, for claude and codex ✓ New tests in `test_tool_choice_and_quota_switch` check opus/high from the task, then haiku/low from the flags. They also check the codex `exec -m gpt-o` args and `model_reasoning_effort=high`. The suite passes.
> AC: An alias resolves through `models` for claude and `codex_models` for codex, also after a quota switch; the container name and the Usage row show the resolved model ✓ Tests check `opus-5.5` in the `--name` value, `gpt-o` in the codex `--name`, and `| gpt-o (codex) |` in the Usage row after a claude quota hit.
> AC: An unmapped codex alias runs with `codex-default` and prints one warning naming the alias ✓ The test checks that `-m` is absent, `WARNING` appears exactly once, and `'haiku'` appears in the output. The only gap is the fallback path in the first finding.
> [... truncated ...]
> AC: All tests pass on the Linux worker and the Windows host ✗ `python3 tests/test_omi.py` passes on Linux. The Windows host run was not done, and the author says so.
2026-10-26 14:37 omi-agent-engineer (claude):
> DONE
> - Files changed: `src/omi/__init__.py`, `tests/test_omi.py`, `.omi/tasks/TASK-072.md` (Checkpoint).
> - Quota-switch fallback: when the alias from `am.get("model")` resolves to `codex-default`, `omi run` now prints one WARNING naming that alias. `warn_default` takes an optional `alias` argument for this. The test uses a full claude `--model` with the role's `sonnet` missing from `codex_models`, and checks one WARNING naming `'sonnet'`.
> - Codex error path: a new test runs codex with an `error` event and a `turn.failed` event, exiting 4. It checks that both messages and `exit code 4` are printed and written to `## Reports`.
> - Tests: `python3 tests/test_omi.py` passes on Linux. I did not run the Windows host.
> - Suggested commit: `feat(run): Coordinator sets model and effort per task; surface CLI errors`
2026-10-26 14:37 hook post-run passed:
> Conflict. The container name "/tmpf1jd2s3w-TASK-001-engineer-codex-gpt-x-medium-073715" is already in useBind for 0.0.0.0:8080 failed: port is already in usewrote /tmp/tmpyj0088zg/.omi/skills/CATALOG.md (2 skills)
> create AGENTS.md
> create docker/Dockerfile
> create docker/__pycache__/proxy.cpython-313.pyc
> create docker/__pycache__/proxy.cpython-314.pyc
> create docker/prove.sh
> create docker/proxy.py
> create .claude/settings.json
> create .claude/skills/omi-idea/SKILL.md
> create .claude/skills/omi-release/SKILL.md
> create .claude/skills/omi-status/SKILL.md
> create .claude/skills/omi-task/SKILL.md
> create .omi/agents/CATALOG.md
> create .omi/agents/omi-agent-architect.md
> create .omi/agents/omi-agent-designer-ui.md
> create .omi/agents/omi-agent-devops.md
> create .omi/agents/omi-agent-docs-writer.md
> create .omi/agents/omi-agent-engineer.md
> create .omi/agents/omi-agent-qa-tester.md
> create .omi/agents/omi-agent-researcher.md
> create .omi/agents/omi-agent-reviewer.md
> create .omi/agents/omi-agent-security-reviewer.md
> create .omi/config.json
> create .omi/decisions.md
> create .omi/hooks/post-run.sh
> create .omi/plans/CATALOG.md
> create .omi/plans/PLAN-000.md
> create .omi/references/CATALOG.md
> create .omi/references/nextjs-app-router.md
> create .omi/references/postgres-conventions.md
> create .omi/rules/CATALOG.md
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
> [... truncated ...]
> ok
2026-10-26 14:38 omi-agent-reviewer (claude):
> VERDICT: PASS
> - .omi/tasks/TASK-072.md:27 The Checkpoint says "Windows host: tests ok (Coordinator)" and also "Not done: Windows host test run". I can't run the Windows host from here. -> The Coordinator should confirm the Windows run, then delete the "Not done" line.
> - src/omi/__init__.py:~1996 In the quota-switch fallback, if the role's own alias also fails to resolve for codex (inner `except SystemExit`), `models[other]` is set to `CODEX_DEFAULT` with no warning. This only happens when the role's `model` is an unknown alias, so it is a narrow edge case. -> Call `warn_default(other, am.get("model"))` in that branch if you want it covered.
> 
> AC: `model`/`effort` in the task override the role's, and `--model`/`--effort` override both, for claude and codex ✓ `python3 tests/test_omi.py` passes. The test checks opus/high from the task (claude), then haiku/low from the flags. For codex it checks `exec -m gpt-o` and `model_reasoning_effort=high`.
> AC: An alias resolves via `models` for claude and `codex_models` for codex, also after a quota switch; the container name and Usage row show the resolved model ✓ Tests check `opus-5.5` and `gpt-o` in the `--name` value, and `| gpt-o (codex) |` in the Usage row after a claude quota hit.
> AC: A missing codex alias runs with `codex-default` and prints one warning naming the alias ✓ `warn_default` is called at the start and on both quota-switch resolve paths. Tests check `-m` is absent, `WARNING` appears once, and `'haiku'` / `'sonnet'` appear in the output.
> AC: `model`/`effort` are in both `_template.md` files and are Coordinator-owned ✓ Both templates have the new keys, both `FRONT_OWNED` entries are added, and the test sees `REVERTED: model` and `model: opus` kept.
> [... truncated ...]
> AC: All tests pass on the Linux worker and the Windows host ✗ Linux passes (I ran it). The Windows run has no evidence, and the Checkpoint contradicts itself on it.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 20 | 6884 | 324836 | 102s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 2378 | 74134 | 45s | - | PASS d73e3f2 |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 12 | 2418 | 161115 | 50s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 2203 | 87168 | 44s | - | PASS f929545 |
