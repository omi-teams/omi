---
id: TASK-063
title: README - how to get and store the Claude token and the OpenAI key
status: done
depends: TASK-054
scope: README.md
role: omi-agent-docs-writer
skills: []
workflow: omi-flow-feature
step: accept
---
## Goal
A short Vietnamese README section "Lấy và lưu key" so the PO can set up both tools without the chat.

## Acceptance criteria
- [x] Claude: `claude setup-token`, then `python -m omi token set` (Windows Credential Manager target `omi/CLAUDE_CODE_OAUTH_TOKEN`; other OS: env `CLAUDE_CODE_OAUTH_TOKEN`).
- [x] OpenAI: platform.openai.com account, API billing is separate from ChatGPT plans, add credit, set a monthly spend limit, API keys -> Create new secret key (shown once); then `python -m omi token set --tool codex` (target `omi/OPENAI_API_KEY`; other OS: env `OPENAI_API_KEY`); `api.openai.com` is allowed automatically for codex runs.
- [x] Check and remove: `cmdkey /list:<target>`, `cmdkey /delete:<target>`; pasting shows nothing; never paste a key into chat, issues or files.
- [x] Note that OpenAI menu names may change; at most ~15 lines; no other README change.

## Checkpoint
Done: README section "Lấy và lưu key" added before "Cách tiết kiệm quota" (Claude, OpenAI, cmdkey, hidden input, menu-change note).
Not done: none in scope. `cmdkey` is not in the code (Windows built-in, unverified here).
Tests: python3 tests/test_omi.py run after the edit (see build report).
Next: Coordinator review and commit.

## Steps
- plan started 2026-10-26 11:09
- plan done 2026-10-26 11:09
- build started 2026-10-26 11:09
- build done 2026-10-26 11:10
- review started 2026-10-26 11:10
- review done 2026-10-26 11:12
- accept started 2026-10-26 11:12
PO approval accept: "Chấp nhận + làm TASK-064"
- accept done 2026-10-26 11:12

## Reports
2026-10-26 11:10 omi-agent-docs-writer (claude):
> DONE
> Files: README.md (new "Láº¥y vÃ  lÆ°u key" section, ~9 lines, before "CÃ¡ch tiáº¿t kiá»‡m quota"); .omi/tasks/TASK-063.md (checkpoint)
> Commit: `docs: add README section on getting and storing Claude and OpenAI keys`
> Not verified: `cmdkey` commands (not in the repo; Windows built-in); OpenAI console menu names (expected to change); the `api.openai.com` auto-allow was checked only against README text, not the proxy code.
> Open issues: on non-Windows, `omi token set` only prints a hint and stores nothing, so the env-var path is the only option there; the doc says so. Tests: `python3 tests/test_omi.py` exit 0.
2026-10-26 11:10 omi-agent-reviewer (claude):
> VERDICT: PASS
> - .omi/tasks/TASK-063.md:37 The build report's Vietnamese is mojibake ("LÃ¡ÂºÂ¥y vÃƒ  lÃ†Â°u key"). This is the task file, not the README, and it doesn't affect the deliverable. -> Re-save the report as UTF-8 if it matters.
> 
> AC: Claude: `claude setup-token`, `python -m omi token set`, Credential Manager target, env fallback âœ“ README.md:31 has all four. The target matches the code, and the env name is `CLAUDE_CODE_OAUTH_TOKEN`.
> AC: OpenAI: account, separate billing, credit, monthly limit, key shown once, `token set --tool codex`, target and env, `api.openai.com` auto-allowed âœ“ README.md:32 covers each item. `CODEX_CRED_TARGET` and `CODEX_ENV` in `src/omi/__init__.py:48-49` match the target and env names. `TOOL_API_HOST` at `src/omi/__init__.py:982` and the tests at `tests/test_omi.py:708` confirm the auto-allow.
> AC: `cmdkey` list and delete, hidden input, never paste a key âœ“ README.md:33 and README.md:34 cover the `cmdkey` commands, the blank screen while typing, and the no-pasting rule. I did not run `cmdkey` or `token set` here, so the commands and the hidden-input behaviour are checked against the task text only.
> AC: Menu names may change; at most about 15 lines; no other README change âœ“ README.md:35 has the note. The section is 7 lines, and the README diff is a single hunk adding only that section.
> 
> Tests: `python3 tests/test_omi.py` ran to the end and printed "ok".

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-docs-writer | claude-haiku-5-5 | low | 14 | 2556 | 181359 | 32s | - | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 1085 | 57485 | 26s | - | PASS a18e235 |
