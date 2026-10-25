# Decisions

<!-- append-only: - YYYY-MM-DD | decision | why | ref -->
- 2026-10-25 | Restart OMI Squad from scratch in omi-squad2; vision = project-overview.md | PO: old repo's process overhead too heavy | project-overview.md
- 2026-10-25 | v1 cuts: 3 roles, no custom broker, GitHub rulesets for PO merges, no quota forecast, one task at a time | PO: minimise quota/cost | README.md
- 2026-10-25 | Make omi-squad2 public | PO: rulesets need public repo on Free plan; matches vision | TASK-003
- 2026-10-25 | Defer separate omi-skills repo and extra workflows (change request, incident, skills pinning, doctor/update) until the TASK-009 pilot shows real gaps | PO: minimise quota; avoid speculative skills | TASK-011
- 2026-10-25 | Add TASK-012 (guard hardening), tag ruleset in TASK-010, Docker pitfalls in TASK-006 | review of ../omi-squad found scope self-widening, outside writes and unprotected rc tags | TASK-012
