---
id: strategy
summary: Strategy pattern: when to use, when not, signs to remove it
---
# Strategy

## When to use
- One step has several interchangeable algorithms chosen at run time (pricing rule, retry policy, export format).
- Adding a variant should not edit the caller.

## When not to use
- Two fixed branches that will not grow: use an `if` or a function argument.
- A plain function passed as a parameter already does the job; no class is needed.

## Signs to remove it
- Only one strategy has existed for a long time.
- The caller still switches on a type to pick the strategy.
- Strategies share state with the caller and cannot be tested alone.

## Sources
- Gamma, Helm, Johnson, Vlissides, *Design Patterns* (1994), Strategy, ISBN 0-201-63361-2.
- Fowler, YAGNI: https://martinfowler.com/bliki/Yagni.html
