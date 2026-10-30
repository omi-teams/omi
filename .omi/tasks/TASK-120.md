---
id: TASK-120
title: Resume the engineer session on fix rounds
status: in-progress
depends:
plan:
scope: src/omi/worker/**, src/omi/app/cli.py, .omi/rules/omi-modules.md, src/omi/template/**, src/omi/template_shas.json, .claude/skills/omi-task/SKILL.md, tests/test_worker.py, .omi/tasks/TASK-120.md
role: omi-agent-engineer
skills: []
refs: []
tool: claude
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature-sensitive
step: build
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
Done: worker/session.py (cache, Session line), resume cmds in tools.py, run.py resume/--fresh/fallback/hook retry, docker clean + --mount, cli usage, omi-modules rule, omi-task skill (+template, sha), tests.
Not done: nothing known.
Tests: python3 tests/test_omi.py passed (pip/playwright tests skipped).
Next: Coordinator review and commit.

## Steps
- plan started 2026-10-30 22:39
- plan done 2026-10-30 22:39
- architect started 2026-10-30 22:39
- architect done 2026-10-30 22:44
- build started 2026-10-30 22:44

## Reports
2026-10-30 22:43 omi-agent-architect (claude):
> I'm not escalating: nothing in the brief conflicts and no approved decision changes. Option A does need the task scope widened by two files, which the Coordinator should confirm.
> 
> ```
> RECOMMEND: A (new worker/session.py module; tools.py builds the resume commands; run.py decides fresh vs resume) - keeps session state and the token check in one place, keeps run.py (432 lines) well under 600, and keeps read roles out structurally. Needs 2 files added to scope: the module list and layer order in .omi/rules/omi-modules.md, and the `--fresh` usage line in src/omi/app/cli.py.
> OPTIONS: A: one owner for the session cache, easy to test / adds a module, so 2 files join the scope; B: no new module (resume commands in tools.py, cache and clean in docker.py, all decisions in run.py ~530 lines) / stays inside scope, but run.py's nested attempt() grows further and session logic is split over 3 files; C: keep the whole /home/node per task / simplest, but it stores .codex/auth.json and Claude credentials, so it fails the "no auth token" criterion: rejected.
> [... truncated ...]
> ```
2026-10-30 22:55 omi-agent-engineer (claude):
> DONE. Fix rounds now resume the engineer's session, and the full `python3 tests/test_omi.py` passes. The pip/wheel and playwright browser checks were skipped, and it did not run against a real `claude` or `codex` CLI.
> 
> - **Files changed:** `src/omi/worker/session.py` (new), `tools.py`, `run.py`, `docker.py`, `src/omi/app/cli.py` (`--fresh` usage), `.omi/rules/omi-modules.md`, `.claude/skills/omi-task/SKILL.md`, its template copy, `src/omi/template_shas.json`, `tests/test_worker.py` (new `test_session_resume`) and the task file.
> - **Behaviour:**
>   - The session id is written as `Session: <tool> <id>` under `## Checkpoint`.
>   - Transcripts go to a per-task cache outside the repo (`$XDG_CACHE_HOME/omi/sessions/<repo>/<task>/<tool>`). Only the transcript directory is mounted, so no auth file lands there; `omi clean` removes it.
>   - A tool switch or `--fresh` starts fresh.
>   - A missing transcript, or a resume that fails without a result, prints one `RESUME FAILED:` line and runs fresh.
>   - Read roles never resume.
>   - If the `post-run` hook fails, the engineer is resumed once with the hook's last 20 lines, the hook reruns, and usage is recorded as usual.
> - **Test coverage:** the new test covers resume, fresh fallback, read-role exclusion, tool switch, the single hook retry and cache clearing.
> - **Template hash:** I updated the `0.5.0` entry for `omi-task/SKILL.md` in `template_shas.json`, because the template copy changed and `test_release_0_5_0` checks that hash.
> - **Open issues:**
>   - The `codex exec resume <id> -m … -c … --json` flag order is untested against a real codex CLI.
>   - If the engineer rewrites `## Checkpoint` and drops the `Session:` line, the next run starts fresh.
>   - The cache directory is `chmod 0o777` so the container user can write to it.
> 
> Suggested commit: `feat(worker): resume the engineer session on fix rounds`
2026-10-30 23:00 hook post-run passed:
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
| omi-agent-architect | claude-opus-5-5 | high | 18 | 8176 | 379460 | 91s | - | n/a |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 38 | 21678 | 1166841 | 647s | 1/1 omi-skill-lean-implementation | - |
