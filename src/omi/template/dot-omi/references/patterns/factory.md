---
id: factory
summary: Factory pattern: when to use, when not, signs to remove it
---
# Factory

## When to use
- Creating an object needs a choice among several concrete types, or non-trivial setup callers should not repeat.
- The concrete type must be hidden behind a port.

## When not to use
- One product built with a plain constructor.
- Construction is only a few arguments; a function or classmethod is enough.

## Signs to remove it
- The factory has one product and no branching.
- Callers pass the factory through layers only to call one constructor.
- The factory is a registry nobody extends.

## Sources
- Gamma et al., *Design Patterns* (1994), Abstract Factory and Factory Method.
- Fowler, YAGNI: https://martinfowler.com/bliki/Yagni.html
