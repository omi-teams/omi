---
id: TASK-119
title: PR naming rules (task ID first) and step results as PR comments
status: in-progress
depends:
plan: PLAN-006
scope: src/omi/**, .claude/skills/omi-task/SKILL.md, .claude/skills/omi-release/SKILL.md, src/omi/template/dot-claude/skills/omi-task/SKILL.md, src/omi/template/dot-claude/skills/omi-release/SKILL.md, src/omi/template_shas.json, tests/**, .omi/tasks/TASK-119.md
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature
step: build
---
## Goal
Every PR the squad opens is readable without opening the commits: the task ID comes first in the title, and the body follows a fixed set of sections. The omi-task and omi-release skills (repo copy and `src/omi/template`) state the rule, so new projects get it too. Every step result (agent, model, verdict, report) is also posted to the PR as a comment, so the PR shows the whole run. PR #119 (TASK-114) was opened with `--fill`, which gave the title `task/TASK 114` and a list of commits as the body.

## Acceptance criteria
- [ ] omi-task PR step: title `[TASK-NNN] <type>(<area>): <summary>` (type one of feat, fix, docs, chore, refactor, test, ci; English, imperative, at most 72 characters); `gh pr create` passes `--title` and `--body-file`, never `--fill`; `gh pr merge --squash` keeps the PR title as the squash commit subject; the no-remote squash commit uses the same subject.
- [ ] PR body sections, in order: `## Summary` (1-2 lines, plan and task id), `## Changes` (per file or area), `## Not in this PR`, `## Verification` (test command -> result, review rounds and verdicts, security review when the workflow has one, one `Host:` line per HOST check), `## Known issues` (or `none`).
- [ ] omi-release promotion PRs use the title `[RELEASE vX.Y.Z] development -> staging` (and `-> main`) with the same body sections.
- [ ] Repo and template copies of both skills are identical; `src/omi/template_shas.json` is updated if the template checks need it; a test asserts both skills name the title format and never mention `--fill`.
- [ ] Every step result goes to the PR as its own comment. omi-task opens the PR as a draft after the first build commit, and marks it ready (`gh pr ready`) once every review-type step in the workflow (review, security, and any other `gate review`) has passed. A later FAIL or `step back` turns it back into a draft (`gh pr ready --undo`). When a PR exists for `task/<ID>`, `omi run` posts each final report itself (its `## Reports` entry). Each comment starts with `**Step:** <step> · **Agent:** <role> (<tool>/<model>/<effort>) · **Time:** <time> · **Verdict:** <verdict>`, followed by the report verbatim. Hook results get one short line each (name, pass/fail, last line of output). Coordinator decisions (scope widened, step back, fix round, `Host:` checks) and PO approvals (quoting the PO's words) are posted as `**Agent:** Coordinator` comments. If posting fails (no remote, no `gh`), `omi run` prints a warning and continues, and the task file still has the report.
- [ ] A test for posting the comment (gh patched): the header format, the verbatim body, and a skipped post when no PR or no remote exists.
- [ ] `python3 tests/test_omi.py` prints `ok`.

## Checkpoint
Note (Coordinator): the host-level copy in `C:\Users\Admin\.claude\skills\omi-task` is older than the repo copy (still `--fill`, no PO accept gate). After merge, check how that copy is installed and refresh it (outside this task's scope).
Done: worker/pr.py (comment header, post, hook line), run.py posts reports and hook results; omi-task/omi-release skills (repo+template) with title/body/draft rules; tests in test_tasks.py and test_worker.py. template_shas.json unchanged (holds released versions only).
Not done: none
Tests: python3 tests/test_omi.py -> ok
Next: Coordinator review

## Steps
- plan started 2026-10-30 13:29
- plan done 2026-10-30 13:29
- build started 2026-10-30 13:29

## Reports
2026-10-30 13:38 omi-agent-engineer (claude):
> DONE
> - Files: `src/omi/worker/pr.py` (new), `src/omi/worker/run.py`, `.claude/skills/omi-task/SKILL.md`, `.claude/skills/omi-release/SKILL.md`, the same two skills under `src/omi/template/dot-claude/skills/`, `tests/test_tasks.py`, `tests/test_worker.py`, `.omi/tasks/TASK-119.md`.
> - `omi run` now posts each final report to the task's PR as a comment with the required header. The `pre-run` and `post-run` hook results get one line each. With no remote or no open PR it skips silently, and a missing `gh` or a failed post prints a warning and continues.
> - The skills now state the `[TASK-NNN] <type>(<area>): <summary>` title, the five body sections, `--title` with `--body-file` (never `--fill`), and the squash subject. They also state the draft/ready/`--undo` flow, the Coordinator comments, and the `[RELEASE vX.Y.Z]` promotion titles.
> - Commit message: `feat(omi): task-ID-first PR titles, fixed PR body and step results as PR comments`
> - Tests: `python3 tests/test_omi.py` printed `ok`. It covers the header format, the verbatim body, the skipped post, the post-failure warning, and the skill title/format assertions, including that neither skill mentions `--fill`.
> - Open issues:
>   - `template_shas.json` is unchanged. It only holds released versions, and 0.4.1 is already in it.
>   - The draft/ready steps, the Coordinator and PO comments, and `--subject` on `gh pr merge` are skill instructions only. `omi run` does none of them, and none were run against GitHub.
>   - For engineer runs the posted verdict is the first `DONE`, `BLOCKED` or `NEEDS SCOPE` found in the report, else `exit <rc>`.
>   - `omi-modules.md` is outside scope, so `worker.pr` is not in its layer-order list.
> 
> Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
2026-10-30 13:42 hook post-run passed:
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

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 30 | 8680 | 632447 | 537s | 1/1 omi-skill-lean-implementation | - |
