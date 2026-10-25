---
id: TASK-053
title: Hotfix - egress proxy name exceeds the DNS label limit
status: in-progress
depends: TASK-044
scope: src/omi/__init__.py, tests/**
role: omi-agent-engineer
skills: []
workflow: omi-flow-incident
step:
---
## Goal
Worker containers reach the model API through the egress proxy whatever the length of the run's container name.

### Brief
- Symptom: after TASK-044 every `omi run` fails with `API Error: Can't reach the API server (ENOTFOUND)`. Cause: `egress` names the proxy `<container_name>-proxy` (69 chars for `omi-omi-squad2-TASK-052-omi-agent-engineer-sonnet-medium-231504-proxy`) and `worker_argv` uses it as the `HTTPS_PROXY` host; a DNS label is at most 63 chars, so it never resolves. `omi worker --prove` used a shorter name, so it passed.
- Fix: connect the proxy to the per-run network with `--alias omi-proxy` and use `http://omi-proxy:3128` (each run has its own internal network, so the alias is unique per network).
- Coordinator hotfix, approved by the PO in chat (engineer runs are broken by this bug).

## Acceptance criteria
- [ ] `HTTPS_PROXY`/`HTTP_PROXY` use the alias `omi-proxy`, never the container name; `network connect` passes `--alias omi-proxy`.
- [ ] A test asserts the proxy URL host is at most 63 chars for a long container name.
- [ ] Real check: Claude CLI behind the proxy with a 60+ char container name answers a prompt.
- [ ] `python3 tests/test_omi.py` passes.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-052 (resume)
