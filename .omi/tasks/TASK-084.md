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
step: architect
---
## Goal
In TASK-080/081 a researcher inside the Docker worker ran `claude -p --model haiku "say ok"` and got "Not logged in · Please run /login" even though the agent itself was a logged-in claude; `codex login status` said "Not logged in" (`~/.codex` empty) and the proxy blocked `api.openai.com` / `chatgpt.com`. A model-probe spike must be able to call the CLI of the run's own tool from inside the worker, with the same credentials the agent already has, and without new exposure of secrets.

## Acceptance criteria
PO decision 2026-10-27 (.omi/decisions.md): keep Claude Code's subprocess credential scrub; no nested claude login in the worker. Scope narrowed to Codex.
- [ ] In a worker run with tool codex, a nested `codex exec -m gpt-6-luna -c model_reasoning_effort=low "say ok"` answers `ok`. Proven by one real run, output pasted in the Checkpoint; if it fails, fix the root cause in the worker (auth file, network allow-list) and prove again.
- [ ] Only the codex credentials enter a codex run (no Claude secret), the auth file stays access-token-only in the container tmpfs, secrets stay out of argv, image layers and the worktree, and the network allow-list grows by nothing beyond codex's own hosts. Tests in `tests/test_omi.py` cover this env/mount and allow-list construction for a codex run.
- [ ] README states: nested `codex` calls in a codex worker use the run's own login; nested `claude` calls in the worker are not logged in by design (Claude Code strips credentials from subprocesses), so Claude model probes run on the host.

## Checkpoint
Coordinator evidence for the architect (2026-10-27, host, read-only):
- Claude: omi passes the session access token as `-e CLAUDE_CODE_OAUTH_TOKEN` (src/omi/__init__.py claude_secret/claude_auth). Strings in the Claude Code 2.1.302 binary (`grep -a` on claude.exe) show a list of credential env names that Claude Code strips from the environment of its subprocesses: "CLAUDE_CODE_OAUTH_TOKEN","CLAUDE_CODE_OAUTH_REFRESH_TOKEN",...,"ANTHROPIC_AUTH_TOKEN","ANTHROPIC_API_KEY"..., controlled by `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` (error text: "set CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=0 to opt out"). So the agent itself is logged in, but its Bash tool children (the nested `claude -p`) get no token -> "Not logged in". This is a deliberate Claude Code protection: any fix makes the token readable by code the agent runs (tests, scripts) inside the container.
- Codex: CODEX_AUTH_BOOT writes ~/.codex/auth.json (slim, access token only, no refresh) into the container tmpfs and the codex API hosts are added for a codex run. TASK-081's failure ran on claude (bug fixed in TASK-083), so a codex worker may already work for nested `codex exec`: unproven.
- Options to weigh: (a) set CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=0 only for runs of a task that opts in (e.g. frontmatter `nested_cli: true`), never by default; (b) write a tmpfs ~/.claude/.credentials.json with the access token only (same exposure, works without disabling the scrub); (c) no change, the Coordinator probes on the host (what 080/081 did). Name the trust boundary for each.
Architect (2026-10-27, Codex gpt-6-astra/high, 2 runs): both Claude options expose the token to worker subprocesses, contradicting "no new exposure"; asked the PO. PO chose: keep the boundary, Codex only. Trust boundaries: container = boundary for code the agent runs; Claude token lives only in the agent process (scrubbed from children); Codex auth.json (access token only, no refresh) sits in container tmpfs and is readable by code in a codex run, already the case today; egress limited to the allow-list.
Done:
Not done:
Tests:
Next:

## Steps
- plan started 2026-10-27 10:40
- plan done 2026-10-27 10:40
- architect started 2026-10-27 10:40

## Reports
2026-10-27 10:42 omi-agent-architect (codex):
> NEEDS DECISION: Can you provide a secret-redacted reproduction from each tool’s own worker, showing credential variable names, auth-file presence, and blocked hosts? Codex already initializes auth.json and permits its hosts; its failure inside a Claude worker is expected isolation. Claude’s nested credential loss remains unexplained, so the evidence is insufficient to choose a fix.
2026-10-27 10:43 omi-agent-architect (codex):
> NEEDS DECISION: TASK-084 requires “without new exposure of secrets,” but both Claude fixes expose the access token to worker subprocesses. May explicitly opted-in tasks accept that exposure, or must the boundary remain unchanged, requiring host-side Claude probes and revised acceptance criteria?

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-architect | gpt-6-astra (codex) | high | 135655 | 968 | 105344 | 58s | - | n/a |
| omi-agent-architect | gpt-6-astra (codex) | high | 85332 | 430 | 69248 | 28s | - | n/a |
