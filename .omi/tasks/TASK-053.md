---
id: TASK-053
title: Hotfix - egress proxy name exceeds the DNS label limit
status: done
depends: TASK-044
scope: src/omi/__init__.py, tests/**
role: omi-agent-engineer
skills: []
workflow: omi-flow-incident
step: postmortem
---
## Goal
Worker containers reach the model API through the egress proxy whatever the length of the run's container name.

### Brief
- Symptom: after TASK-044 every `omi run` fails with `API Error: Can't reach the API server (ENOTFOUND)`. Cause: `egress` names the proxy `<container_name>-proxy` (69 chars for `omi-omi-squad2-TASK-052-omi-agent-engineer-sonnet-medium-231504-proxy`) and `worker_argv` uses it as the `HTTPS_PROXY` host; a DNS label is at most 63 chars, so it never resolves. `omi worker --prove` used a shorter name, so it passed.
- Fix: connect the proxy to the per-run network with `--alias omi-proxy` and use `http://omi-proxy:3128` (each run has its own internal network, so the alias is unique per network).
- Coordinator hotfix, approved by the PO in chat (engineer runs are broken by this bug).

## Acceptance criteria
- [x] `HTTPS_PROXY`/`HTTP_PROXY` use the alias `omi-proxy`, never the container name; `network connect` passes `--alias omi-proxy`.
- [x] A test asserts the proxy URL host is at most 63 chars for a long container name.
- [x] Real check: Claude CLI behind the proxy with a 60+ char container name answers a prompt.
- [x] `python3 tests/test_omi.py` passes.

## Checkpoint
Done: `PROXY_ALIAS = "omi-proxy"`; `network connect --alias omi-proxy`; `egress` yields the alias; test with the TASK-052 container name (63 chars, proxy name 69).
Not done: -
Tests: python3 tests/test_omi.py ok (Windows host). Real check 2026-10-25: `egress` with the 63-char name, Claude CLI 2.1.302 `claude -p 'say ok'` with the token -> `ok`; no container or network left.
Next: TASK-052 (resume)

## Steps
- contain started 2026-10-25 23:16
- contain skipped 2026-10-25 23:16: contained by Coordinator: workers paused (TASK-052 engineer stopped), no merges pending; devops cannot run while the bug stands
- diagnose started 2026-10-25 23:16
- diagnose skipped 2026-10-25 23:16: diagnosed by Coordinator: proxy container name 69 chars > 63-char DNS label, probe with a short name answers ok
- hotfix started 2026-10-25 23:16
- hotfix done 2026-10-25 23:18
- merge-prod started 2026-10-25 23:18
PO approval merge-prod: Duyệt, merge (Recommended)
- merge-prod done 2026-10-25 23:19
- postmortem started 2026-10-25 23:19
- postmortem done 2026-10-25 23:19

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 1153 | 57768 | 23s | - | PASS 03ed861 |
| omi-agent-security-reviewer | claude-sonnet-5-5 | medium | 6 | 707 | 58623 | 15s | - | PASS 03ed861 |
