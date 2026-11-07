---
id: anti-patterns
summary: Anti-patterns per stack: god module, utils black hole, framework in domain, module import cycles
---
# Anti-patterns

## When to use
Read before writing a `Pattern:` line or when a review flags structure. Each entry gives the symptom, the stack where it shows, and the fix.
- God module: one file with many responsibilities (Python `service.py`, TS `index.ts`, Go `util.go`). Split by concept; name files after what they do.
- `utils` black hole: `utils`, `helpers`, `common` collect unrelated code. Move each function next to its only caller or into a named module.
- Framework in domain: ORM models, `Request` objects or decorators imported by domain code (Django, Next.js, Spring). Keep the domain free of outer-layer names; translate in an adapter.
- Module import cycles: A imports B imports A (Python, TS, Go refuses at compile time). Fix the layering; never import inside a function to dodge it.

## When not to use
Do not split a file only because it is long if it has one responsibility. A shared `utils` of three truly generic functions is not a black hole yet.

## Signs to remove it
A fix is working when file names describe one concept, no inner layer imports an outer one, and the import graph has no cycle.

## Sources
- Martin, The Clean Architecture, 2012 (dependencies point inward): https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
- Martin, *Clean Architecture* (2017), ch. 14 (Component Coupling, Acyclic Dependencies Principle).
- import-linter contract types (layers, forbidden): https://import-linter.readthedocs.io/en/stable/contract_types/
