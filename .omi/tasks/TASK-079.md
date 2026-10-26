---
id: TASK-079
title: omi upgrade and /omi-upgrade - install a newer omi and update unmodified template files
status: in-progress
depends: TASK-078
scope: src/omi/__init__.py, src/omi/template_shas.json, pyproject.toml, tests/**, src/omi/template/**, .claude/skills/omi-upgrade/**, AGENTS.md, README.md
role: omi-agent-engineer
skills: [omi-skill-windows-powershell]
refs:
plan: PLAN-001
tool: claude
model: sonnet
effort: medium
workflow: omi-flow-feature-sensitive
step: build
---
## Goal
A project that runs omi moves to a newer omi with one PO command: install the new version, add new template files, update template files the project never changed, and list the ones it did change for the PO to decide. This also fixes Dockerfile drift.

## Acceptance criteria
- [ ] `omi init` writes `.omi/manifest.json`: `{"version": X, "files": {"<project path>": "<sha256 of the template file it installed>"}}` for every template file it creates. A project without a manifest gets one on its next `omi init`/`omi upgrade`, recording only files that are byte-identical (CRLF/LF ignored) to the current template or to a released template listed in `src/omi/template_shas.json` (`{"0.2.0": {path: sha}}`, built once from tag v0.2.0, shipped as package data). Tested.
- [ ] `omi upgrade --check` lists remote tags (`git ls-remote --tags` of `omi_repo` in `.omi/config.json`, default https://github.com/omi-teams/omi-squad2), picks the highest `vX.Y.Z` (SemVer, ignores date tags), and prints `omi <installed> -> <latest>` or `up to date`. Tested with a fake subprocess.
- [ ] `omi upgrade [--to vX.Y.Z]` runs `python -m pip install --user --upgrade "git+<omi_repo>@<tag>"`, then runs `python -m omi upgrade --apply` in a new process so the newly installed omi updates the project. Tested on argv.
- [ ] `omi upgrade --apply`: per template file, missing in the project -> create; unchanged since install (sha matches manifest) -> overwrite with the new template; changed by the project -> keep it, print `kept (modified): <path>`, and write the new version next to it as `<path>.omi-new`. Then update `.omi/manifest.json` and `.omi/version`, regenerate catalogs, print a summary. Never touch task files (`.omi/tasks/TASK-*`; `_template.md` is a template file and is updated like the others), `.omi/plans/PLAN-*` other than PLAN-000, `.omi/decisions.md`; `.omi/config.json` only gains new keys from the template, existing values stay. Tested.
- [ ] Skill `.claude/skills/omi-upgrade/SKILL.md` (root and template) and an AGENTS.md line for `omi-upgrade`: run `--check`, ask the PO (pick-list) which version, run the upgrade, show the summary, for each `.omi-new` ask the PO keep / take new / merge, then commit on `development` and run the tests.
- [ ] README upgrade section uses `/omi-upgrade` or `python -m omi upgrade`.
- [ ] Real check (Coordinator): a sandbox initialised with 0.2.0 files plus one locally edited template file runs `--apply` with this branch's code: new files created, unchanged files updated, the edited file kept with a `.omi-new` next to it.
- [ ] All tests pass on the Linux worker and the Windows host.

## Checkpoint
Done: review round 3 fix. `upgrade_write_safe` checks every upgrade write destination before use: template creation/update, `.omi-new`, config, manifest, version, and all six catalogs. A symlink (including a linked parent directory) or a resolved path outside the project is skipped with `skip (symlink): <path>`. Unsafe config/manifest paths are also skipped before parsing. Existing round 1/2 fixes remain in place.
Not done: Windows host rerun for round 3 and Coordinator security review.
Tests: targeted upgrade tests and `python3 tests/test_omi.py` passed (Linux, exit 0, ok). New regressions cover `.omi-new` links to decisions.md and outside the project, an updated file link, a dangling creation target, linked config/manifest/version/catalogs, and directory links redirecting writes outside the project or into task data. Tests skip symlink cases when creation raises OSError on Windows.
Security round 1 fix: init guards manifest and version with upgrade_write_safe; test_init_symlink_manifest added; Linux tests pass.
Next: Coordinator security review, rerun tests on Windows, then commit on the host. Suggested commit: fix: skip symlink destinations during omi upgrade

Coordinator note for build: git does not work in the worker, so the v0.2.0 hashes cannot be read there. Provide a function that maps a template directory to {posix rel: norm_sha} and a CLI entry the Coordinator can run on the host, e.g. `python -m omi template-shas <template-dir> <version>` writing/merging `src/omi/template_shas.json`. Commit an empty `{}` placeholder; the Coordinator runs it against an export of tag v0.2.0 and commits the data. Tests use a tmp template dir.

Coordinator host steps (2026-10-26):
- template_shas.json: `git archive v0.2.0 src/omi/template` exported, `python -m omi template-shas <export>/src/omi/template 0.2.0` with this branch -> 61 files.
- Windows: `python tests/test_omi.py` -> rc=0, ok.
- Real check: sandbox `git init` + v0.2.0 `omi init` (no manifest), appended a line to .omi/agents/omi-agent-reviewer.md, then this branch's `omi upgrade --apply` -> `1 created, 8 updated, 1 kept`; created .claude/skills/omi-upgrade/SKILL.md, updated AGENTS.md, docker/Dockerfile, docker/proxy.py and 5 more; `kept (modified): .omi/agents/omi-agent-reviewer.md` with `omi-agent-reviewer.md.omi-new` next to it; .omi/version and .omi/manifest.json written.

Review round 1 FAIL:
- latest_tag: `git ls-remote` of the real repo returns tags rc-20261026-d55dcd3, v0.2.0 and v2026.10.26; latest_tag picks v2026.10.26 today (verified on the host). Date tags in vYYYY.MM.DD form are not releases: tags with major >= 1000 are ignored, and `--to` rejects them the same way. The existing test uses `2026-10-01`, which never matched; it needs the v2026.10.26 form.
- `upgrade --to` without a value installs the latest version silently (reviewer reproduced it). A missing value exits with the usage line before any install.
- `.omi/tasks/_template.md` being updated is intended (PO decision; criterion text clarified). No change needed.

Coordinator host check after review round 1 fix: latest_tag on the real repo -> v0.2.0 (was v2026.10.26); Windows `python tests/test_omi.py` -> rc=0, ok.

Review round 2 FAIL (escalated to opus/high by PO):
- omi_repo from .omi/config.json reaches `git ls-remote --tags <repo>` as a positional argument; a value like `--upload-pack=<cmd>` is read as an option. omi_repo is validated (https://, ssh://, git@host:path; no leading `-`, no whitespace) before any use, ls-remote gets `--` before the repo, and the pip `git+{repo}@{tag}` URL uses the same validated value. Tests for rejected values.
- released_shas re-reads template_shas.json per file; it is loaded once per run.
- upgrade_apply: .omi/config.json is parsed before any file changes; invalid JSON exits with a clear message and nothing changed.
- Type hints on the new public functions (.omi/rules/python.md).
- A test that protected() keeps PLAN-001 and updates PLAN-000.
Note: the Windows run after review round 1 is recorded above (rc=0, ok).

Coordinator host check after review round 2 fix: Windows `python tests/test_omi.py` -> rc=0; latest_tag on the real repo -> v0.2.0.

Review round 3 FAIL (PO chose a small fix, then security review):
- upgrade_apply writes (create, update, `.omi-new`, manifest, version, config) follow symlinks: a `<path>.omi-new` symlink to ../decisions.md or outside the repo gets overwritten. Every write target that is a symlink, or whose resolved path is outside the project root, is skipped with a `skip (symlink): <path>` line. Tests: a `.omi-new` symlink and an updated file that is a symlink both leave their targets unchanged. On Windows, creating symlinks may need privileges; the tests skip that part when os.symlink raises OSError.

Coordinator host check after review round 3 fix: Windows `python tests/test_omi.py` -> rc=0, ok.

Open (review round 4 PASS, low severity, later task): scp-form omi_repo breaks the pip URL; non-dict config.json fails after files are written; `--to` still calls ls-remote; stale `.omi-new` overwritten on a repeat apply.

Security round 1 FAIL:
- init reads and writes .omi/manifest.json (and .omi/version) without the symlink guard; a manifest symlink to a JSON file outside the project gets overwritten. init uses upgrade_write_safe for the manifest and version, the same way upgrade_apply does. Test: a manifest symlink leaves its target unchanged (skip when os.symlink raises OSError).

## Steps
- plan started 2026-10-26 22:07
- plan done 2026-10-26 22:07
- architect started 2026-10-26 22:07
- architect done 2026-10-26 22:10
- build started 2026-10-26 22:10
- build done 2026-10-26 22:15
- review started 2026-10-26 22:15
- review failed 2026-10-26 22:18
- build started 2026-10-26 22:18
- build done 2026-10-26 22:22
- review started 2026-10-26 22:22
- review failed 2026-10-26 22:24
- build started 2026-10-26 22:24
- build done 2026-10-26 22:30
- review started 2026-10-26 22:30
- review failed 2026-10-26 22:34
- build started 2026-10-26 22:34
- build done 2026-10-26 22:40
- review started 2026-10-26 22:40
- review done 2026-10-26 22:42
- security started 2026-10-26 22:42
- security failed 2026-10-26 22:51
- build started 2026-10-26 22:51

## Reports
2026-10-26 22:08 omi-agent-architect (claude):
> RECOMMEND: B - a manifest plus a shipped `known_shas` file for v0.2.0, so a 0.2.0 project with no manifest (every project today) gets its unchanged files updated instead of flooded with `.omi-new`.
> OPTIONS: A: manifest only, backfilled from the current template / smallest and matches AC1 word for word, but on the first upgrade from 0.2.0 every unchanged file differs from the 0.3.0 template, so all are "kept (modified)" and the Coordinator real check fails; B: A plus `src/omi/template_shas.json` (`{"0.2.0": {path: sha}}`, built once from tag v0.2.0) so a file matching a released sha is backfilled as unmodified / one extra data file, its hashes must be correct, and it extends AC1's backfill rule; C: hashes computed at run time from `git show v0.2.0` / git is often missing in the installed package and needs the omi repo, so it is fragile.
> [... truncated ...]
> NEEDS DECISION: AC1 says backfill records only files identical to the *current* template, but the real check expects a no-manifest 0.2.0 sandbox to have its unchanged files *updated*. Approve B's extension (also match released v0.2.0 hashes), or keep A and have the real check run on a sandbox made by this branch's `omi init`?
2026-10-26 22:13 omi-agent-engineer (claude):
> DONE (the v0.2.0 hashes still need to be generated on the host, see open issues)
> - Files changed:
>   - `src/omi/__init__.py`, `src/omi/template_shas.json` (`{}` placeholder), `pyproject.toml` (package data)
>   - `tests/test_omi.py`
>   - `.claude/skills/omi-upgrade/SKILL.md` and the same file under `src/omi/template/dot-claude/skills/`
>   - `AGENTS.md` and `src/omi/template/AGENTS.md`, `README.md`, and the TASK-079 checkpoint
> - Commit message: `feat: omi upgrade with install manifest, .omi-new for modified template files`
> - Tests: `python3 tests/test_omi.py` passes on Linux. I did not run the Windows host or the real sandbox check.
> - Open issue: `template_shas.json` is empty. Run `python -m omi template-shas <v0.2.0 export>/src/omi/template 0.2.0` on the host and commit the result. Until then, a 0.2.0 project without a manifest will see its edited and unedited files all kept as modified.
> - `CATALOG.md` files are excluded from the manifest and from `--apply`, because every `init` and `--apply` regenerates them.
> - `.omi/tasks/_template.md` is updated by `--apply`; every other file under `.omi/tasks` is untouched.
> - `--check` prints the latest tag without the `v` (`omi 0.2.0 -> 0.3.0`). The pip and `--apply` subprocess calls use `sys.executable`, not a literal `python`.
2026-10-26 22:14 hook post-run passed:
> Conflict. The container name "/tmp31dl45um-TASK-001-engineer-codex-gpt-x-medium-151325" is already in useBind for 0.0.0.0:8080 failed: port is already in usewrote /tmp/tmp9xre0yaz/.omi/skills/CATALOG.md (2 skills)
> create AGENTS.md
> create docker/Dockerfile
> create docker/prove.sh
> create docker/proxy.py
> create .claude/settings.json
> create .claude/skills/omi-idea/SKILL.md
> create .claude/skills/omi-release/SKILL.md
> create .claude/skills/omi-status/SKILL.md
> create .claude/skills/omi-task/SKILL.md
> create .claude/skills/omi-upgrade/SKILL.md
> create .omi/agents/omi-agent-architect.md
> create .omi/agents/omi-agent-designer-ui.md
> create .omi/agents/omi-agent-devops.md
> create .omi/agents/omi-agent-docs-writer.md
> create .omi/agents/omi-agent-engineer.md
> create .omi/agents/omi-agent-qa-tester.md
> create .omi/agents/omi-agent-researcher.md
> create .omi/agents/omi-agent-reviewer.md
> create .omi/agents/omi-agent-security-reviewer.md
> create .omi/config.json
> create .omi/decisions.md
> create .omi/hooks/post-run.sh
> create .omi/plans/PLAN-000.md
> create .omi/references/nextjs-app-router.md
> create .omi/references/postgres-conventions.md
> create .omi/rules/docker.md
> create .omi/rules/go.md
> create .omi/rules/nextjs.md
> create .omi/rules/postgres.md
> create .omi/rules/python.md
> create .omi/skills/.gitkeep
> create .omi/skills/data/omi-skill-data-review/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-docker-worker-pitfalls/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-incident/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-release-checklist/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-rollback/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-windows-powershell/SKILL.md
> create .omi/skills/qa-web/omi-skill-web-qa/SKILL.md
> create .omi/skills/quality/omi-skill-ci-workflow-audit/SKILL.md
> create .omi/skills/quality/omi-skill-debug-root-cause/SKILL.md
> create .omi/skills/quality/omi-skill-diff-security-review/SKILL.md
> create .omi/skills/quality/omi-skill-simplify-review/SKILL.md
> [... truncated ...]
> ok
2026-10-26 22:17 omi-agent-reviewer (codex):
> VERDICT: FAIL
> - src/omi/__init__.py:817 `.omi/tasks/_template.md` is explicitly eligible for creation or replacement, violating “Never touch .omi/tasks” -> protect every path under `.omi/tasks/`.
> - src/omi/__init__.py:890 A bare `upgrade --to` silently installs the latest version; reproduced with mocked subprocesses -> reject missing flag values before running installation.
> 
> AC: Init manifest and legacy backfill ✓ `test_upgrade` passes; shipped hashes contain 61 v0.2.0 files; package data includes them.
> AC: Remote version check ✓ `test_upgrade_cmd` verifies numeric version ordering, date-tag exclusion, and check output.
> AC: Install and new-process apply ✓ `test_upgrade_cmd` verifies pip and apply argv for a valid explicit tag.
> AC: Apply updates and preserves protected content ✗ Task-template exemption violates directory protection; other update, preservation, config, and stamping checks pass.
> AC: Upgrade skills and AGENTS entries ✓ Root and template contain the required workflow and command entry.
> AC: README upgrade instructions ✓ Documents `python -m omi upgrade` and `/omi-upgrade`.
> AC: Real v0.2.0 sandbox check ✓ Coordinator records 1 created, 8 updated, 1 modified file preserved with `.omi-new`; not independently repeated.
> AC: Linux and Windows tests ✓ `python3 tests/test_omi.py` completed with exit 0 and `ok`; Coordinator records Windows exit 0.
2026-10-26 22:21 omi-agent-engineer (codex):
> DONE
> Files changed: `src/omi/__init__.py`, `tests/test_omi.py`, `.omi/tasks/TASK-079.md`.
> Fixed date-tag filtering and missing/invalid `--to` validation.
> Suggested commit: `fix: validate omi upgrade release tags and target arguments`
> Tests: regression tests and `python3 tests/test_omi.py` passed on Linux.
> Checkpoint updated; no commit made.
> Open issue: Coordinator must rerun tests on Windows.
2026-10-26 22:21 hook post-run passed:
> Conflict. The container name "/tmpm6eamj5d-TASK-001-engineer-codex-gpt-x-medium-152112" is already in useBind for 0.0.0.0:8080 failed: port is already in usewrote /tmp/tmpaoo3jwew/.omi/skills/CATALOG.md (2 skills)
> create AGENTS.md
> create docker/Dockerfile
> create docker/prove.sh
> create docker/proxy.py
> create .claude/settings.json
> create .claude/skills/omi-idea/SKILL.md
> create .claude/skills/omi-release/SKILL.md
> create .claude/skills/omi-status/SKILL.md
> create .claude/skills/omi-task/SKILL.md
> create .claude/skills/omi-upgrade/SKILL.md
> create .omi/agents/omi-agent-architect.md
> create .omi/agents/omi-agent-designer-ui.md
> create .omi/agents/omi-agent-devops.md
> create .omi/agents/omi-agent-docs-writer.md
> create .omi/agents/omi-agent-engineer.md
> create .omi/agents/omi-agent-qa-tester.md
> create .omi/agents/omi-agent-researcher.md
> create .omi/agents/omi-agent-reviewer.md
> create .omi/agents/omi-agent-security-reviewer.md
> create .omi/config.json
> create .omi/decisions.md
> create .omi/hooks/post-run.sh
> create .omi/plans/PLAN-000.md
> create .omi/references/nextjs-app-router.md
> create .omi/references/postgres-conventions.md
> create .omi/rules/docker.md
> create .omi/rules/go.md
> create .omi/rules/nextjs.md
> create .omi/rules/postgres.md
> create .omi/rules/python.md
> create .omi/skills/.gitkeep
> create .omi/skills/data/omi-skill-data-review/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-docker-worker-pitfalls/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-incident/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-release-checklist/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-rollback/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-windows-powershell/SKILL.md
> create .omi/skills/qa-web/omi-skill-web-qa/SKILL.md
> create .omi/skills/quality/omi-skill-ci-workflow-audit/SKILL.md
> create .omi/skills/quality/omi-skill-debug-root-cause/SKILL.md
> create .omi/skills/quality/omi-skill-diff-security-review/SKILL.md
> create .omi/skills/quality/omi-skill-simplify-review/SKILL.md
> [... truncated ...]
> ok
2026-10-26 22:24 omi-agent-reviewer (claude):
> VERDICT: FAIL
> - src/omi/__init__.py:444 `omi_repo` comes from the project's `.omi/config.json` and is passed to `git ls-remote --tags <repo>` as a positional argument. A cloned project can set it to `--upload-pack=<cmd>`, which git reads as an option. With a local or ssh `origin`, `omi upgrade --check` could then run that command. I did not run an exploit. -> Validate `omi_repo` (https/ssh/git URL, no leading `-`) and call `["git","ls-remote","--tags","--",repo]`. Apply the same check before building `git+{repo}@{tag}` for pip.
> - src/omi/__init__.py:329 `released_shas` re-reads and parses `template_shas.json` for every file in `init` and `upgrade_apply`, about 60 times per run. -> Load it once, or pass it in.
> - src/omi/__init__.py:417-423 `upgrade_apply` rewrites `.omi/config.json` after the files are already changed. An invalid-JSON config raises a traceback and leaves the project half-upgraded, with no manifest or version written. -> Parse the config first and exit with a clear message, or guard the failure.
> - src/omi/__init__.py:290-466 The new public functions (`norm_sha`, `template_map`, `upgrade_apply`, `latest_tag` and others) have no type hints, but `.omi/rules/python.md` requires them (only `release_tag` has any). -> Add hints.
> 
> AC: `omi init` manifest and backfill ✓ `test_upgrade` passes. `init` writes the manifest. Without one, pristine files and CRLF variants are backfilled and an edited AGENTS.md is not. A fake released template counts as pristine. `template_shas.json` ships in package data with 61 v0.2.0 entries.
> AC: `--check` ✓ `test_upgrade_cmd` uses a fake `subprocess.run`. It picks v0.10.0 over v0.9.0 and ignores `^{}`, `v2026.10.26`, `v1000.0.0` and rc tags. The output is `omi <ver> -> 0.10.0`, and the ls-remote argv is asserted.
> [... truncated ...]
> Scope ✓ All changed files are within `scope`.
2026-10-26 22:28 omi-agent-engineer (claude):
> DONE
> 
> - **Files changed:** `src/omi/__init__.py`, `tests/test_omi.py`, `.omi/tasks/TASK-079.md` (checkpoint).
> - **`omi_repo` fix:** the new `valid_repo` accepts only `https://`, `ssh://` and `git@host:path`, and rejects whitespace and a leading `-`, including straight after the scheme. An invalid value stops `--check`, the install and `--to` with `invalid omi_repo ...` before git or pip runs. `git ls-remote` now gets `--` before the repo.
> - **Other review fixes:**
>   - `released_shas()` reads `template_shas.json` once per `init` and `upgrade_apply` run.
>   - `upgrade_apply` reads `.omi/config.json` before changing any file. Invalid JSON stops it with a clear message and nothing changed.
>   - All the new public functions now have type hints.
> - **New tests:** PLAN-001 is kept and PLAN-000 is updated; rejected repo values start no subprocess; a broken config changes no files; the hash file is read once. The new tests are added to the test file's explicit run list.
> - **Tests:** `python3 tests/test_omi.py` passes on Linux (exit 0, `ok`).
> - **Open:** the tests still need a rerun on the Windows host (Coordinator).
> - **Commit:** `fix: validate omi_repo, load released hashes once, check config before omi upgrade --apply`
2026-10-26 22:29 hook post-run passed:
> Conflict. The container name "/tmpvqx9vygc-TASK-001-engineer-codex-gpt-x-medium-152857" is already in useBind for 0.0.0.0:8080 failed: port is already in usewrote /tmp/tmptz4egl0a/.omi/skills/CATALOG.md (2 skills)
> create AGENTS.md
> create docker/Dockerfile
> create docker/prove.sh
> create docker/proxy.py
> create .claude/settings.json
> create .claude/skills/omi-idea/SKILL.md
> create .claude/skills/omi-release/SKILL.md
> create .claude/skills/omi-status/SKILL.md
> create .claude/skills/omi-task/SKILL.md
> create .claude/skills/omi-upgrade/SKILL.md
> create .omi/agents/omi-agent-architect.md
> create .omi/agents/omi-agent-designer-ui.md
> create .omi/agents/omi-agent-devops.md
> create .omi/agents/omi-agent-docs-writer.md
> create .omi/agents/omi-agent-engineer.md
> create .omi/agents/omi-agent-qa-tester.md
> create .omi/agents/omi-agent-researcher.md
> create .omi/agents/omi-agent-reviewer.md
> create .omi/agents/omi-agent-security-reviewer.md
> create .omi/config.json
> create .omi/decisions.md
> create .omi/hooks/post-run.sh
> create .omi/plans/PLAN-000.md
> create .omi/references/nextjs-app-router.md
> create .omi/references/postgres-conventions.md
> create .omi/rules/docker.md
> create .omi/rules/go.md
> create .omi/rules/nextjs.md
> create .omi/rules/postgres.md
> create .omi/rules/python.md
> create .omi/skills/.gitkeep
> create .omi/skills/data/omi-skill-data-review/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-docker-worker-pitfalls/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-incident/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-release-checklist/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-rollback/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-windows-powershell/SKILL.md
> create .omi/skills/qa-web/omi-skill-web-qa/SKILL.md
> create .omi/skills/quality/omi-skill-ci-workflow-audit/SKILL.md
> create .omi/skills/quality/omi-skill-debug-root-cause/SKILL.md
> create .omi/skills/quality/omi-skill-diff-security-review/SKILL.md
> create .omi/skills/quality/omi-skill-simplify-review/SKILL.md
> [... truncated ...]
> ok
2026-10-26 22:32 omi-agent-reviewer (codex):
> VERDICT: FAIL
> - src/omi/__init__.py:859 Writing `.omi-new` follows existing symlinks and can overwrite protected files. For example, a modified `.omi/rules/python.md` with `python.md.omi-new -> ../decisions.md` causes decisions.md to be overwritten -> reject symlink destinations and resolve parent paths before writing.
> 
> AC: Init manifest and legacy backfill ✓ `test_upgrade` passes; 61 released hashes are shipped as package data.
> AC: Remote version check ✓ Fake subprocess tests verify version ordering, date-tag exclusion, and output.
> AC: Install and new-process apply ✓ `test_upgrade_cmd` verifies pip and apply argv.
> AC: Apply and protected-file preservation ✗ Normal update paths pass tests; symlink destinations bypass protection.
> AC: Upgrade skills and AGENTS entries ✓ Root and template contain the required workflow and command entry.
> AC: README upgrade instructions ✓ Documents `python -m omi upgrade` and `/omi-upgrade`.
> AC: Real sandbox check ✓ Coordinator records creation, updates, and preservation of an edited file with `.omi-new`.
> AC: Linux and Windows tests ✓ Linux suite completed with exit 0 and `ok`; Coordinator records Windows exit 0.
2026-10-26 22:39 omi-agent-engineer (codex):
> DONE — upgrade writes now skip symlinks and destinations outside the project.
> Files changed: `src/omi/__init__.py`, `tests/test_omi.py`, `.omi/tasks/TASK-079.md`.
> Suggested commit: `fix: skip symlink destinations during omi upgrade`
> Tests: targeted regressions and `python3 tests/test_omi.py` passed on Linux (exit 0).
> Checkpoint updated; no commit made.
> Open issues: Coordinator security review and Windows rerun.
2026-10-26 22:40 hook post-run passed:
> Conflict. The container name "/tmpcpzdz2jn-TASK-001-engineer-codex-gpt-x-medium-153909" is already in useBind for 0.0.0.0:8080 failed: port is already in usewrote /tmp/tmpspp83913/.omi/skills/CATALOG.md (2 skills)
> create AGENTS.md
> create docker/Dockerfile
> create docker/prove.sh
> create docker/proxy.py
> create .claude/settings.json
> create .claude/skills/omi-idea/SKILL.md
> create .claude/skills/omi-release/SKILL.md
> create .claude/skills/omi-status/SKILL.md
> create .claude/skills/omi-task/SKILL.md
> create .claude/skills/omi-upgrade/SKILL.md
> create .omi/agents/omi-agent-architect.md
> create .omi/agents/omi-agent-designer-ui.md
> create .omi/agents/omi-agent-devops.md
> create .omi/agents/omi-agent-docs-writer.md
> create .omi/agents/omi-agent-engineer.md
> create .omi/agents/omi-agent-qa-tester.md
> create .omi/agents/omi-agent-researcher.md
> create .omi/agents/omi-agent-reviewer.md
> create .omi/agents/omi-agent-security-reviewer.md
> create .omi/config.json
> create .omi/decisions.md
> create .omi/hooks/post-run.sh
> create .omi/plans/PLAN-000.md
> create .omi/references/nextjs-app-router.md
> create .omi/references/postgres-conventions.md
> create .omi/rules/docker.md
> create .omi/rules/go.md
> create .omi/rules/nextjs.md
> create .omi/rules/postgres.md
> create .omi/rules/python.md
> create .omi/skills/.gitkeep
> create .omi/skills/data/omi-skill-data-review/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-docker-worker-pitfalls/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-incident/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-release-checklist/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-rollback/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-windows-powershell/SKILL.md
> create .omi/skills/qa-web/omi-skill-web-qa/SKILL.md
> create .omi/skills/quality/omi-skill-ci-workflow-audit/SKILL.md
> create .omi/skills/quality/omi-skill-debug-root-cause/SKILL.md
> create .omi/skills/quality/omi-skill-diff-security-review/SKILL.md
> create .omi/skills/quality/omi-skill-simplify-review/SKILL.md
> [... truncated ...]
> ok
2026-10-26 22:42 omi-agent-reviewer (claude):
> VERDICT: PASS
> - src/omi/__init__.py:623 `valid_repo` accepts scp-style `git@host:path`, but `upgrade_cmd` puts it into `git+{repo}@{tag}` for pip (line 665). pip needs `git+ssh://git@host/path`, so the install fails for that form while `--check` works. -> Reject the scp form, or convert it to `ssh://git@host/path` before building the pip URL. Low severity.
> - src/omi/__init__.py:605-608 `upgrade_apply` assumes `config.json` parses to a dict. A valid JSON non-dict, such as `[]`, makes `merge_keys` raise `AttributeError` after the template files are already written, with no manifest or version stamp. The round-2 fix only guarded invalid JSON. -> Check `isinstance(old_cfg, dict)` in the pre-flight and exit with the same "nothing was changed" message. Low severity.
> - src/omi/__init__.py:657-660 `upgrade --to vX.Y.Z` still calls `git ls-remote` and exits with "no vX.Y.Z tag" if the remote has none. An explicit tag does not need that lookup. -> Skip `latest_tag` when `requested` is set and not `--check`. Low severity.
> - src/omi/__init__.py:601-604 After a modified file is later resolved, a stale `<path>.omi-new` stays on disk, and a repeat `--apply` overwrites it silently. No data loss; the skill tells the PO to delete it. Informational only.
> 
> AC: `omi init` writes the manifest and backfills a project that has none ✓ `test_upgrade` covers a fresh init, a CRLF-modified pristine file, an edited `AGENTS.md` that is not recorded, and a fake released template. `template_shas.json` has 61 entries for 0.2.0 and is listed in `pyproject.toml` package-data.
> [... truncated ...]
> Rules and scope: type hints are present on the new public functions and files are read as UTF-8, which matches python.md. The docker rule does not apply to this diff. All changed files are within `scope`.
2026-10-26 22:45 omi-agent-security-reviewer (codex):
> VERDICT: FAIL
> - src/omi/__init__.py:754 High: `omi init` follows a manifest symlink and overwrites its target | why: a repository can redirect `.omi/manifest.json` to an existing JSON object outside the project | verified: traced `init:774` → `read_manifest:748` → `write_manifest:787`, with no destination guard -> validate manifest and parent paths before reading or writing.
> UNVERIFIED: none; `python3 tests/test_omi.py` passed.
2026-10-26 22:53 omi-agent-engineer (claude):
> DONE
> - Files changed: `src/omi/__init__.py`, `tests/test_omi.py`, `.omi/tasks/TASK-079.md` (checkpoint).
> - `init` now runs `.omi/manifest.json` and `.omi/version` through `upgrade_write_safe`, the same guard `upgrade_apply` uses. A symlinked destination is skipped with `skip (symlink): <path>`, and its target is left unchanged.
> - New test `test_init_symlink_manifest` covers a manifest symlink and a version symlink. It skips if `os.symlink` raises OSError.
> - Suggested commit: `fix: guard manifest and version writes in omi init against symlinks`
> - Tests: `python3 tests/test_omi.py` passed on Linux (`ok`). The Windows rerun is still open (Coordinator).
2026-10-26 22:54 hook post-run passed:
> Conflict. The container name "/tmpe6smuyz8-TASK-001-engineer-codex-gpt-x-medium-155323" is already in useBind for 0.0.0.0:8080 failed: port is already in usewrote /tmp/tmpdone28iw/.omi/skills/CATALOG.md (2 skills)
> create AGENTS.md
> create docker/Dockerfile
> create docker/prove.sh
> create docker/proxy.py
> create .claude/settings.json
> create .claude/skills/omi-idea/SKILL.md
> create .claude/skills/omi-release/SKILL.md
> create .claude/skills/omi-status/SKILL.md
> create .claude/skills/omi-task/SKILL.md
> create .claude/skills/omi-upgrade/SKILL.md
> create .omi/agents/omi-agent-architect.md
> create .omi/agents/omi-agent-designer-ui.md
> create .omi/agents/omi-agent-devops.md
> create .omi/agents/omi-agent-docs-writer.md
> create .omi/agents/omi-agent-engineer.md
> create .omi/agents/omi-agent-qa-tester.md
> create .omi/agents/omi-agent-researcher.md
> create .omi/agents/omi-agent-reviewer.md
> create .omi/agents/omi-agent-security-reviewer.md
> create .omi/config.json
> create .omi/decisions.md
> create .omi/hooks/post-run.sh
> create .omi/plans/PLAN-000.md
> create .omi/references/nextjs-app-router.md
> create .omi/references/postgres-conventions.md
> create .omi/rules/docker.md
> create .omi/rules/go.md
> create .omi/rules/nextjs.md
> create .omi/rules/postgres.md
> create .omi/rules/python.md
> create .omi/skills/.gitkeep
> create .omi/skills/data/omi-skill-data-review/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-docker-worker-pitfalls/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-incident/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-release-checklist/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-rollback/SKILL.md
> create .omi/skills/delivery-ops/omi-skill-windows-powershell/SKILL.md
> create .omi/skills/qa-web/omi-skill-web-qa/SKILL.md
> create .omi/skills/quality/omi-skill-ci-workflow-audit/SKILL.md
> create .omi/skills/quality/omi-skill-debug-root-cause/SKILL.md
> create .omi/skills/quality/omi-skill-diff-security-review/SKILL.md
> create .omi/skills/quality/omi-skill-simplify-review/SKILL.md
> [... truncated ...]
> ok

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-architect | claude-opus-5-5 | high | 12 | 4515 | 152074 | 53s | - | n/a |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 18 | 11516 | 297805 | 180s | 2/2 omi-skill-windows-powershell omi-skill-lean-implementation | - |
| omi-agent-reviewer | gpt-6.1-sol (codex) | medium | 208445 | 1944 | 171904 | 117s | - | FAIL b8079e3 |
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 327207 | 2666 | 291456 | 138s | 2/2 omi-skill-windows-powershell omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 4 | 3382 | 63463 | 84s | - | FAIL 2a0e3cb |
| omi-agent-engineer | claude-opus-5-5 | high | 34 | 11265 | 649712 | 239s | 2/2 omi-skill-windows-powershell omi-skill-lean-implementation | - |
| omi-agent-reviewer | gpt-6.1-sol (codex) | medium | 229107 | 1739 | 186752 | 99s | - | FAIL c968083 |
| omi-agent-engineer | gpt-6.1-sol (codex) | high | 640327 | 6845 | 590080 | 263s | 2/2 omi-skill-windows-powershell omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 4769 | 136777 | 106s | - | PASS 7f0f612 |
| omi-agent-security-reviewer | gpt-6.1-sol (codex) | medium | 356553 | 1887 | 287488 | 104s | 2/2 omi-skill-diff-security-review omi-skill-ci-workflow-audit | FAIL 47df69f |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 12 | 2112 | 197291 | 93s | 1/2 omi-skill-lean-implementation | - |
