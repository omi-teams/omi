---
id: omi-skill-windows-powershell
group: delivery-ops
description: Use when running omi, git, gh, docker or shell scripts on Windows PowerShell or Git Bash, or when a command works on Linux but fails on the PO's Windows machine.
tokens: 554
tools: Read, Bash
source_repo: https://github.com/omi-teams/omi-squad2
source_ref: a35ba0957a0a8e7e431fbbaba2b3df1f3588a79d
source_file: docs/spikes/docker.md, docs/verification.md, .omi/tasks/TASK-006.md, .omi/tasks/TASK-015.md
source_license: internal (no LICENSE file yet)
source_use: rewrite
---
# Windows and PowerShell

Only problems seen in this repo's own Windows 11 runs are listed (`docs/spikes/docker.md`, `docs/verification.md`).

## When to use
- A command, script or path behaves differently on the PO's Windows machine than in the Linux container.

## When not to use
- Linux-only work inside the worker container.

## Inputs
- The command, the shell (PowerShell 5.1 or Git Bash) and the error text.

## Steps
1. Locate tools explicitly: `where.exe codex` on Windows, `command -v codex` elsewhere, when a CLI is not on PATH (verification: Codex stopped until told this).
2. Shell scripts need `sh`: from PowerShell call `& "C:\Program Files\Git\bin\sh.exe" <script>` (docker spike).
3. Git Bash rewrites `/work`-style paths in `docker` arguments; set `MSYS_NO_PATHCONV=1` for such calls.
4. Secrets: read the token with `Read-Host -AsSecureString` into `$env:CLAUDE_CODE_OAUTH_TOKEN`, then `Remove-Item Env:CLAUDE_CODE_OAUTH_TOKEN` afterwards. Better: `omi token set` (Credential Manager, TASK-015). Never put a token in argv or a file.
5. omi reads and writes repo text files as UTF-8 (`encoding="utf-8"`); keep files you create UTF-8 too.
6. A sandboxed Codex run needed `-c windows.sandbox="unelevated"` to find `python`, and git reported "dubious ownership" (verification TASK-007); report such errors, do not change global git config unasked.
7. Quote for the shell you are in: PowerShell sets env vars as `$env:NAME`, sh as `NAME=...`.

## Outputs and evidence
- The failing and the working command, with the shell named.

## Stop and escalate
- A fix needs global config, admin rights or PO credentials: stop and tell the PO.

## Tools needed
- Read, Bash.
