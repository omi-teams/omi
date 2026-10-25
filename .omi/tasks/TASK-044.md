---
id: TASK-044
title: Network allowlist for worker containers
status: planned
depends: TASK-028
scope: src/omi/__init__.py, src/omi/template/**, tests/**, README.md
skills: [omi-skill-docker-worker-pitfalls, omi-skill-windows-powershell]
---
## Goal
Every worker container (engineer and read roles) reaches only the model API and the hosts the PO allows.

## Acceptance criteria
- [ ] Containers run on a restricted network or through an egress proxy; the default allowlist is the model API host(s) only, editable in `.omi/config.json`.
- [ ] A request to any other host from inside the container fails; a test or documented manual check proves it.
- [ ] No token is exposed to the proxy beyond what the harness already sends; works on Docker Desktop for Windows.
- [ ] Blocked-host failures name the host and how to allow it; `python tests/test_omi.py` passes.

## Checkpoint
Done:
Not done:
Tests:
Next: TASK-045
