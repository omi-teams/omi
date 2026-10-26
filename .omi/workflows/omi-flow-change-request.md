---
id: omi-flow-change-request
summary: Handle a scope or requirement change after a task was approved: impact on tasks and cost, options with one recommendation, PO decision in decisions.md, then replan. Use when the PO changes their mind or an engineer reports NEEDS SCOPE; no work starts before the decision.
steps:
- id: impact | role: coordinator | skills: omi-skill-change-request | input: change description, affected task files, diff so far | output: impact list of tasks touched, work to redo, cost and time delta | gate: none | stop: every affected task and the rework cost are listed
- id: options | role: omi-agent-architect | skills: omi-skill-change-request | input: impact list | output: 2-3 options with trade-offs and exactly one recommendation | gate: none | stop: one option is marked recommended with the reason
- id: decide | role: coordinator | skills: | input: impact list, options | output: PO decision line in .omi/decisions.md and PO approval line in ## Steps | gate: po | stop: PO picked an option or dropped the change
- id: replan | role: coordinator | skills: omi-skill-task-brief | input: PO decision, affected task files | output: updated or new task files with scope and acceptance criteria; dropped tasks marked | gate: none | stop: task files match the decision and no work ran before it
---
# Change request

**When to use:** requirements, scope or an approved decision change after a task started, or an engineer reported `NEEDS SCOPE`. Why not `omi-flow-feature`: it plans a fresh change and has no impact, options or decision record.
**Use instead:** `omi-flow-feature` for a new change nobody started; `omi-flow-spike` when the question is feasibility, not scope.

## Models
- impact: Coordinator, sonnet/low.
- options: architect, opus/high.
- decide: Coordinator; the PO decides.
- replan: Coordinator, sonnet/low.

## Stop conditions
- No work on the changed scope starts, and running workers on affected tasks are paused, until `decide` is recorded.
- PO drops the change: record it in decisions.md, restore the old plan, stop.
- The change touches auth, secrets, data or CI: replanned tasks use `omi-flow-feature-sensitive`.

## Review-fail rule
Nothing is reviewed here; the replanned tasks are reviewed in their own workflows. If the PO rejects every option, rerun `options` once with the PO's objection, then ask the PO (pick-list: rescope, keep the old plan, drop).

## PO gates
`decide` needs `PO approval decide: <PO's words>` under `## Steps` and a line `date | decision | why | PO chat` in `.omi/decisions.md`; `omi step` refuses otherwise. Merge to staging/main stays with the PO.
