---
name: omi-idea
description: Turn the PO's idea into an approved product spec and a task backlog.
disable-model-invocation: true
---
1. Ask the PO one question at a time, in Vietnamese, each with a suggested answer they can just accept. Cover only what is missing: users, problem, v1 features, out of scope, constraints (stack, budget, hosting), success criteria. Don't ask what you can default; state the default instead. Stop at about 10 questions.
2. Write `docs/product.md` in Vietnamese, at most 2 pages, with those headings plus the chosen stack and a one-line reason for each choice.
3. Show the PO a 5-line summary and ask for approval. Revise until approved. Spawn `omi-agent-reviewer` on the spec only if the PO asks.
4. On approval: commit on `main`, then append to `.omi/decisions.md`: `- <date> | Approve docs/product.md | PO | <commit sha>`.
5. Create `development` from `main`. On it, split the work into `.omi/tasks/TASK-NNN.md` files from `.omi/tasks/_template.md`. Each task has one outcome, fits in one session, explicit `scope` globs, and testable acceptance criteria. Pick the lightest fitting workflow from `.omi/workflows/CATALOG.md` and write it as `workflow:`. TASK-001 is usually the project skeleton plus CI.
6. Commit, run `python -m omi status`, and ask the PO which task to run.
7. If a git remote exists, push `main` and `development`, then tell the PO to run `python -m omi github --po` once (repo must be public on the Free plan).
