---
id: TASK-094
title: Host-only criteria are confirmed by the Coordinator, not marked by the reviewer
status: done
depends:
plan: PLAN-003
scope: .omi/agents/omi-agent-reviewer.md, src/omi/template/dot-omi/agents/omi-agent-reviewer.md, .claude/skills/omi-task/SKILL.md, src/omi/template/dot-claude/skills/omi-task/SKILL.md, .omi/agents/CATALOG.md, src/omi/template_shas.json, tests/test_omi.py
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature-sensitive
step: review
---
## Goal
On TASK-092 the reviewer gave PASS although "tests pass on the Windows host" could not run in its container, against its own UNVERIFIED rule. Host-only checks get one owner: the Coordinator, with evidence in the checkpoint.

## Acceptance criteria
- [x] Reviewer prompt (both copies): a criterion that can only run on the host (e.g. "on the Windows host") is reported `HOST <criterion>` and does not block PASS; every other skipped or unexecuted criterion stays `UNVERIFIED` and blocks PASS.
- [x] omi-task skill (both copies): before merge, the Coordinator runs the host checks and writes `Host: <command> -> <result>` in the task checkpoint; no merge without that line when the reviewer reported a `HOST` item.
- [x] Repo copies equal their template copies; agents catalog regenerated; `omi skills --check` passes; template shas updated if the tests require it. All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done: reviewer HOST carve-out and omi-task `Host:` line in repo and template copies (identical); test_host_only_criteria added. CATALOG.md and template_shas.json unchanged (summary same, shas hold released versions only).
Not done: Windows host test run (Coordinator).
Tests: python3 tests/test_omi.py ok on Linux worker; `PYTHONPATH=src python3 -m omi skills --check` ok (19 checked).
Host: python tests/test_omi.py (Windows host, Git\bin prepended to PATH, see TASK-103) -> exit 0, ok
Next: merge

## Steps
- plan started 2026-10-28 14:05
- plan done 2026-10-28 14:05
- architect started 2026-10-28 14:05
- architect done 2026-10-28 14:08
- build started 2026-10-28 14:08
- build done 2026-10-28 14:15
- review started 2026-10-28 14:15

## Reports
2026-10-28 14:08 omi-agent-architect (claude):
> ```
> RECOMMEND: A (prompt-only change plus a phrase test) - decision 2026-10-28 (TASK-092 gap) already approves this carve-out, every file it touches is in scope, and the PO-accept gate's unticked-AC check already catches a HOST criterion that was never ticked.
> OPTIONS: A: reviewer gets a narrow HOST mark, omi-task step 6 gets a Coordinator host check with a `Host:` line, one test pins the phrases / pro: in scope, cheap, no code / con: the `Host:` line is enforced by the skill text only; B: A plus a code check (pre-merge or po accept refuses when the reviewer report has HOST but the checkpoint has no `Host:`) / pro: machine-enforced / con: needs src/omi/__init__.py, which is out of scope, and parsing the reviewer report inside `## Reports` is fragile (clip_report).
> STRUCTURE: reviewer.md step 3 gets one sentence: "a criterion whose text names the host (e.g. 'on the Windows host') is `HOST <criterion>`, does not block PASS; every other skipped or unexecuted check stays UNVERIFIED and blocks PASS; a mixed criterion (Linux worker + Windows host) is split: verify the Linux part, mark only the host part HOST". Output line becomes `AC: <criterion> ✓|✗|UNVERIFIED|HOST <evidence>`. Keep the `summary:` frontmatter unchanged, so CATALOG.md regenerates with no diff. omi-task SKILL.md step 6: "if the reviewer reported HOST items, run each host check on the host, write `Host: <command> -> <result>` under `## Checkpoint` in <wt>'s task file, tick that criterion only on a pass; a failed host check is a fix round (step 5); no merge without one `Host:` line per HOST item". Apply identical edits to the src/omi/template copies. template_shas.json holds released versions only (0.2.0/0.3.0/0.3.1), so leave it unchanged.
> [... truncated ...]
> ```
2026-10-28 14:13 omi-agent-engineer (claude):
> DONE
> - Files changed:
>   - `.omi/agents/omi-agent-reviewer.md` and `src/omi/template/dot-omi/agents/omi-agent-reviewer.md`
>   - `.claude/skills/omi-task/SKILL.md` and `src/omi/template/dot-claude/skills/omi-task/SKILL.md`
>   - `tests/test_omi.py` (new `test_host_only_criteria`)
>   - `.omi/tasks/TASK-094.md` (checkpoint)
> - Reviewer prompt: a criterion that names the host is reported `HOST <criterion>` and does not block PASS. Every other skipped or unexecuted criterion stays `UNVERIFIED` and blocks PASS. A mixed criterion is split.
> - omi-task step 6: the Coordinator runs each `HOST` check and writes `Host: <command> -> <result>` in the checkpoint. There is no merge without one `Host:` line per `HOST` item.
> - Tests: `python3 tests/test_omi.py` and `PYTHONPATH=src python3 -m omi skills --check` (19 checked) both pass on the Linux worker. The Windows host run has not been done.
> - Unchanged on purpose: `.omi/agents/CATALOG.md` has no diff because the reviewer `summary:` is unchanged, and `template_shas.json` holds released versions only.
> - The `Host:` rule is enforced by the skill text alone, with no code check.
> - Suggested commit: `feat: host-only criteria are reported HOST and confirmed by the Coordinator (TASK-094)`
2026-10-28 14:15 hook post-run passed:
> create AGENTS.md
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
> create .omi/skills/ui/omi-skill-ui-direction/SKILL.md
> create .omi/skills/ui/omi-skill-ui-direction/references/style-presets.md
> [... truncated ...]
> ok
2026-10-28 14:20 omi-agent-reviewer (claude):
> ```
> VERDICT: PASS
> AC: Reviewer prompt (both copies): a host-only criterion is reported `HOST <criterion>` and does not block PASS; every other skipped or unexecuted criterion stays `UNVERIFIED` and blocks PASS ✓ Step 3 of both copies keeps the UNVERIFIED-blocks-PASS rule. It adds an exception for criteria that name the host, reported as `HOST <criterion>`, and splits mixed criteria. The output line is now `✓|✗|UNVERIFIED|HOST`. The two copies are byte-identical (diff clean).
> AC: omi-task skill (both copies): before merge, the Coordinator runs the host checks and writes `Host: <command> -> <result>` in the task checkpoint; no merge without that line when the reviewer reported a `HOST` item ✓ Step 6 of both copies adds this. Each HOST item gets a check on the host, a `Host:` line under `## Checkpoint`, and a criterion tick only on a pass. A failed host check is a fix round, and the step says "no merge without one `Host:` line per `HOST` item". The copies are identical (diff clean).
> AC: Repo copies equal their template copies; agents catalog regenerated; `omi skills --check` passes; template shas updated if the tests require it; all tests pass on the Linux worker and the Windows host ✓ for repo/template equality, `omi skills --check` (19 checked) and the Linux worker tests. The catalog and shas are unchanged and the tests pass, which fits an unchanged `summary:` and shas that hold released versions only. UNVERIFIED for the Windows host: the task file's own Checkpoint says that run has not been done. This is the host-only part of the criterion, so it is reported as HOST and doesn't block PASS. HOST: all tests pass on the Windows host (Coordinator must run `python3 tests/test_omi.py` there and write a `Host:` line).
> ```

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-architect | claude-opus-5-5 | high | 14 | 3415 | 164639 | 50s | - | n/a |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 16 | 2947 | 187595 | 253s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 1342 | 75098 | 239s | - | PASS fd067f7 |
