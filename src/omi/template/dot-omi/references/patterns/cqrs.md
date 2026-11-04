---
id: cqrs
summary: CQRS pattern: when to use, when not, signs to remove it
---
# CQRS

## When to use
- Read and write models have clearly different shapes or load (rich domain writes, flat denormalized reads).
- Reads must scale or evolve separately from writes.

## When not to use
- Plain CRUD with one model; the split only doubles the code.
- Most of the system is not a complex domain. Fowler warns it adds risky complexity to most systems.

## Signs to remove it
- The read model is the write model copied under another name.
- Teams fight eventual consistency nobody needed.
- Commands and queries share the same tables and types anyway.

## Sources
- Fowler, CQRS: https://martinfowler.com/bliki/CQRS.html
- Young, CQRS Documents (2010).
