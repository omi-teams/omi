---
id: adapter
summary: Adapter pattern: when to use, when not, signs to remove it
---
# Adapter

## When to use
- Domain or application code needs a port, and an external system (API, SDK, database, framework) has a different shape.
- You want to translate errors and types at the boundary so the outside never leaks inward.

## When not to use
- The external API already matches the port you need.
- A wrapper that renames methods and has one use.

## Signs to remove it
- The adapter holds business rules (they belong in the domain).
- The port changed to mirror the vendor SDK, so the adapter is a pass-through.
- The external system was replaced by an in-process call.

## Sources
- Cockburn, Hexagonal Architecture (ports and adapters), 2005: https://alistair.cockburn.us/hexagonal-architecture/
- Martin, The Clean Architecture, 2012: https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
- Gamma et al., *Design Patterns* (1994), Adapter.
