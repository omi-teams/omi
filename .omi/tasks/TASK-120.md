---
id: TASK-120
title: Resume the engineer session on fix rounds
status: planned
depends:
plan:
scope: src/omi/worker/**, src/omi/template/**, tests/test_worker.py, .omi/tasks/TASK-120.md
role: omi-agent-engineer
skills: []
refs: []
tool:
model:
effort:
step_settings:
workflow: omi-flow-feature-sensitive
step:
---
## Goal
On a fix round, `omi run` continues the engineer's previous CLI session (`claude -p --resume <id>`, `codex exec resume <id>`) with only the new findings, instead of starting a fresh agent that rereads everything; the reviewer stays a fresh instance.

## Acceptance criteria
- [ ] `omi run` records the engineer's session id per tool in the task file (e.g. under `## Checkpoint` or `## Usage`) after each write-role run.
- [ ] A later write-role run on the same task, same tool, resumes that session and sends a short prompt pointing at the new `## Checkpoint` findings; `--fresh` forces a new session; a tool switch (quota fallback or PO pick) starts fresh.
- [ ] Read roles (reviewer, security, qa) never resume.
- [ ] Session data kept between runs lives only in a per-task cache outside the repo, holds no auth token, and `omi clean` removes it; a missing or expired session falls back to a fresh run with one `RESUME FAILED:` line.
- [ ] When the `post-run` hook fails, `omi run` sends the hook's failing output (tail) into the resumed engineer session once to fix it, reruns the hook, and stops after that single retry with the hook failure reported as today; the retry's usage is recorded like any run.
- [ ] The omi-task skill (template copy) describes the resume behaviour; tests cover resume, fresh fallback and read-role exclusion; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next:
