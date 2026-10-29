---
id: TASK-101
title: Pilot detached mode on omi-pilot-splitbill
status: in-progress
depends: TASK-099, TASK-100
plan: PLAN-004
scope: docs/pilot-detached.md
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-docs-only
step: write
---
## Goal
Prove the spec's success criteria on real runs and write the evidence down; gaps found become decisions for a later plan.

## Acceptance criteria
- [ ] On a fresh clone of omi-pilot-splitbill: `omi install-user`, `omi attach`, one real task from start to merge. Evidence: `git log` and `git status` of the code repo show only the task's code commit and no omi file.
- [ ] A second clone of omi-state in another dir (`OMI_STATE`) gives the same `omi status`.
- [ ] `docs/pilot-detached.md` (Vietnamese) lists each criterion with the command run and its output, and every gap found.
- [ ] In-repo mode: the full test suite passes on the Linux worker and the Windows host.

## Checkpoint
Pilot run by the Coordinator on the Windows host, 2026-10-29, omi 0.3.2 (development 181b31c, `pip install -e .`).
Evidence (commands and outputs; docs-writer turns this into docs/pilot-detached.md):
E1 install: `omi --version` -> `omi 0.3.2`; `omi install-user` -> `installed omi user integration`, exit 0.
E2 state repo: `gh repo create omi-teams/omi-state --private` -> https://github.com/omi-teams/omi-state
E3 fresh clone: `git clone https://github.com/omi-teams/omi-pilot-splitbill.git` into E:/Github/Orgs/omi-teams/pilot/.
E4 attach: `omi attach --state https://github.com/omi-teams/omi-state.git` -> created docker/, .omi/ (agents, skills, rules, workflows, catalogs) under `~/.omi/state/projects/omi-pilot-splitbill`, `project.json` = {"remote": "https://github.com/omi-teams/omi-pilot-splitbill.git"}, `tools: git ok, gh ok, docker ok, claude ok, codex ok`, `attached: ...`, exit 0. Code repo `git status` -> `nothing to commit, working tree clean`. State repo: one commit `omi: attach omi-pilot-splitbill`, `## main...origin/main [gone]` (not pushed).
E5 `omi status` -> `state pull skipped: offline or remote unavailable (check remote/upstream)`, `no tasks yet`; `omi sync` -> `state synced`, state now `## main...origin/main`.
E6 real task: TASK-003 `Add --tip percentage` (copied from the repo's in-repo plan) created in state, workflow omi-flow-feature, engineer codex gpt-6.1-sol/medium. `omi step` plan/build/review/accept each committed and pushed state (`chore(omi-pilot-splitbill): step state`), code repo untouched. Engineer: DONE, 10 tests passed, `hook post-run passed`, 50s, 88818 in / 1571 out tokens. Reviewer (claude-sonnet-5-5/medium): VERDICT PASS, 21s; non-blocking note: `--tip 1e9999999` gives a ValueError traceback instead of exit 2. `omi step accept done` refused until the line `PO approval accept: ...` was directly under `## Steps`. `omi hook pre-merge` -> `no pre-merge hook`. PR https://github.com/omi-teams/omi-pilot-splitbill/pull/5, CI ubuntu/macos/windows all pass, squash-merged.
E7 code repo after merge: `git log --oneline -3` -> `f79b518 feat: add tip percentage before splitting bills (#5)`, `4afcd6f feat: equal split ... (TASK-002) (#2)`, `2dcd07e chore: start TASK-002`. `git show --stat HEAD` -> only `src/split_bill/cli.py | 13`, `tests/test_cli.py | 37`. `git diff --name-only 4afcd6f HEAD` -> only those 2 files. `git status` -> clean. Criterion 1 met: no omi file or commit added by the task.
E8 second state clone: `git clone https://github.com/omi-teams/omi-state.git E:/Github/Orgs/omi-teams/pilot/state2`; `omi status` with default state and with `OMI_STATE=E:/Github/Orgs/omi-teams/pilot/state2` both print `branch: development`, `omi 0.3.2 (project 0.3.2)`, `done: 1/1`, `next: none ready`; `diff` -> identical. Criterion 2 met.
E9 in-repo tests on the Windows host: `python tests/test_omi.py` in this worktree -> `ok`, exit 0. Linux: this PR's CI.
Gaps found:
G1 `pip install -e .` puts omi.exe in the Python `Scripts` dir, which is not on PATH; `omi` not found until called by full path.
G2 `omi attach` commits state but does not push; first `omi status` on a new empty remote prints `state pull skipped` until `omi sync` runs.
G3 A fresh clone checks out `main`; `development` had to be created by hand (`git checkout -b development origin/development`) before the task worktree.
G4 splitbill already contains in-repo omi files (.omi/, AGENTS.md, .claude/) from before; once attached they are silently ignored in favour of state. No warning, and no import of existing in-repo tasks (TASK-003 copied by hand, `depends: TASK-002` dropped). `omi detach`/migration is out of v1 scope.
G5 No command records a PO approval line; a line appended at the end of the task file (after ## Usage) is refused by the po gate.
G6 The squash commit title has no task ID (`feat: add tip percentage before splitting bills (#5)`), unlike in-repo `(... TASK-002)`.
G7 Default config of an attached project has `"test": ""` (status warns) and `network_allow` lists only api.anthropic.com, yet the codex engineer run worked.
G8 splitbill follow-up: cap huge `--tip` exponents (reviewer note).
Not done: write docs/pilot-detached.md.
Next: docs-writer.

## Steps
- plan started 2026-10-29 13:18
- plan done 2026-10-29 13:18
- write started 2026-10-29 13:18
