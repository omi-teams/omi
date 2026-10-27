---
id: TASK-081
title: Spike - which Codex models and efforts this Codex session supports, and what each fits
status: in-progress
depends:
scope: docs/research/models-codex.md
role: omi-agent-researcher
skills: []
refs:
plan: PLAN-001
tool: codex
model: sonnet
effort: medium
workflow: omi-flow-spike
step: research
---
## Goal
Codex runs often show `codex-default` / `none`, so nobody knows which model or effort ran. Find out, from inside the worker (Codex CLI 0.164.0, the PO's ChatGPT login), which Codex models and reasoning efforts are actually usable, and what kind of omi task each fits.

## Questions
1. Which model IDs does this `codex` CLI accept (`-m`) with the ChatGPT login? Look at what the CLI itself exposes (help, `~/.codex` model cache, error messages for an unknown model) and prove each with a one-line `codex exec -m <id> -c model_reasoning_effort=low "say ok"` run, or say why it was not run. Which model does `codex exec` use when no `-m` is given, and which effort?
2. Which `model_reasoning_effort` values exist (none, minimal, low, medium, high, xhigh?) per model, and what they change.
3. For each usable model x effort that matters, which omi work fits: mechanical, normal feature, bugfix, refactor, review, security review, architecture, research. Relative cost (ChatGPT plan limits) and speed from the run's usage numbers where possible.
4. A recommended `codex_models` mapping for the aliases haiku / sonnet / opus, and a default per omi role.

## Acceptance criteria
- [ ] Report saved at `docs/research/models-codex.md` (Vietnamese prose, English IDs): a table `model id | effort levels | fits | avoid for | relative cost/speed | evidence`, the default model/effort of `codex exec`, the proposed `codex_models` mapping and per-role defaults.
- [ ] Every claim says how it was verified (command run and its output, or CLI help/cache content); anything not verified is marked as such.

## Checkpoint
Done: research step (see Reports): in-container codex is "Not logged in" and the proxy blocks api.openai.com; the researcher also ran on claude, not codex, although the task says `tool: codex` (omi bug, not part of this spike). PO approved the Coordinator probing on the host (2026-10-27).
Host evidence (codex-cli 0.164.0, PO ChatGPT login, Windows host):
- `~/.codex/models_cache.json` (fetched_at 2026-10-27T02:25Z, client 0.164.0), slug | description | default_reasoning_level | supported_reasoning_levels | visibility | priority | context_window:
  - gpt-6.1-sol | "Latest workhorse model for coding and everyday work." | low | low,medium,high,xhigh,max,ultra | list | 1 | 500000
  - gpt-6-astra | "Frontier intelligence for the most demanding work." | low | low..ultra | list | 2 | 272000
  - gpt-6.1-terra | "GPT-6.1 Terra Codex model." | low | low..ultra | list | 3 | 500000
  - gpt-6-sol | "Previous generation workhorse model." | medium | low..ultra | list | 4 | 272000
  - gpt-reserve | "Fast and affordable agentic coding model." | medium | low..max | hide | 4 | 272000
  - gpt-6-luna | "Fast and affordable model for easier tasks." | medium | low..max | list | 5 | 272000
  - gpt-5.6-sol | "Older generation workhorse model." | low | low..ultra | list | 6
  - gpt-5.6-terra | "Older balanced model for straightforward work." | medium | low..ultra | list | 8
  - gpt-5.6-luna | "Older fast and efficient model." | medium | low..max | list | 9
  - codex-auto-review | "Automatic approval review model for Codex." | hide (internal, not probed)
  All list service tier `priority` and speed tier `fast`.
- `~/.codex/config.toml` on the host: `model = "gpt-6.1-sol"`, `model_reasoning_effort = "medium"`, `service_tier = "priority"`. So on this host, `codex exec` with no -m runs gpt-6.1-sol at medium. Probe with no -m answered ok with input_tokens 19532, the same as the explicit gpt-6.1-sol run (the JSON output does not name the model). Inside the Docker worker there is no host config.toml: the default there is unverified (likely cache priority 1 = gpt-6.1-sol at its default_reasoning_level low).
- Model probe `codex exec --skip-git-repo-check --json -s read-only -m <id> -c model_reasoning_effort=low "say ok"` (answer | input/cached/output/reasoning tokens | wall ms):
  gpt-6.1-sol ok 19532/13440/5/0 9685; gpt-6-astra ok 18922/13312/5/0 10898; gpt-6.1-terra ok 18922/8320/5/0 8558; gpt-6-sol ok 18473/12928/5/0 7515; gpt-6-luna OK 18294/12672/5/0 7521; gpt-5.6-sol ok 18650/12416/5/0 8127; gpt-5.6-terra ok 18104/12032/5/0 9084; gpt-5.6-luna ok 17123/11392/5/0 10126; gpt-reserve ok 16577/11392/5/0 9385 (hidden in cache but works).
  `-m foo-model`: turn.failed 400 invalid_request_error "The 'foo-model' model is not supported when using Codex with a ChatGPT account".
- Effort probe, prompt bat-and-ball (all answered 5), gpt-6.1-sol, output/reasoning tokens | ms: low 5/0 8975; medium 5/0 7323; high 17/10 8183; xhigh 20/13 9276; max 25/18 8896; ultra 17/10 8533.
  gpt-6-luna: ultra accepted (23/16) although the cache does not list it for luna; none accepted (5/0); minimal rejected: "Unsupported value: 'minimal' is not supported with the 'gpt-6-luna' model. Supported values are: 'none', 'low', 'medium', 'high', 'xhigh', and 'max'." How the CLI handles ultra on luna (clamped or passed through): unverified.
- Not measurable here: ChatGPT plan cost per model (usage JSON shows tokens only, no price; token counts are near-equal on a tiny prompt), speed on real tasks (wall time 7.5-11 s is dominated by startup), quality per task type.
- Coordinator recommendation (from cache descriptions, not benchmarks): codex_models haiku -> gpt-6-luna, sonnet -> gpt-6.1-sol, opus -> gpt-6-astra; efforts map 1:1 (low/medium/high), avoid ultra/max by default; never leave model or effort empty (that is what prints codex-default/none).
Not done: write step (docs-writer saves docs/research/models-codex.md from Reports + this evidence; mark fits/defaults as recommendation, not measured).
Tests: n/a (docs only)
Next: write, then decide (PO gate).
## Steps
- plan started 2026-10-27 09:23
- plan done 2026-10-27 09:23
- research started 2026-10-27 09:23

## Reports
2026-10-27 09:25 omi-agent-researcher (claude):
> ANSWER: I can't answer this from this container. `codex` is not logged in, and the proxy blocks `api.openai.com`, so no model or effort could be tested. I also did not write `docs/research/models-codex.md`, because this role is read-only.
> - `codex login status` prints "Not logged in", and `~/.codex` holds only an empty `tmp/` directory. There is no model cache to read. [shell run, codex-cli 0.164.0, 2026-10-27]
> - `codex exec -m foo "x"` failed to connect: "Proxy connection failed: HTTP CONNECT failed with status 403, url: wss://api.openai.com/v1/responses". It then fell back to HTTPS and kept printing "Reconnecting... waiting for network". The run was cut off by `timeout 60`, so the CLI never reported whether `foo` is an unknown model. [same run]
> - `codex exec --help` says only "-m, --model <MODEL>  Model the agent should use". It lists no model IDs and no effort values. The only hint is an example `-c model="o3"`, which proves nothing about this login. [`codex exec --help`, 0.164.0]
> - `.omi/config.json:7-11` maps haiku, sonnet and opus all to `gpt-6.1-sol`. `.omi/decisions.md:56` records this as a PO decision made on 2026-10-26. I could not check that `gpt-6.1-sol` is accepted under this login, so it is unverified.
> - `README.md:61` says that with no `codex_models` entry, the `-m` flag is dropped and the CLI uses its own default model. That is the source of the `codex-default` label.
> CONFIDENCE: high that nothing can be verified from here (login and network are both blocked). I have no data to rate any model or effort.
> GAPS: Everything in questions 1–4 is unverified: the accepted model IDs, the default model and effort of `codex exec`, the effort values per model, usage and speed numbers, the fit per task type, and the recommended mapping and per-role defaults.
> NEEDS DECISION: Should this spike be re-run in a session with a ChatGPT login and a network path to `api.openai.com`? I can't mark it done or write the report from here without inventing evidence.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-researcher | claude-sonnet-5-5 | medium | 12 | 1424 | 108686 | 86s | - | n/a |
