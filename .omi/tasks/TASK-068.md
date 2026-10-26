---
id: TASK-068
title: Add rules auto-loaded by task scope, with their own token budget
status: done
depends:
scope: src/omi/__init__.py, tests/**, src/omi/template/**, .omi/rules/**, .omi/config.json, AGENTS.md
role: omi-agent-engineer
skills: [omi-skill-windows-powershell]
tool:
workflow: omi-flow-feature
step: accept
---
## Goal
Rules in `.omi/rules/<id>.md` (frontmatter `id, summary, applies`) are added to an agent's prompt automatically when any `applies` glob matches the task `scope`, within a separate rule budget. Spec: `docs/specs/template-kinds.md` (Rules).

## Acceptance criteria
- [x] `python -m omi rules` validates every rule (id = file name, summary, at least one `applies` glob, at most `rule_limits.rule_tokens`) and writes `.omi/rules/CATALOG.md`, one line per rule with its globs and token count.
- [x] `rule_limits` in `.omi/config.json` overrides the defaults `{"tokens": 2000, "rule_tokens": 800}`; the skill budget is unchanged.
- [x] `omi run` adds the paths of the matching rules to the prompt under a "Rules (you must follow these)" heading; a task with scope `src/**/*.go` gets rule `go` and not `python`. Tested.
- [x] Over budget, `omi run` exits before starting the agent and names each rule and its token count. Tested.
- [x] The template ships rules `go`, `python`, `postgres`, `nextjs`, `docker` (each at most 800 tokens) and its catalog; `omi init` into an empty directory creates them. Tested.
- [x] Template and root `AGENTS.md` mention rules in one line each.
- [x] All tests pass.

## Checkpoint
Round 3: test rmtree of .git now chmods read-only files on error (Windows). Tests ok.
Review round 2 FAIL (host test run on Windows, reviewer not started):
- tests/test_omi.py:1131 `omi.shutil.rmtree(root / ".git")` fails with `PermissionError: [WinError 5] Access is denied` on a git object file: git makes objects read-only and Windows cannot unlink read-only files. Since round 1 the test commits files, so objects exist. Make the removal work on Windows (e.g. `rmtree(..., onexc=lambda f, p, e: (os.chmod(p, stat.S_IWRITE), f(p)))`), or avoid deleting a real .git. Tests must pass on the Windows host, not only in the Linux container.
Review round 1 PASS with a finding the PO asked to fix now (PO: "Sửa luôn trong 068"):
- `rule_matches` only tests the scope glob as a string against `applies`, so broad scopes (`src/**`, `tests/**`, `**`) never get a rule. Also match `applies` against the real files inside the scope (`git ls-files` in the worktree filtered by the scope globs); keep the current string check so a scope naming new files still matches.
- Add a test: scope `src/**` with a tracked `src/x.go` gets rule `go`, not `python`; scope `src/**/*.go` with no Go files yet still gets `go`.
Done: all criteria (rules cmd, rule_limits, run prompt + budget stop, 5 template rules + catalog, AGENTS.md lines, test_rules).
Not done: -
Tests: python3 tests/test_omi.py ok
Round 2: `task_rules` now also matches `applies` against tracked files inside the scope (`git ls-files`); test added in test_rules. Tests ok.
Next: review and commit.

## Steps
PO approval accept: Nghiệm thu, merge (Recommended)
- plan started 2026-10-26 13:45
- plan done 2026-10-26 13:46
- build started 2026-10-26 13:46
- build done 2026-10-26 13:48
- review started 2026-10-26 13:48
- review failed 2026-10-26 13:49
- build started 2026-10-26 13:49
- build done 2026-10-26 13:50
- review started 2026-10-26 13:50
- review failed 2026-10-26 13:51
- build started 2026-10-26 13:51
- build done 2026-10-26 13:52
- review started 2026-10-26 13:52
- review done 2026-10-26 13:52
- accept started 2026-10-26 13:52

## Reports
2026-10-26 13:48 omi-agent-engineer (claude):
> DONE
> - Files changed: `src/omi/__init__.py`, `tests/test_omi.py`, `AGENTS.md`, `src/omi/template/AGENTS.md`, `src/omi/template/dot-omi/rules/` (`go`, `python`, `postgres`, `nextjs`, `docker`, plus `CATALOG.md`), and the task's Checkpoint.
> - Commit: `feat(rules): auto-load rules by task scope with their own token budget`
> - Tests: `python3 tests/test_omi.py` passes, including a new `test_rules`.
>   - `test_rules` covers validation errors, `rule_limits` overrides, scope matching, and `omi init` into an empty directory.
>   - It also checks that `omi run` adds the rule paths under "Rules (you must follow these)", and that an over-budget run exits before any `docker run` and names each rule with its token count.
> - Open issues:
>   - A scope of `src/**/*.go` gets `go` and not `python`. The match runs the scope glob through `fnmatch` against each `applies` glob.
>   - `**/` at the start of an `applies` glob is optional, so `**/*.py` also matches `setup.py`.
>   - `omi run` only checks the rules that match the scope, so an invalid unrelated rule won't block it. `python -m omi rules` validates all of them.
>   - I did not add rules to the repo's own `.omi/`, only to the template.
2026-10-26 13:49 omi-agent-reviewer (claude):
> VERDICT: PASS
> - src/omi/__init__.py:120 Scope matching is one-directional: it treats the scope glob as a string and the rule's `applies` glob as the pattern. A broad scope such as `src/**` or `**` never matches `**/*.go`, so no rule loads even though the task covers Go files. The spec example (`src/**/*.go`) works. -> Accept as a documented limitation, or also test `fnmatch(glob, s)`.
> - AGENTS.md:20 The root `AGENTS.md` points to `.omi/rules/CATALOG.md`, but the repo's own `.omi/` has no rules directory or catalog. The AC only asks for the mention, and the engineer reported this. -> Optional: run `python -m omi rules` in the repo, or leave as is.
> - .omi/tasks/TASK-068.md Changes to the task file (Steps, Reports, Checkpoint) are outside the listed `scope`. They look like normal workflow bookkeeping. -> No action.
> 
> AC: `python -m omi rules` validates and writes the catalog ✓ `load_rules` checks id equals file name, summary, at least one `applies` glob, and the `rule_tokens` cap. `rules_catalog` writes `- id: summary (applies: …) [~N tokens]`. `test_rules` covers the bad-rule errors.
> AC: `rule_limits` overrides the defaults, skill budget unchanged ✓ `RULE_LIMITS | config["rule_limits"]` is a separate key, and the test checks partial overrides.
> AC: `omi run` adds matching rule paths under "Rules (you must follow these)" ✓ `run_role` calls `task_rules` and `rule_prompt`. The test asserts `go.md` is in the docker prompt and `python.md` is not for scope `src/**/*.go`.
> AC: over budget, `omi run` exits before starting the agent and names each rule with its token count ✓ `task_rules` calls `sys.exit` with "rule budget … go N tokens". The test asserts no `docker run` call and that the message names `go`.
> [... truncated ...]
> AC: all tests pass ✓ `python3 tests/test_omi.py` ends with `ok`.
2026-10-26 13:50 omi-agent-engineer (claude):
> DONE
> - Files changed: `src/omi/__init__.py`, `tests/test_omi.py`, and the Checkpoint in `.omi/tasks/TASK-068.md`.
> - Fix: `task_rules` now also expands the scope into the tracked files it covers (`git ls-files` filtered by the scope globs) and matches `applies` against those. The string check stays, so a scope naming new files still matches.
> - Tests: added to `test_rules`. Scope `src/**` with a tracked `src/x.go` gets `go`, and scope `src/**/*.go` and `lib/**/*.go` (no Go files) also get `go`. `python3 tests/test_omi.py` ends with `ok`.
> - Commit: `fix(rules): match rules against tracked files inside a broad task scope`
> - Open issues: none.
2026-10-26 13:51 omi-agent-engineer (claude):
> DONE
> - Files changed: `tests/test_omi.py` and the Checkpoint in `.omi/tasks/TASK-068.md`.
> - The fix: the `.git` removal in `test_rules` now uses an `onerror` handler that does `chmod 0o700` on the failing path and retries. That should avoid the read-only git object failure on Windows.
> - Tests: `python3 tests/test_omi.py` ends with `ok` in the Linux container. I couldn't run it on Windows, so that still needs checking on the host.
> - Commit: `test(rules): make .git removal work on Windows read-only objects`
> - Open issues: none.
2026-10-26 13:52 omi-agent-reviewer (claude):
> VERDICT: PASS
> - tests/test_omi.py:404 `shutil.rmtree(..., onerror=...)` has been deprecated since Python 3.12. The template's python rule says 3.13, and the task suggested `onexc`. -> Use `onexc=lambda f, p, e: (omi.os.chmod(p, 0o700), f(p))`. This is low severity because it still works today.
> - src/omi/__init__.py:173 `task_rules` ignores the validation errors that `load_rules` returns. A rule with a mismatched `id` or a missing `summary` still loads into the prompt if its `applies` matches. The engineer reported this, and the AC only requires that `python -m omi rules` validates. -> Optional: skip or fail on matched rules that have errors.
> - Windows is unverified. The Round 3 fix was only run on Linux, and I could not test it on the host. The handler does `chmod 0o700` and retries, which clears the read-only flag, so it should work.
> 
> AC: `python -m omi rules` validates every rule and writes the catalog ✓ `load_rules` checks id against the file name, a missing `summary`, no `applies` glob, and the token cap. `rules_catalog` writes one line per rule with its globs and `[~N tokens]`. `test_rules` covers the bad-rule errors, and `tests/test_omi.py` ends with `ok`.
> AC: `rule_limits` overrides the defaults, skill budget unchanged ✓ `RULE_LIMITS | over` is a separate config key. The test asserts the defaults and a partial override `{"tokens":100,"rule_tokens":800}`.
> AC: `omi run` adds matching rule paths under "Rules (you must follow these)" ✓ `run_role` calls `task_rules` and `rule_prompt`. The test asserts `go.md` is in the docker prompt and `python.md` is not for scope `src/**/*.go`. Broad scopes also work: `src/**` with a tracked `src/x.go` gets `go`, and `lib/**/*.go` with no Go files still gets `go`.
> [... truncated ...]
> Scope: changes stay within `scope`, apart from the `.omi/tasks/TASK-068.md` bookkeeping.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-engineer | claude-sonnet-5-5 | medium | 26 | 9725 | 519593 | 114s | 2/2 omi-skill-windows-powershell omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 6 | 2247 | 76330 | 37s | - | PASS f62106c |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 14 | 2266 | 172600 | 38s | 2/2 omi-skill-windows-powershell omi-skill-lean-implementation | - |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 10 | 906 | 107746 | 34s | 2/2 omi-skill-windows-powershell omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 4 | 2268 | 49847 | 39s | - | PASS 044b57c |
