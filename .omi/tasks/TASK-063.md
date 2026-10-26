---
id: TASK-063
title: README - how to get and store the Claude token and the OpenAI key
status: in-progress
depends: TASK-054
scope: README.md
role: omi-agent-docs-writer
skills: []
workflow: omi-flow-feature
step:
---
## Goal
A short Vietnamese README section "Lấy và lưu key" so the PO can set up both tools without the chat.

## Acceptance criteria
- [ ] Claude: `claude setup-token`, then `python -m omi token set` (Windows Credential Manager target `omi/CLAUDE_CODE_OAUTH_TOKEN`; other OS: env `CLAUDE_CODE_OAUTH_TOKEN`).
- [ ] OpenAI: platform.openai.com account, API billing is separate from ChatGPT plans, add credit, set a monthly spend limit, API keys -> Create new secret key (shown once); then `python -m omi token set --tool codex` (target `omi/OPENAI_API_KEY`; other OS: env `OPENAI_API_KEY`); `api.openai.com` is allowed automatically for codex runs.
- [ ] Check and remove: `cmdkey /list:<target>`, `cmdkey /delete:<target>`; pasting shows nothing; never paste a key into chat, issues or files.
- [ ] Note that OpenAI menu names may change; at most ~15 lines; no other README change.

## Checkpoint
Done:
Not done:
Tests:
Next:
