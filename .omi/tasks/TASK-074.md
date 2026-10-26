---
id: TASK-074
title: Versioned omi package - omi --version, project version stamp, install from a tag
status: in-progress
depends:
scope: pyproject.toml, src/omi/__init__.py, tests/**, src/omi/template/**, README.md
role: omi-agent-engineer
skills: [omi-skill-windows-powershell]
refs:
plan:
tool:
model: sonnet
effort: medium
workflow: omi-flow-feature
step:
---
## Goal
omi has one version (SemVer 0.x, in `pyproject.toml`), shows it, stamps it into each project on `omi init`, tells the PO when a project is older than the installed omi, and installs cleanly from a git tag. Bump to 0.2.0 (rules, references, plans, hooks, model per task).

## Acceptance criteria
- [ ] `pyproject.toml` is the only place the version is written; `version = "0.2.0"`.
- [ ] `omi --version` (and `omi version`) prints `omi 0.2.0`, read with `importlib.metadata`; when omi runs from a source checkout without being installed, it falls back to `pyproject.toml`. Tested both ways.
- [ ] `omi init` writes `.omi/version` with the running version (also when re-run on an existing project, so the stamp follows the files it added). Tested.
- [ ] `omi status` prints `omi <installed> (project <stamp>)` and, when the stamp is missing or older (SemVer compare, no new dependency), one line `run \`omi init\` to add the files of omi <installed>`. Tested.
- [ ] Every file under `src/omi/template` is covered by `[tool.setuptools.package-data]`, including dot-dirs stored as `dot-*`, `.sh` hooks and `references/` under skills. Tested by matching the globs against the file list.
- [ ] Template `post-run.sh` runs the `test` command from `.omi/config.json` when it is set, before the go/npm/pytest detection. Tested with `sh` in a temp dir.
- [ ] README install section: `pipx install git+https://github.com/omi-teams/omi-squad2@v0.2.0`, upgrade (`pipx install --force ...@<tag>`, then `omi init` in each project), `omi --version`.
- [ ] Real install (Coordinator, Windows host): `pip install` of this branch into a fresh venv, then `omi --version` and `omi init` into an empty dir create `.omi/version`, rules, references, plans and hooks.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done:
Not done:
Tests:
Next:
