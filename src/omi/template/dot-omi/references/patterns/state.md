---
id: state
summary: State pattern: when to use, when not, signs to remove it
---
# State

## When to use
- An object's behavior changes with a state that has many transitions, and the same `if state ==` branches repeat across methods.
- Illegal transitions must be rejected in one place.

## When not to use
- Two or three states with a single status field and one switch.
- A transition table (dict of allowed moves) already expresses the rules.

## Signs to remove it
- State classes only delegate and hold no behavior of their own.
- The set of states is stable and small, and one table would be shorter.
- Every new rule still edits several state classes.

## Sources
- Gamma et al., *Design Patterns* (1994), State.
- Fowler, YAGNI: https://martinfowler.com/bliki/Yagni.html
