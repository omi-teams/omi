---
id: TASK-119
title: PR naming rules (task ID first) and step results as PR comments
status: in-progress
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
step:
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
Done:
Not done:
Tests:
Next:
