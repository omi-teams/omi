---
id: TASK-044
title: Network allowlist for worker containers
status: in-progress
depends: TASK-028
scope: src/omi/__init__.py, src/omi/template/**, tests/**, README.md
role: omi-agent-engineer
skills: [omi-skill-docker-worker-pitfalls, omi-skill-windows-powershell]
workflow: omi-flow-feature-sensitive  # worker security boundary
step: architect
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
Architect (step architect): RECOMMEND B; Coordinator took B, one task (T1+T2 together, scope already covers both).
- Per-run `docker network create --internal omi-net-<name>` (labels `omi-worker=1`, `omi-repo`); a stdlib CONNECT proxy `src/omi/template/docker/proxy.py` (always from TEMPLATE), run from the worker image with the same hardening flags, no worktree, no token, allowlist as argv; started on bridge, connected to the internal net, wait for `omi-proxy ready`; removed with the network in `finally` (context manager `egress`).
- `allowed(host, port, allow)`: exact host or `*.suffix`, port 443 unless `host:port`; CONNECT only (405 otherwise, never plain HTTP, never log headers); 403 reason `omi blocked <host>: add it to "network_allow" in .omi/config.json`; logs `BLOCKED <host>:<port>`.
- `network_allow(root)`: `DEFAULT_ALLOW = ["api.anthropic.com"]`, `.omi/config.json` `"network_allow"` overrides, entries regex-checked. Template `dot-omi/config.json` gets the key.
- `worker_argv(..., network, proxy)`: `--network`, `-e HTTPS_PROXY=http://<proxy>:3128`, `-e HTTP_PROXY=...`, `-e CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`; `run_role` and `worker --prove` run inside `egress`; after a run print `NETWORK BLOCKED: <host> - add to "network_allow" in .omi/config.json` from the proxy log.
- `clean` also removes networks by `label=omi-repo=<repo>`.
- `prove.sh`: CONNECT api.anthropic.com -> 200; CONNECT example.com -> 403 naming host and key; direct TCP 1.1.1.1:443 fails.
- Tests: proxy allow/deny matrix, wildcard, port, 405, 403 text (importlib); argv, egress order, clean networks. README: manual check incl. Docker Desktop on Windows; known residue: DNS may still resolve on some engines.
Done:
Not done:
Tests:
Next: TASK-045

## Steps
- plan started 2026-10-25 22:58
- plan done 2026-10-25 22:58
- architect started 2026-10-25 22:58

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-architect | claude-opus-5-5 | high | 12 | 6071 | 145418 | 66s | - | n/a |
