---
name: omi-idea
description: Turn the PO's idea into an approved product spec and a task backlog.
disable-model-invocation: true
---
0. No `.omi/` in the repo: run `python -m omi init` first, then continue.
1. Ask the PO one question at a time with AskUserQuestion: a pick list in Vietnamese, the recommended option first and marked "(Khuyến nghị)", never a plain-text question. Cover only what is missing: users, problem, v1 features, out of scope, constraints (stack, budget, hosting), success criteria. Don't ask what you can default; state the default instead. Stop at about 10 questions.
2. Once the stack is chosen, propose the root layout and the full `.omi/structure.md` (one line per root entry: `deploy/`, `docs/`, `src/`, `scripts/`, `tests/`, `.github/`, config files; layers and `imports:` as in `.omi/structure.example.md`; `python -m omi structure init` prints a starting map). Write the proposed `.omi/structure.md`, then run `python -m omi structure check`. Fix the map and rerun the check until it exits 0; only then ask the PO to approve it by pick list. On approval commit both on `main` and append to `.omi/decisions.md`: `- <date> | Approve root layout and .omi/structure.md | PO | <commit sha>`. Write steps refuse to start without `.omi/structure.md`.
3. Write `docs/product.md` in Vietnamese, at most 2 pages, with those headings plus the chosen stack and a one-line reason for each choice.
4. Before approval, offer 2-4 spec additions the PO did not ask for (e.g. audit log, export, health check) as one multi-select AskUserQuestion; add the picked ones. Then show a 5-line summary and ask for approval by pick list. Revise until approved. Spawn `omi-agent-reviewer` on the spec only if the PO asks.
5. On approval: commit on `main`, then append to `.omi/decisions.md`: `- <date> | Approve docs/product.md | PO | <commit sha>`.
6. On stack approval, before TASK-001, update `docker/Dockerfile` with the stack's toolchain and `network_allow` in `.omi/config.json` with its registries, so the first worker can build and test:
   | stack | `network_allow` |
   |---|---|
   | npm | registry.npmjs.org |
   | Go | proxy.golang.org, sum.golang.org, storage.googleapis.com |
   | Python | pypi.org, files.pythonhosted.org |
   Fill `host_test` in `.omi/config.json` with the host command that runs the full suite (init and upgrade set it to `sh docker/host-test.sh` when the state holds that script and the field is empty).
7. Create `development` from `main`. On it, split the work into `.omi/tasks/TASK-NNN.md` files from `.omi/tasks/_template.md`. Each task has one outcome, fits in one session, explicit `scope` globs inside the approved layout, and testable acceptance criteria. Set `type`, `parent` and `workflow:` by `omi-skill-issue-types` (lightest fitting workflow from `.omi/workflows/CATALOG.md`). Leave `tool`, `model`, `effort` empty; the Coordinator sets them at task start. TASK-001 is usually the project skeleton plus CI.
8. Commit, run `python -m omi status`, and ask the PO which task to run (pick list).
9. If a git remote exists, push `main` and `development`, then tell the PO to run `python -m omi github --po` once (repo must be public on the Free plan).
