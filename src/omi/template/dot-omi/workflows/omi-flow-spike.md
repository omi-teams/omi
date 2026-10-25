---
id: omi-flow-spike
summary: Time-boxed research question: researcher gathers cited findings, docs-writer saves the report under docs/, PO decides. No product code. Use to answer a question or compare options; use feature once the decision is made.
steps:
- id: plan | role: coordinator | skills: omi-skill-task-brief | input: PO question | output: task file with the question, time box and a scope limited to docs/** | gate: none | stop: task file complete and PO picked it
- id: research | role: omi-agent-researcher | skills: | input: task file | output: findings with a source for every claim, options and a recommendation (read-only, returned as text) | gate: none | stop: every claim cited; open questions listed
- id: write | role: omi-agent-docs-writer | skills: | input: researcher findings, task file | output: cited report saved under docs/, Checkpoint updated | gate: none | stop: report saved, all citations kept, no product code changed
- id: decide | role: coordinator | skills: | input: report path, recommendation | output: PO decision line in ## Steps | gate: po | stop: PO decides (adopt, adjust, drop)
---
# Spike

**When to use:** a question or option comparison where the output is knowledge, not code.
**Use instead:** `omi-flow-feature` to build what the spike recommended; the decision can start that task.

## Models
- plan: Coordinator, sonnet/low.
- research: researcher, sonnet/medium; read-only, so it cannot save the report.
- write: docs-writer, sonnet/low; saves the researcher's cited report under `docs/`, adds no new claims.
- decide: Coordinator; the PO decides.

## Stop conditions
- Any product code change: stop; that belongs in a feature task.
- Time box exhausted: report what is known and ask the PO.
- A claim without a source: remove it or mark it unverified.

## PO gates
`decide` needs `PO approval decide: <PO's words>` under `## Steps`; `omi step` refuses otherwise. Record a lasting decision in `.omi/decisions.md`.
