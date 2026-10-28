---
id: TASK-093
title: /omi-upgrade applies project files when they are behind the installed omi
status: done
depends:
plan: PLAN-003
scope: .claude/skills/omi-upgrade/SKILL.md, src/omi/template/dot-claude/skills/omi-upgrade/SKILL.md, src/omi/__init__.py, tests/test_omi.py, src/omi/template_shas.json
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature
step: accept
---
## Goal
omi-board had omi 0.3.1 installed but 0.3.0 project files, and `/omi-upgrade` stopped at `up to date`. After this, an upgrade always ends with `.omi/version` equal to the installed version.

## Acceptance criteria
- [x] `/omi-upgrade` step 1 (both copies): when `upgrade --check` says `up to date` but `.omi/version` is older than the installed omi (or missing), run `python -m omi upgrade --apply` and continue with steps 4-5 instead of stopping; stop only when both are current.
- [x] `omi status` hint for an older project stamp names the same command the skill runs (`python -m omi upgrade --apply`, or `omi init` if that is what actually stamps; pick the one that does, and the test proves it updates `.omi/version`). Tested.
- [x] Repo copy equals its template copy; template shas updated if the tests require it. All tests pass on the Linux worker and the Windows host.

## Checkpoint
Host: `python tests/test_omi.py` on the Windows host after fix round 1 -> ok (Coordinator, 2026-10-28)
Round 2: removed the no-op write_text before unlink in tests/test_omi.py; the test already starts from a stale 0.1.0 stamp and asserts upgrade_apply stamps the installed version. Linux `python3 tests/test_omi.py` -> ok. Windows host run still for the Coordinator.
Review round 1 FAIL:
- tests/test_omi.py:103 `write_text("0.1.0
")` right before `unlink()` has no effect: delete it.
- Optional: make the test start from a stale project (stamp 0.1.0, run `upgrade_apply`, assert the stamp equals the installed version) so it covers the `up to date` + older-stamp path.
- Host: `python tests/test_omi.py` on the Windows host -> ok (Coordinator, 2026-10-28, before the fix; rerun after).
Done: both skill copies (step 1 applies when stamp is older/missing), status hint now `python -m omi upgrade --apply`, tests (hint, apply stamps .omi/version, skill text)
Not done: Windows host run; template_shas.json untouched (0.3.1 is a released entry)
Tests: python3 tests/test_omi.py passed on Linux
Next: Coordinator review/commit

## Steps
- plan started 2026-10-28 13:27
- plan done 2026-10-28 13:27
- build started 2026-10-28 13:27
- build done 2026-10-28 13:35
- review started 2026-10-28 13:35
- review failed 2026-10-28 13:40
- build started 2026-10-28 13:40
- build done 2026-10-28 13:49
- review started 2026-10-28 13:49
- review done 2026-10-28 13:53
- accept started 2026-10-28 13:53

## Reports
2026-10-28 13:31 omi-agent-engineer (claude):
> DONE
> - Files changed: `.claude/skills/omi-upgrade/SKILL.md`, `src/omi/template/dot-claude/skills/omi-upgrade/SKILL.md` (identical), `src/omi/__init__.py`, `tests/test_omi.py`, `.omi/tasks/TASK-093.md`.
> - Skill step 1: when `upgrade --check` says `up to date`, it now compares `.omi/version` with `python -m omi version`. If the stamp is older or missing, it runs `python -m omi upgrade --apply` and continues with steps 4-5. It stops only when both are current.
> - `omi status` hint now says ``run `python -m omi upgrade --apply` ...``. Both `omi init` and `upgrade_apply` stamp `.omi/version`; I picked the one the skill runs. The test calls `upgrade_apply` and checks that `.omi/version` equals the installed version.
> - Tests: `python3 tests/test_omi.py` ran on Linux and printed `ok`. I did not run it on the Windows host.
> - `template_shas.json` is untouched. The 0.3.1 entry there is a released snapshot, and the tests didn't ask for an update.
> - Suggested commit: `fix(upgrade): apply project files when .omi/version is behind the installed omi`
2026-10-28 13:34 hook post-run passed:
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
2026-10-28 13:39 omi-agent-reviewer (claude):
> VERDICT: FAIL
> - `.omi/tasks/TASK-093.md:27` The Windows host run was not done, so the last acceptance criterion is unproven. -> Run `python3 tests/test_omi.py` on the Windows host and record the result.
> - `tests/test_omi.py:103` `(root/".omi"/"version").write_text("0.1.0\n")` is immediately followed by `unlink()`, so it has no effect. -> Delete the write_text line.
> - `tests/test_omi.py:100` The `omi status` hint is only tested after `omi.init` has already stamped the version. The test calls `upgrade_apply` on a project that `omi.init` created, not on a stale one, and it doesn't cover the `up to date` + older-stamp path. The code behind that path (`upgrade_apply` writing `.omi/version`) does work. -> Optional: stamp 0.1.0 first, run `upgrade_apply`, and assert the stamp equals the installed version. The current test partly does this.
> 
> AC: Skill step 1 (both copies) applies when `up to date` but the stamp is older or missing, then continues with steps 4-5; stops only when both are current. ✓ The wording is in both copies (`cmp` shows the two files are identical). The test asserts "older than", "upgrade --apply" and "steps 4-5".
> AC: `omi status` hint names the command that stamps, and a test proves it updates `.omi/version`. ✓ The hint is now `python -m omi upgrade --apply`. `upgrade_apply` writes `.omi/version` (src/omi/__init__.py:~986), and the test asserts the stamp equals the installed version after calling it.
> AC: Repo copy equals template copy; shas updated if needed; tests pass on Linux and on the Windows host. UNVERIFIED. The copies are identical and `python3 tests/test_omi.py` exits 0 and prints `ok` on Linux. The Windows run was not done. I did not check whether `template_shas.json` needed changes, though the tests pass without any.
2026-10-28 13:44 omi-agent-engineer (claude):
> DONE
> - I deleted the no-op `write_text("0.1.0\n")` that came right before `unlink()` in `tests/test_omi.py`.
> - The test already starts from a stale project: it stamps 0.1.0, runs `upgrade_apply`, and asserts the stamp equals the installed version. I made no other change.
> - I updated `## Checkpoint` in `.omi/tasks/TASK-093.md`.
> - Files changed: `tests/test_omi.py`, `.omi/tasks/TASK-093.md`.
> - Tests: `python3 tests/test_omi.py` ran on Linux and printed `ok`. I did not run the Windows host check, so it is still open.
> - Suggested commit: `fix(upgrade): apply project files when .omi/version is behind the installed omi`
2026-10-28 13:47 hook post-run passed:
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
2026-10-28 13:53 omi-agent-reviewer (claude):
> ```
> VERDICT: PASS
> AC: /omi-upgrade step 1 (both copies) applies when "up to date" but the stamp is older or missing, then continues with steps 4-5 ✓ `cmp` shows the two copies are identical. The test asserts the skill wording ("older than", "upgrade --apply", "steps 4-5") was added in the earlier rounds. I did not re-read the skill text itself this round.
> AC: `omi status` hint names the command that stamps, and a test proves it updates `.omi/version` ✓ src/omi/__init__.py:1142 prints "run `python -m omi upgrade --apply` ...". tests/test_omi.py:98-101 starts from a stale 0.1.0 stamp, checks the hint text, runs `upgrade_apply`, and asserts the stamp equals the installed version. The no-op `write_text` from round 1 is gone.
> AC: Repo copy equals template copy; shas updated if tests require; tests pass on Linux and the Windows host UNVERIFIED. The copies are identical, and `python3 tests/test_omi.py` on Linux exits 0 and prints `ok`. No shas update was needed. No Windows host run after the round-2 change is recorded: the task file only has the pre-fix Windows result and says the Coordinator still has to run it. This is not a code defect, so the Coordinator should run `python tests/test_omi.py` on the Windows host before closing.
> ```

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 16 | 3041 | 198334 | 249s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 8 | 1620 | 96196 | 199s | - | FAIL 8cbcc8f |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 12 | 1258 | 132668 | 237s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 1043 | 63301 | 233s | - | PASS 61165e2 |
