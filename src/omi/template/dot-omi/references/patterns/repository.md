---
id: repository
summary: Repository pattern: when to use, when not, signs to remove it
---
# Repository

## When to use
- Domain code needs to load and save aggregates and the storage (SQL, API, files) must stay outside the domain.
- Several callers run the same non-trivial query, or tests need an in-memory substitute for storage.

## When not to use
- One small CRUD table with one caller; the ORM session or query builder is already the abstraction.
- The interface would have exactly one implementation and no boundary to invert.

## Signs to remove it
- Methods mirror ORM calls one to one (`get`, `save`, `filter`) and add nothing.
- Callers still pass ORM or SQL types through it.
- Tests never use the in-memory implementation.

## Sources
- Fowler, *Patterns of Enterprise Application Architecture* (2002), Repository: https://martinfowler.com/eaaCatalog/repository.html
- Evans, *Domain-Driven Design* (2003), ch. 6 (Repositories).
