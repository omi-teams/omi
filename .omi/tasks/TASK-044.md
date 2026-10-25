---
id: TASK-044
title: Network allowlist for worker containers
status: in-progress
depends: TASK-028
scope: src/omi/__init__.py, src/omi/template/**, tests/**, README.md
role: omi-agent-engineer
skills: [omi-skill-docker-worker-pitfalls, omi-skill-windows-powershell]
workflow: omi-flow-feature-sensitive  # worker security boundary
step:
---
## Goal
Every worker container (engineer and read roles) reaches only the model API and the hosts the PO allows.

### Brief
- Worker containers are started by `worker_argv` / `run_role` in `src/omi/__init__.py` (flags `--read-only`, `--cap-drop ALL`, `--user node`); image from `src/omi/template/docker/Dockerfile` (python3, git, node CLI); boundary proof `src/omi/template/docker/prove.sh` (`omi worker <wt> --prove`, no token).
- Constraints: stdlib only on the host, no new image dependency unless the architect shows a stdlib way is not viable; the model API traffic is TLS, so an allowlist proxy must use HTTP CONNECT and never terminate TLS (no token visible to it); must work on Docker Desktop for Windows (WSL2 backend).
- Default allowlist: the model API host(s) used by the CLIs in the image (Claude: `api.anthropic.com`; Codex later, TASK-045), in `.omi/config.json` `"network_allow": [...]`.
- Proof: extend `prove.sh` so `omi worker <wt> --prove` shows an allowed host connects and a blocked host fails with a message naming the host and the config key; unit tests in `tests/test_omi.py` for the argv and the allowlist check (`python3 tests/test_omi.py`).
- `omi clean` also removes the proxy container and network it creates.

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
