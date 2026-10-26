---
id: TASK-044
title: Network allowlist for worker containers
status: done
depends: TASK-028
scope: src/omi/__init__.py, src/omi/template/**, tests/**, README.md
role: omi-agent-engineer
skills: [omi-skill-docker-worker-pitfalls, omi-skill-windows-powershell]
workflow: omi-flow-feature-sensitive  # worker security boundary
step: accept
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
- [x] Containers run on a restricted network or through an egress proxy; the default allowlist is the model API host(s) only, editable in `.omi/config.json`.
- [x] A request to any other host from inside the container fails; a test or documented manual check proves it.
- [x] No token is exposed to the proxy beyond what the harness already sends; works on Docker Desktop for Windows.
- [x] Blocked-host failures name the host and how to allow it; `python tests/test_omi.py` passes.

## Checkpoint
Review round 1 FAIL: (reviewer PASS with findings, security-reviewer ran without its step skills; fix all)
1. src/omi/__init__.py `step()`/`step_skill_ids`: the budget check for a step adds the task's `skills:` only when the step role has `access: write` (same rule as `run_role`, TASK-049). Now `omi step next` into `security` fails with "4 skills declared" because the task's 2 Docker skills are counted for a read role. Test it.
2. src/omi/__init__.py:909 `egress`: always use `TEMPLATE / "docker" / "proxy.py"`, never the repo copy.
3. src/omi/__init__.py:83-87 `network_allow`: require a list of strings, catch `JSONDecodeError`; exit with "Nothing changed." otherwise. Test a bare string.
4. src/omi/__init__.py:107-108: report the stderr of the docker command that failed (`network connect` / `start`), not of `docker create`.
5. src/omi/template/docker/proxy.py: reject a CONNECT host that is not `[A-Za-z0-9.-]+` (400, no log line); cap the `NETWORK BLOCKED` lines printed by `run_role` (e.g. first 5 plus "... and N more"). Test both.
6. tests/test_omi.py:378: delete the leftover `px.ALLOW[:] = ["127.0.0.1:%d"]` line.
Architect (step architect): RECOMMEND B; Coordinator took B, one task (T1+T2 together, scope already covers both).
- Per-run `docker network create --internal omi-net-<name>` (labels `omi-worker=1`, `omi-repo`); a stdlib CONNECT proxy `src/omi/template/docker/proxy.py` (always from TEMPLATE), run from the worker image with the same hardening flags, no worktree, no token, allowlist as argv; started on bridge, connected to the internal net, wait for `omi-proxy ready`; removed with the network in `finally` (context manager `egress`).
- `allowed(host, port, allow)`: exact host or `*.suffix`, port 443 unless `host:port`; CONNECT only (405 otherwise, never plain HTTP, never log headers); 403 reason `omi blocked <host>: add it to "network_allow" in .omi/config.json`; logs `BLOCKED <host>:<port>`.
- `network_allow(root)`: `DEFAULT_ALLOW = ["api.anthropic.com"]`, `.omi/config.json` `"network_allow"` overrides, entries regex-checked. Template `dot-omi/config.json` gets the key.
- `worker_argv(..., network, proxy)`: `--network`, `-e HTTPS_PROXY=http://<proxy>:3128`, `-e HTTP_PROXY=...`, `-e CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`; `run_role` and `worker --prove` run inside `egress`; after a run print `NETWORK BLOCKED: <host> - add to "network_allow" in .omi/config.json` from the proxy log.
- `clean` also removes networks by `label=omi-repo=<repo>`.
- `prove.sh`: CONNECT api.anthropic.com -> 200; CONNECT example.com -> 403 naming host and key; direct TCP 1.1.1.1:443 fails.
- Tests: proxy allow/deny matrix, wildcard, port, 405, 403 text (importlib); argv, egress order, clean networks. README: manual check incl. Docker Desktop on Windows; known residue: DNS may still resolve on some engines.
Done: proxy.py, egress/network_allow/worker_argv/clean, prove.sh, config template, README, tests.
Not done: real Docker run of --prove (no docker in this container).
Tests: python3 tests/test_omi.py -> ok
Coordinator proof 2026-10-25 on the Windows host (Docker Desktop, WSL2): `omi worker . --prove` -> PASS allowed api.anthropic.com (200), PASS blocked example.com (403 with host and key), PASS direct TCP 1.1.1.1:443 blocked; NETWORK BLOCKED line printed; no container or network left.
Review round 1 fixes 1-6 done (step_skill_ids write-only task skills, egress uses TEMPLATE proxy, network_allow validation, per-command stderr, proxy host regex + blocked cap, test leftover removed). Tests: python3 tests/test_omi.py -> ok.
Next: TASK-045

## Steps
- plan started 2026-10-25 22:58
- plan done 2026-10-25 22:58
- architect started 2026-10-25 22:58
- architect done 2026-10-25 22:59
- build started 2026-10-25 22:59
- build done 2026-10-25 23:02
- review started 2026-10-25 23:02
- review done 2026-10-25 23:03
- security started 2026-10-25 23:06
- security done 2026-10-25 23:07
- accept started 2026-10-25 23:07
PO approval accept: Chấp nhận, merge (Recommended)
- accept done 2026-10-25 23:08

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-architect | claude-opus-5-5 | high | 12 | 6071 | 145418 | 66s | - | n/a |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 30 | 14708 | 641592 | 146s | 3/3 omi-skill-docker-worker-pitfalls omi-skill-windows-powershell omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 3520 | 87324 | 45s | - | PASS 6f0e339 |
| omi-agent-security-reviewer | claude-sonnet-5-5 | medium | 6 | 3029 | 86394 | 40s | - | PASS 6f0e339 |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 22 | 5486 | 367995 | 89s | 2/2 omi-skill-docker-worker-pitfalls omi-skill-windows-powershell | - |
| omi-agent-security-reviewer | claude-sonnet-5-5 | medium | 6 | 2109 | 96580 | 36s | 2/2 omi-skill-diff-security-review omi-skill-ci-workflow-audit | PASS f018ae6 |
