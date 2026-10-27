---
id: TASK-084
title: Agents in the worker can run the claude and codex CLIs themselves (logged in, network allowed)
status: in-progress
depends: TASK-083
plan: PLAN-001
scope: src/omi/__init__.py, tests/test_omi.py, docker/**, README.md
role: omi-agent-engineer
skills: []
refs: []
tool: codex
model: opus
effort: high
workflow: omi-flow-feature-sensitive
step: build
---
## Goal
In TASK-080/081 a researcher inside the Docker worker ran `claude -p --model haiku "say ok"` and got "Not logged in · Please run /login" even though the agent itself was a logged-in claude; `codex login status` said "Not logged in" (`~/.codex` empty) and the proxy blocked `api.openai.com` / `chatgpt.com`. A model-probe spike must be able to call the CLI of the run's own tool from inside the worker, with the same credentials the agent already has, and without new exposure of secrets.

## Acceptance criteria
PO decision 2026-10-27 (.omi/decisions.md): keep Claude Code's subprocess credential scrub; no nested claude login in the worker. Scope narrowed to Codex.
- [x] In a worker run with tool codex, a nested `codex exec -m gpt-6-luna -c model_reasoning_effort=low "say ok"` answers `ok`. Proven by one real run, output pasted in the Checkpoint; if it fails, fix the root cause in the worker (auth file, network allow-list) and prove again.
- [x] Only the codex credentials enter a codex run (no Claude secret), the auth file stays access-token-only in the container tmpfs, secrets stay out of argv, image layers and the worktree, and the network allow-list grows by nothing beyond codex's own hosts. Tests in `tests/test_omi.py` cover this env/mount and allow-list construction for a codex run.
- [x] README states: nested `codex` calls in a codex worker use the run's own login; nested `claude` calls in the worker are not logged in by design (Claude Code strips credentials from subprocesses), so Claude model probes run on the host.

## Checkpoint
Coordinator evidence for the architect (2026-10-27, host, read-only):
- Claude: omi passes the session access token as `-e CLAUDE_CODE_OAUTH_TOKEN` (src/omi/__init__.py claude_secret/claude_auth). Strings in the Claude Code 2.1.302 binary (`grep -a` on claude.exe) show a list of credential env names that Claude Code strips from the environment of its subprocesses: "CLAUDE_CODE_OAUTH_TOKEN","CLAUDE_CODE_OAUTH_REFRESH_TOKEN",...,"ANTHROPIC_AUTH_TOKEN","ANTHROPIC_API_KEY"..., controlled by `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` (error text: "set CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=0 to opt out"). So the agent itself is logged in, but its Bash tool children (the nested `claude -p`) get no token -> "Not logged in". This is a deliberate Claude Code protection: any fix makes the token readable by code the agent runs (tests, scripts) inside the container.
- Codex: CODEX_AUTH_BOOT writes ~/.codex/auth.json (slim, access token only, no refresh) into the container tmpfs and the codex API hosts are added for a codex run. TASK-081's failure ran on claude (bug fixed in TASK-083), so a codex worker may already work for nested `codex exec`: unproven.
- Options to weigh: (a) set CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=0 only for runs of a task that opts in (e.g. frontmatter `nested_cli: true`), never by default; (b) write a tmpfs ~/.claude/.credentials.json with the access token only (same exposure, works without disabling the scrub); (c) no change, the Coordinator probes on the host (what 080/081 did). Name the trust boundary for each.
Architect (2026-10-27, Codex gpt-6-astra/high, 2 runs): both Claude options expose the token to worker subprocesses, contradicting "no new exposure"; asked the PO. PO chose: keep the boundary, Codex only. Trust boundaries: container = boundary for code the agent runs; Claude token lives only in the agent process (scrubbed from children); Codex auth.json (access token only, no refresh) sits in container tmpfs and is readable by code in a codex run, already the case today; egress limited to the allow-list.
Done:
- Nested Codex proven in this Codex worker using its existing ChatGPT login; no runtime/auth/allow-list changes needed. Added regression coverage for run credential isolation, exact Codex host additions, tmpfs home and worktree mounts, no secrets in argv/worktree, and real bootstrap execution with a descendant reading mode-0600 auth after OMI_CODEX_AUTH is unset.
- README documents nested Codex using the run's login, Claude's deliberate subprocess credential scrub, and host-side Claude probes. No scrub override or Claude auth file added; no image change.
- Real run (2026-10-27, this worker): `codex login status` returned `Logged in using ChatGPT`. Command: `codex exec -m gpt-6-luna -c model_reasoning_effort=low -c project_doc_max_bytes=0 "say ok"` (the additional config prevents loading the Coordinator's AGENTS.md).
  Output excerpt (exit 0):
  ```text
  OpenAI Codex v0.164.0
  workdir: /work
  model: gpt-6-luna
  provider: openai
  reasoning effort: low
  codex
  ok
  ok
  tokens used
  2,048
  ```
  Non-fatal diagnostics also reported the unavailable host gitdir and missing system bubblewrap (bundled fallback); the model answered successfully.
Not done: None.
Tests: PASS — real nested CLI probe (exit 0, ok); README acceptance assertion; full suite `TMPDIR=/work/docker PYTHONDONTWRITEBYTECODE=1 python3 tests/test_omi.py` (exit 0, final output `ok`), including test_codex_chatgpt_login, expanded test_codex_chatgpt_run, and new test_codex_auth_boot_nested_process. Temporary fixtures removed.
Next: Coordinator reviews the diff and commits on the host. Suggested commit: `test(worker): verify nested Codex login and credential isolation`. No implementation issues remain; no commit made in the worker.

## Steps
- plan started 2026-10-27 10:40
- plan done 2026-10-27 10:40
- architect started 2026-10-27 10:40
- architect done 2026-10-27 10:49
- build started 2026-10-27 10:49

## Reports
2026-10-27 10:42 omi-agent-architect (codex):
> NEEDS DECISION: Can you provide a secret-redacted reproduction from each tool’s own worker, showing credential variable names, auth-file presence, and blocked hosts? Codex already initializes auth.json and permits its hosts; its failure inside a Claude worker is expected isolation. Claude’s nested credential loss remains unexplained, so the evidence is insufficient to choose a fix.
2026-10-27 10:43 omi-agent-architect (codex):
> NEEDS DECISION: TASK-084 requires “without new exposure of secrets,” but both Claude fixes expose the access token to worker subprocesses. May explicitly opted-in tasks accept that exposure, or must the boundary remain unchanged, requiring host-side Claude probes and revised acceptance criteria?
2026-10-27 10:56 omi-agent-engineer (codex):
> DONE
> Files changed: `tests/test_omi.py`, `README.md`, `.omi/tasks/TASK-084.md`.
> Suggested commit: `test(worker): verify nested Codex login and credential isolation`
> Tests: full suite passed; real nested Codex returned `ok` (exit 0); README check passed.
> Checkpoint updated with evidence. No runtime changes needed.
> Open issues: none. No commit made.
2026-10-27 10:57 hook post-run passed:
> Conflict. The container name "/tmpg0sryvbg-TASK-001-engineer-codex-gpt-x-medium-035614" is already in useBind for 0.0.0.0:8080 failed: port is already in usecreate AGENTS.md
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
> create .omi/config.json
> create .omi/decisions.md
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
> [... truncated ...]
> ok

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-architect | gpt-6-astra (codex) | high | 135655 | 968 | 105344 | 58s | - | n/a |
| omi-agent-architect | gpt-6-astra (codex) | high | 85332 | 430 | 69248 | 28s | - | n/a |
| omi-agent-engineer | gpt-6-astra (codex) | high | 1141283 | 5883 | 1088256 | 411s | 1/1 omi-skill-lean-implementation | - |
