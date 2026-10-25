# Decisions

<!-- append-only: - YYYY-MM-DD | decision | why | ref -->
- 2026-10-25 | Restart OMI Squad from scratch in omi-squad2; vision = project-overview.md | PO: old repo's process overhead too heavy | project-overview.md
- 2026-10-25 | v1 cuts: 3 roles, no custom broker, GitHub rulesets for PO merges, no quota forecast, one task at a time | PO: minimise quota/cost | README.md
- 2026-10-25 | Make omi-squad2 public | PO: rulesets need public repo on Free plan; matches vision | TASK-003
- 2026-10-25 | Defer separate omi-skills repo and extra workflows (change request, incident, skills pinning, doctor/update) until the TASK-009 pilot shows real gaps | PO: minimise quota; avoid speculative skills | TASK-011
- 2026-10-25 | Add TASK-012 (guard hardening), tag ruleset in TASK-010, Docker pitfalls in TASK-006 | review of ../omi-squad found scope self-widening, outside writes and unprotected rc tags | TASK-012
- 2026-10-25 | PO GitHub account not kept logged in on the squad machine; PO runs `omi github` with a one-off token and merges staging/main in the web UI | squad shell could otherwise use the PO token (guard does not cover Bash) | TASK-010
- 2026-10-25 | Add TASK-013 (omi github --po) while TASK-009 pilot is paused | PO asked for fewer steps; every OMI project needs this step | TASK-013
- 2026-10-25 | Coordinator session default model = sonnet in the template (settings.json "model") | pilot: the Coordinator on opus was ~80% of cache reads; sonnet is enough for clarify/plan/delegate | TASK-014
