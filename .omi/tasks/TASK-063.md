---
id: TASK-063
title: README - how to get and store the Claude token and the OpenAI key
status: in-progress
depends: TASK-054
scope: README.md
role: omi-agent-docs-writer
skills: []
workflow: omi-flow-feature
step: build
---
## Goal
A short Vietnamese README section "Lấy và lưu key" so the PO can set up both tools without the chat.

## Acceptance criteria
- [ ] Claude: `claude setup-token`, then `python -m omi token set` (Windows Credential Manager target `omi/CLAUDE_CODE_OAUTH_TOKEN`; other OS: env `CLAUDE_CODE_OAUTH_TOKEN`).
- [ ] OpenAI: platform.openai.com account, API billing is separate from ChatGPT plans, add credit, set a monthly spend limit, API keys -> Create new secret key (shown once); then `python -m omi token set --tool codex` (target `omi/OPENAI_API_KEY`; other OS: env `OPENAI_API_KEY`); `api.openai.com` is allowed automatically for codex runs.
- [ ] Check and remove: `cmdkey /list:<target>`, `cmdkey /delete:<target>`; pasting shows nothing; never paste a key into chat, issues or files.
- [ ] Note that OpenAI menu names may change; at most ~15 lines; no other README change.

## Checkpoint
Done: README section "Lấy và lưu key" added before "Cách tiết kiệm quota" (Claude, OpenAI, cmdkey, hidden input, menu-change note).
Not done: none in scope. `cmdkey` is not in the code (Windows built-in, unverified here).
Tests: python3 tests/test_omi.py run after the edit (see build report).
Next: Coordinator review and commit.

## Steps
- plan started 2026-10-26 11:09
- plan done 2026-10-26 11:09
- build started 2026-10-26 11:09

## Reports
2026-10-26 11:10 omi-agent-docs-writer (claude):
> DONE
> Files: README.md (new "Láº¥y vÃ  lÆ°u key" section, ~9 lines, before "CÃ¡ch tiáº¿t kiá»‡m quota"); .omi/tasks/TASK-063.md (checkpoint)
> Commit: `docs: add README section on getting and storing Claude and OpenAI keys`
> Not verified: `cmdkey` commands (not in the repo; Windows built-in); OpenAI console menu names (expected to change); the `api.openai.com` auto-allow was checked only against README text, not the proxy code.
> Open issues: on non-Windows, `omi token set` only prints a hint and stores nothing, so the env-var path is the only option there; the doc says so. Tests: `python3 tests/test_omi.py` exit 0.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-docs-writer | claude-haiku-5-5 | low | 14 | 2556 | 181359 | 32s | - | - |
