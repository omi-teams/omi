---
id: TASK-103
title: Windows test shell skips the WindowsApps WSL bash alias
status: in-progress
depends:
plan: PLAN-003
scope: src/omi/__init__.py, tests/test_omi.py
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature
step: review
---
## Goal
On the PO's Windows host `test_command` picked `%LOCALAPPDATA%\Microsoft\WindowsApps\bash.exe`, a WSL app alias like System32's, and every `omi run` pre-check failed with `execvpe(/bin/bash) failed` (no WSL distro). Git Bash at `C:\Program Files\Git\bin\bash.exe` was installed but `Git\bin` is not on PATH (only `Git\cmd`). Found 2026-10-28 while starting TASK-094.

## Acceptance criteria
- [ ] On Windows, `test_command` never picks a WSL alias bash (System32 or WindowsApps); it finds Git Bash even when only `Git\cmd` is on PATH (e.g. `bash.exe` under the parent of `git.exe`'s directory, `bin\`), else falls back to `cmd`.
- [ ] A test covers the WindowsApps skip and the Git Bash lookup without needing Windows.
- [ ] All tests pass on the Linux worker and on the Windows host with the PATH as it is (no `Git\bin` added).

## Checkpoint
Review round 1 FAIL (host check by Coordinator): `python tests/test_omi.py` on the Windows host with PATH as is (Git\cmd only) -> FileNotFoundError at tests/test_omi.py:140 `subprocess.run(["sh", hook])`: sh.exe is in Git\bin, not on PATH. Same pattern at tests/test_omi.py:3560 (`["sh", "-c", ...]`). Fix: the tests must run host shell scripts through the same Git Bash lookup as `test_command` (e.g. factor the lookup into one helper in src/omi and reuse it in both), not a bare `sh`. Lines 1447/1458/3503 only match docker argv, leave them.
Done: test_command skips System32 and WindowsApps, finds Git Bash via git.exe's parent\bin\bash.exe, else cmd; test extended.
Not done: run on the real Windows host.
Tests: python3 tests/test_omi.py passed on Linux (exit 0).
Next: Coordinator verifies on Windows.

## Steps
- plan started 2026-10-28 14:30
- plan done 2026-10-28 14:30
- build started 2026-10-28 14:30
- build done 2026-10-28 14:35
- review started 2026-10-28 14:35

## Reports
2026-10-28 14:32 omi-agent-engineer (claude):
> DONE
> - Files changed: `src/omi/__init__.py`, `tests/test_omi.py`, `.omi/tasks/TASK-103.md` (checkpoint).
> - On Windows, `test_command` now skips both the `System32` and `WindowsApps` bash aliases. If no other bash is on PATH, it finds `git.exe` and uses `bin\bash.exe` under the parent of git's directory. If that file doesn't exist, it falls back to `cmd`.
> - `test_windows_test_shell` now covers the WindowsApps skip, the Git Bash lookup with only `Git\cmd` on PATH, and the `cmd` fallback. It runs on Linux against a temp directory.
> - Tests: `python3 tests/test_omi.py` passed on Linux (exit 0). I have not run it on the Windows host, so that acceptance criterion is still open.
> - Commit message: `fix(windows): skip WindowsApps WSL bash alias and locate Git Bash via git.exe`
> 
> Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
2026-10-28 14:35 hook post-run passed:
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
2026-10-28 14:40 omi-agent-reviewer (claude):
> ```
> VERDICT: PASS
> AC: On Windows, test_command never picks a WSL alias bash (System32 or WindowsApps), finds Git Bash via git.exe's parent\bin\bash.exe when only Git\cmd is on PATH, else falls back to cmd ✓ src/omi/__init__.py:2242-2249 filters both alias dirs from PATH and looks up git on the filtered PATH. It uses bin\bash.exe only if the file exists, otherwise it returns the cmd string. The test exercises each branch.
> AC: A test covers the WindowsApps skip and the Git Bash lookup without needing Windows ✓ tests/test_omi.py:1413-1427 (test_windows_test_shell) runs on Linux with mocked WINDOWS, which and get_exec_path, against a temp dir. It covers the WindowsApps skip, the Git\cmd-only lookup, and the cmd fallback after bash.exe is removed.
> AC: All tests pass on the Linux worker and on the Windows host with the PATH as it is (no Git\bin added) ✓ for Linux (python3 tests/test_omi.py exited 0). HOST for the Windows run, which cannot be done in this container.
> ```

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 16 | 3078 | 178488 | 157s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 1002 | 64892 | 242s | - | PASS 09db1a0 |
