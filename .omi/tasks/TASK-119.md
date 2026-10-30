---
id: TASK-119
title: PR naming rules (task ID first) and step results as PR comments
status: done
depends:
plan: PLAN-006
scope: src/omi/**, .omi/rules/omi-modules.md, .claude/skills/omi-task/SKILL.md, .claude/skills/omi-release/SKILL.md, src/omi/template/dot-claude/skills/omi-task/SKILL.md, src/omi/template/dot-claude/skills/omi-release/SKILL.md, src/omi/template_shas.json, tests/**, .omi/tasks/TASK-119.md
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
Every PR the squad opens is readable without opening the commits: the task ID comes first in the title, and the body follows a fixed set of sections. The omi-task and omi-release skills (repo copy and `src/omi/template`) state the rule, so new projects get it too. Every step result (agent, model, verdict, report) is also posted to the PR as a comment, so the PR shows the whole run. PR #119 (TASK-114) was opened with `--fill`, which gave the title `task/TASK 114` and a list of commits as the body.

## Acceptance criteria
- [x] omi-task PR step: title `[TASK-NNN] <type>(<area>): <summary>` (type one of feat, fix, docs, chore, refactor, test, ci; English, imperative, at most 72 characters); `gh pr create` passes `--title` and `--body-file`, never `--fill`; `gh pr merge --squash` keeps the PR title as the squash commit subject; the no-remote squash commit uses the same subject.
- [x] PR body sections, in order: `## Summary` (1-2 lines, plan and task id), `## Changes` (per file or area), `## Not in this PR`, `## Verification` (test command -> result, review rounds and verdicts, security review when the workflow has one, one `Host:` line per HOST check), `## Known issues` (or `none`).
- [x] omi-release promotion PRs use the title `[RELEASE vX.Y.Z] development -> staging` (and `-> main`) with the same body sections.
- [x] Repo and template copies of both skills are identical; `src/omi/template_shas.json` is updated if the template checks need it; a test asserts both skills name the title format and never mention `--fill`.
- [x] Every step result goes to the PR as its own comment. omi-task opens the PR as a draft after the first build commit, and marks it ready (`gh pr ready`) once every review-type step in the workflow (review, security, and any other `gate review`) has passed. A later FAIL or `step back` turns it back into a draft (`gh pr ready --undo`). When a PR exists for `task/<ID>`, `omi run` posts each final report itself (its `## Reports` entry). Each comment starts with `**Step:** <step> · **Agent:** <role> (<tool>/<model>/<effort>) · **Time:** <time> · **Verdict:** <verdict>`, followed by the report verbatim. Hook results get one short line each (name, pass/fail, last line of output). Coordinator decisions (scope widened, step back, fix round, `Host:` checks) and PO approvals (quoting the PO's words) are posted as `**Agent:** Coordinator` comments. If posting fails (no remote, no `gh`), `omi run` prints a warning and continues, and the task file still has the report.
- [x] A test for posting the comment (gh patched): the header format, the verbatim body, and a skipped post when no PR or no remote exists.
- [x] `python3 tests/test_omi.py` prints `ok`.

## Checkpoint
Fix round 1 done (all review round 1 findings addressed; tests -> ok). Review round 1 FAIL:
- omi-task SKILL.md (repo + template): the PR is opened as a draft right after the first build commit (`gh pr create --draft --title ... --body-file ...`). Step 6 updates it with `gh pr edit task/<ID> --title ... --body-file ...` once Verification is known. Keep `gh pr create` in step 6 only for the case where no PR exists yet.
- Coordinator comments: use `gh pr comment task/<ID> --body-file <file>`, never `--body "...
..."`.
- run.py: take the write-role verdict only from the report's first line (DONE / BLOCKED / NEEDS SCOPE), else `exit <rc>`.
- Hook comments: the agent label must be `omi hook (Docker)`, not `Coordinator`, so the PR shows who wrote each comment.
- tests/test_tasks.py: also assert `--draft`, `gh pr ready`, `**Agent:** Coordinator`, `--subject` and `--body-file` for comments in the skill text.
- `.omi/rules/omi-modules.md` (now in scope): add `worker.pr` to the worker line and the layer order.
Note (Coordinator): the host-level copy in `C:\Users\Admin\.claude\skills\omi-task` is older than the repo copy (still `--fill`, no PO accept gate). After merge, check how that copy is installed and refresh it (outside this task's scope).
Done: worker/pr.py (comment header, post, hook line), run.py posts reports and hook results; omi-task/omi-release skills (repo+template) with title/body/draft rules; tests in test_tasks.py and test_worker.py. template_shas.json unchanged (holds released versions only).
Not done: none
Tests: python3 tests/test_omi.py -> ok
Next: Coordinator review

## Steps
- plan started 2026-10-30 13:29
- plan done 2026-10-30 13:29
- build started 2026-10-30 13:29
- build done 2026-10-30 13:43
- review started 2026-10-30 13:43
- review failed 2026-10-30 13:54
- build started 2026-10-30 13:54
- build done 2026-10-30 14:05
- review started 2026-10-30 14:05
- review done 2026-10-30 14:13
- accept started 2026-10-30 14:13
PO approval accept: Accept, merge development
- accept done 2026-10-30 14:14

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
2026-10-30 13:54 omi-agent-reviewer (claude):
> VERDICT: FAIL
> - `.claude/skills/omi-task/SKILL.md:21,25` (and the template copy) The skill contradicts itself on when the PR is created. The draft bullet says to open the PR as a draft after the first build commit. Step 6 still runs a plain `gh pr create` with `--title` and `--body-file`. By then the PR exists, so `gh pr create` fails. The Verification section can't be known at draft time either, and nothing says to refresh the body. -> In step 6, say to run `gh pr edit task/<ID> --title "<title>" --body-file <file>` when the PR already exists, and keep `gh pr create` only for the no-draft case. Put `--draft` and the title/body rules on the early create.
> - `.claude/skills/omi-task/SKILL.md:25` `gh pr comment task/<ID> --body "<header>\n\n<text>"` posts a literal `\n` under bash and PowerShell, so the comment header is not separated from the text. -> Use `--body-file` with a written file, as for the PR body.
> - `src/omi/worker/run.py:234` For write roles the posted verdict is the first `DONE`, `BLOCKED` or `NEEDS SCOPE` anywhere in the report. A BLOCKED report that mentions "DONE" earlier in its text posts as DONE. -> Match only the report's first line, or reuse a shared verdict parser.
> - `tests/test_tasks.py:260` The draft/ready criterion is only checked through `gh pr ready --undo`. Nothing asserts `--draft`, `gh pr ready`, or the Coordinator comment header, so a skill regression there would pass. -> Assert `--draft`, `gh pr ready`, `**Agent:** Coordinator` and `--subject` in the skill text.
> - `src/omi/worker/pr.py` and `.omi/rules/omi-modules.md:17` `worker.pr` is not in the layer-order list. The module is outside the task scope, and the engineer's report flagged it. -> Have the Coordinator add `worker.pr` to the rule after merge.
> 
> [... truncated ...]
> AC: `python3 tests/test_omi.py` prints `ok`. ✓ I ran it and it printed `ok`, exit 0.
2026-10-30 14:01 omi-agent-engineer (claude):
> DONE. All review round 1 findings are fixed.
> - Files changed:
>   - `.claude/skills/omi-task/SKILL.md` and `src/omi/template/dot-claude/skills/omi-task/SKILL.md`
>   - `src/omi/worker/pr.py`
>   - `src/omi/worker/run.py`
>   - `.omi/rules/omi-modules.md`
>   - `tests/test_tasks.py`
>   - `tests/test_worker.py`
>   - `.omi/tasks/TASK-119.md`
> - **Skill:** the PR opens as a draft after the first build commit. Step 6 runs `gh pr edit task/<ID> --title ... --body-file ...`, and `gh pr create` stays only for when no PR exists yet. Coordinator comments use `gh pr comment task/<ID> --body-file <file>`.
> - **Code:** the write-role verdict now comes only from the report's first line (DONE, BLOCKED or NEEDS SCOPE), else `exit <rc>`. Hook comments use the agent label `omi hook (Docker)`.
> - **Rule:** `worker.pr` is added to the `worker/` line and the layer order in `omi-modules.md`.
> - **Tests:** the skill test now also asserts `--draft`, `gh pr ready`, `**Agent:** Coordinator`, `--subject`, `gh pr edit` and `gh pr comment ... --body-file`. The hook-label assertion in `test_worker.py` is updated. `python3 tests/test_omi.py` printed `ok`.
> - Open issues: none from this round. The host-level `omi-task` skill copy outside the repo is still older, as the checkpoint note says.
> - Commit message: `feat(omi): task-ID-first PR titles, fixed PR body and step results as PR comments`
> 
> Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
2026-10-30 14:04 hook post-run passed:
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
2026-10-30 14:12 omi-agent-reviewer (claude):
> VERDICT: PASS
> - `src/omi/worker/run.py:356` The write-role verdict regex allows leading non-word characters (`\W*`), so a report that starts with punctuation still gets a verdict. This is harmless. No fix needed.
> - `src/omi/worker/run.py:357` The comment posts the full `report`, while the task file's `## Reports` entry is clipped by `clip_report`. The comment is therefore not byte-identical to that entry, but it is the more complete of the two. No fix needed.
> 
> AC: omi-task PR step title format, `--title`/`--body-file` (no `--fill`), `--subject` on `gh pr merge --squash`, no-remote squash subject ✓ Step 6 of `.claude/skills/omi-task/SKILL.md` has `[TASK-NNN] <type>(<area>): <summary>` with the type list and the 72-character limit. It uses `--title` and `--body-file`, `--fill` only appears as "never", and `gh pr merge --squash --delete-branch --subject "<title>"` is there. The no-remote branch says to commit with the same `<title>`.
> AC: PR body sections in order ✓ The five sections are listed in order in the skill, with the Verification contents and `none` for Known issues.
> AC: omi-release promotion PR titles and body sections ✓ The release skill has `[RELEASE vX.Y.Z] development -> staging` and `staging -> main`, the same five sections, and `--title`/`--body-file`.
> AC: repo and template skill copies identical, `template_shas.json`, test asserts title format and no `--fill` ✓ `diff` shows the omi-task and omi-release copies are identical. `template_shas.json` is unchanged, which the task allows ("if the template checks need it"). `test_task_skill_step_commands` asserts the title format and the absence of `--fill`.
> [... truncated ...]
> AC: `python3 tests/test_omi.py` prints `ok` ✓ I ran it and it printed `ok`, exit 0.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 30 | 8680 | 632447 | 537s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 8 | 3181 | 120628 | 493s | - | FAIL c1eafa7 |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 18 | 3566 | 267210 | 344s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 8 | 2640 | 147564 | 307s | - | PASS f126c88 |
