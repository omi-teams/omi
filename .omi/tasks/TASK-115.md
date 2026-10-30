---
id: TASK-115
title: omi board frontend
status: in-progress
depends: TASK-114
plan: PLAN-006
scope: src/omi/board/web/**, src/omi/board/data.py, tests/test_board.py, pyproject.toml, tests/test_board_web.py, tests/test_omi.py, .omi/tasks/TASK-115.md, .omi/tasks/TASK-115-mockup/**
role: omi-agent-engineer
skills: [omi-skill-ui-direction]
refs: []
tool: claude
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature-ui
step: review
---
## Goal
Plain HTML/CSS/JS pages for home, project dashboard and task detail, in Vietnamese, calling the JSON API.

## Acceptance criteria
- [ ] Home, dashboard (PO-waiting, plans, kanban, activity, decisions, usage, sync) and task detail render from the API; auto-refresh every 30 s with a toggle.
- [ ] State text is inserted with `textContent` only, never `innerHTML`; no external script, font or CDN.
- [ ] `pip install .` ships `board/web/*` (package data); a test checks the files are in the installed package.
- [ ] Pages match the PO-approved mockup in `.omi/tasks/TASK-115-mockup/` (Main = dashboard, Home, Task, Phone = 390 px dashboard): same layout, sections, header controls, cards, chips, progress bars, kanban columns, workflow stepper and colours.
- [ ] The header stays pinned at the top while scrolling (sticky), with `scroll-padding-top` so focused or anchored elements are never hidden under it.
- [ ] Next to the auto-refresh toggle a countdown shows the seconds to the next refresh ("Làm mới sau 25 giây"), resets after every refresh (auto or manual), shows "Đã tắt" when the toggle is off and "Tạm dừng" while the tab is hidden; it updates once per second without re-rendering the view and is not announced every second (outside any live region, e.g. aria-hidden, with the toggle label still saying 30 giây).
- [ ] Readable at 360 px width and keyboard navigable; all tests pass.

## Checkpoint
Review round 4 FAIL (codex quota -> claude-opus-5-5/medium): countdown ✓. PO 2026-10-30 approved one small fix round with claude sonnet/medium.
- Fix only: src/omi/board/web/app.js route() clears the timer before fetch and fetch has no timeout; a hung request freezes the countdown at "0 giây" and stops auto-refresh. Abort the fetch after 10 s (AbortController) so the catch shows the existing error/retry UI and finally -> schedule() always runs. Add a Node test with a never-resolving fetch.
- Host: `python tests/test_board_web.py` -> ok, wheel test ran (no skip line); only the Playwright browser test skipped (qa step).

### Fetch timeout fix (2026-10-30)
Done: route() aborts the fetch after 10 s (AbortController), the catch shows the error/retry UI ("quá thời gian chờ"), finally clears the timeout and schedule() runs. Node test with a never-resolving fetch added. Tests: test_board_web.py exit 0; wheel and Playwright tests skipped (pip/Playwright missing). Full `python3 tests/test_omi.py` exit 0, printed ok. Next: review, then qa.

Review round 5 (claude sonnet/medium): no code defect; FAIL only on environment-skipped checks. PO 2026-10-30: treat review as passed on code, browser QA by the Coordinator in real Chrome (Claude in Chrome) at 360/390/768/1280 px vs the mockups.
Host: `python tests/test_board_web.py` -> ok, test_wheel_ships_web ran (no skip line); only the Playwright browser test skipped.

### Countdown build (2026-10-30)
Done: implemented only the round-3 countdown gap. The header groups the toggle and countdown, with a compact stacked arrangement on phones. The countdown uses textContent, is aria-hidden and outside live regions, and keeps the toggle's “30 giây” label. One-second ticks use a timestamp deadline without re-rendering the view or changing focus/status. Completed manual, automatic, retry and route refreshes restart the 30-second deadline, including unchanged responses and failures. Polling pauses during an active request and while hidden; off shows “Đã tắt”, hidden shows “Tạm dừng”, and returning to a visible tab refreshes when enabled.
Not done: real-browser layout/keyboard checks and a new installed-package check cannot run here (Playwright and pip missing). Existing host wheel/install evidence and the qa handoff remain applicable; no additional scope is needed.
Tests: `python3 tests/test_board_web.py` exited 0: static safety/package configuration/mockup structure and Node DOM tests ran, including countdown ticks, no view/live-status updates, focus preservation, manual/auto reset, disabled/manual behavior, hidden/resume, slow responses and delayed ticks. Wheel/install explicitly skipped (pip missing); browser explicitly skipped (Playwright missing). Browser coverage also checks countdown placement/visibility at 360/390/768/1280 px, live-region exclusion and keyboard toggle state. `node --check src/omi/board/web/app.js` exited 0 (syntax only). Full `python3 tests/test_omi.py` exited 0 and printed `ok`, including board API/static/Node countdown tests; wheel/install and browser checks explicitly skipped for missing pip and Playwright. The full run used temporary fixtures within the allowed mockup directory and removed them on completion.
Next: Coordinator review of the countdown-only diff; browser visual/keyboard verification remains in qa (TASK-128). No commit was made.

### Previous build and review context
Done: addressed the round-2 frontend gaps within scope. Task detail and dashboard task records now expose workflow_steps from the project workflow file (with path validation) plus current_step; the task page renders the definition's steps, PO gates and “Bước N/M” (six steps in the regression fixture). Home and dashboard show API-provided project path, branch and sync chips. Kanban shows two cards per column with a native keyboard-operable “+ N task khác” disclosure for the rest. Below 768 px, usage becomes a one-line total and empty Review/Blocked columns merge into one row; populated columns remain separate. The header is sticky, phone breadcrumbs stay on one compact line, the skip link stays reachable while scrolled, and root scroll-padding-top clears the header.
Data semantics: path is the actual detached project directory; branch and sync describe its state repository. The portable project registry stores only remote identities, so no local code checkout path or code branch is invented. UI tooltips identify the state directory and branch. Workflow files retain the state path/symlink boundary checks; missing definitions remain an explicit empty list with a current-step fallback.
Not done: real-browser visual/keyboard verification and installed-package verification cannot execute in this worker because Playwright and pip are absent. The review records a prior host wheel/install pass; this run does not claim a new installed-package verification.
Tests: `python3 tests/test_board.py` exited 0 (API metadata, workflow definitions/defaults/refresh, read-only behavior and path refusal). `python3 tests/test_board_web.py` exited 0 (static safety/package-data/layout checks and Node DOM behavior tests); wheel/install explicitly skipped: pip missing; browser explicitly skipped: Playwright missing. Browser tests retained and extended for 360/390/768/1280 px, sticky-header/anchor clearance, compact phone header, merged empty columns, usage summary and keyboard overflow disclosure. `node --check src/omi/board/web/app.js` exited 0 (syntax only). `python3 tests/test_omi.py` exited 0 and printed `ok`, including the board API/static/Node tests; wheel/install and browser tests explicitly skipped for missing pip and Playwright.
Next: RESUME (session stopped by PO 2026-10-30 after build round 3). Build round 3 (codex gpt-6-astra/high) committed. Host: `python tests/test_board.py` and `python tests/test_board_web.py` -> pass, wheel test ran (no skip). Playwright missing on host and worker. Resume: `python -m omi step TASK-115 next` (review), run a fresh `omi-agent-reviewer`; on FAIL (would be the 3rd) ask the PO before another build (workflow rule: rescope, change approach or drop). On PASS: qa step (omi-agent-qa-tester, browser screenshots vs `.omi/tasks/TASK-115-mockup/`), then PO accept, PR, CI, merge.

Review round 3 FAIL (codex gpt-6-astra/high): only the countdown criterion is missing (added by the PO after build 3, expected).
- Fix: src/omi/board/web/app.js has no countdown; add it next to the auto-refresh toggle per the countdown criterion (1 s ticks without re-render, reset after auto and manual refresh, "Đã tắt" when off, "Tạm dừng" when hidden, aria-hidden, toggle label keeps 30 giây). Add Node DOM tests for tick, reset, off and hidden.
- Not code gaps: wheel/install is covered by the host run (pip absent in worker); browser checks belong to the qa step (Playwright absent, TASK-128). Do nothing else in this round.

### Approved direction
PO 2026-10-30 approved `.omi/tasks/TASK-115-mockup/*.dc.html` and defaults: header "omi board", teal #0f6e6e, dark mode via prefers-color-scheme, Vietnamese date/number format, evergreen browsers.
The implementation copies/merges mockup CSS and DOM structure, keeps class names, moves inline styles into CSS classes for CSP, uses system fonts, and leaves design files/API unchanged. Stats use task_counts/po_waiting_count; plans use progress bars; kanban cards use IDs/titles/chips; criteria use a checklist; reports use details. Workflow steps may only come from an API definition; absent that list, show the current step chip.

Review round 2 FAIL:
- Host: `python tests/test_board_web.py` on the host (pip present) -> wheel test passed, no skip line. Playwright is missing on host and worker: 360/390 px and keyboard are left to the qa step; keep the Playwright test as skip-if-missing.
- PO 2026-10-30 approved widening scope to `src/omi/board/data.py` and `tests/test_board.py` (read-only API, still no writes): add the task's workflow step list and current step to the task detail (render the 6-step stepper "Bước N/M" as in the mockup), and the project path, branch and sync summary to `projects()` (Home cards) and the dashboard heading. Update `tests/test_board.py`.
- Frontend gaps vs mockup: kanban "+ N task khác" overflow link when a column has more cards than shown; phone width (<768 px) shows the usage one-line summary instead of the table, and merges the empty Review and Blocked columns into one row as in Phone.dc.html.
- PO 2026-10-30: header must stay pinned while scrolling (new criterion); on phones the header stays compact.
- Model raised to opus alias (gpt-6-astra/high) after two review FAILs, PO approved.

PO 2026-10-30 (after round 3, while viewing the board): add a countdown next to the auto-refresh toggle (new criterion above). Do it in the next build round; if review round 3 PASSes otherwise, run one small build round for it before qa.
QUOTA: codex hit its usage limit; omi-agent-reviewer continued with claude on the partial diff.

## Steps
- plan started 2026-10-30 14:35
- plan done 2026-10-30 14:35
- design started 2026-10-30 14:35
- design done 2026-10-30 14:39
- build started 2026-10-30 14:39
- build done 2026-10-30 15:02
- review started 2026-10-30 15:02
- review failed 2026-10-30 15:11
- build started 2026-10-30 15:11
- build done 2026-10-30 15:29
- review started 2026-10-30 15:29
- review failed 2026-10-30 15:44
- build started 2026-10-30 15:44
- build done 2026-10-30 15:57
- review started 2026-10-30 18:20
- review failed 2026-10-30 18:27
- build started 2026-10-30 18:27
- build done 2026-10-30 18:51
- review started 2026-10-30 18:51
- review failed 2026-10-30 19:02
- build started 2026-10-30 19:02
- build done 2026-10-30 19:13
- review started 2026-10-30 19:13

## Reports
2026-10-30 14:38 omi-agent-designer-ui (claude):
> MODE: SPEC
> - Routing, `web/index.html` + `app.css` + `app.js`: the server serves only real files and `/` maps to `index.html`, so there are no SPA paths. Use hash routes `#/`, `#/p/<name>`, `#/p/<name>/t/<id>` in one page, with one `h1` that changes per route, `document.title` per route, and focus moved to the `h1` after each route change. Everything is same-origin because of the CSP `default-src 'self'`. That means no inline `<script>`, `<style>` or `style=""`, and no web fonts. Use the system font stack with `font-variant-numeric: tabular-nums`. Build all state text with `textContent` and `createElement`; build URLs with `encodeURIComponent`.
> - Layout and tokens (360 px first, one column; at 768 px and wider the kanban becomes a 5-column grid; max-width 1200 px; spacing 4/8/16/24): `<html lang="vi">`, a skip link, `header` with `nav` (Trang chủ / breadcrumb), `main`, and the refresh toggle in the header. Dashboard order is Chờ PO (first, accent border), Kế hoạch (done/total as text plus `<progress>`), Kanban (heading with count per column; cards are links to the task), Hoạt động, Quyết định, Sử dụng (a real `<table>` in a scroll wrapper with a `tabindex=0` caption), Đồng bộ (ahead/behind/dirty as text). Light and dark via `prefers-color-scheme`. Tinted gray family, one accent (a muted teal, for example `#0f6e6e` on `#fafaf9`, with no pure black). Radius 8 px outer, 4 px inner. Status uses text plus a glyph, not color alone.
> [... truncated ...]
> OPEN: (1) Brand, accent color and a logo or name for the header: use "omi board" and the teal above unless the PO says otherwise. (2) Dark mode: confirm it is wanted. (3) Date and number format in Vietnamese (dd/MM/yyyy and `.` thousands separators) or raw ISO values as the API gives them? (4) Target browsers: assume evergreen desktop and mobile with no IE or old Safari.
2026-10-30 14:44 omi-agent-engineer (claude):
> NEEDS SCOPE: `tests/test_omi.py` — it must import and call `test_board_web.main()`, or the runner never runs the new test.
> 
> - **Files changed:** `src/omi/board/web/{index.html,app.css,app.js}`, `pyproject.toml` (package-data `board/web/*`), `tests/test_board_web.py` (new), `.omi/tasks/TASK-115.md`.
> - **Suggested commit:** `feat(board): plain HTML/CSS/JS frontend in Vietnamese with package data`
> - **Tests that ran:**
>   - `python3 tests/test_board_web.py` passes. It checks that `app.js` has no `innerHTML`, `outerHTML`, `eval` and similar, that no file uses an external URL, `@import` or `@font-face`, and that `index.html` has no inline script or style.
>   - It also checks `lang="vi"`, the viewport tag, the 768 px breakpoint, and that the `pyproject` package-data globs cover all three web files.
> - **Not confirmed:**
>   - The full `python3 tests/test_omi.py` aborted in the sandbox on a docker container-name/port-8080 conflict, so I can't say the whole suite passes.
>   - The package-data test doesn't build or install anything. `pip` and `setuptools` aren't available here, so I didn't verify the criterion that `pip install .` ships the files.
>   - I didn't open the pages in a browser, so the 30 s auto-refresh toggle, the 360 px layout and keyboard navigation are unchecked.
> - **Skipped:** no framework or dependency was added, and `board/server.py` is untouched.
2026-10-30 14:49 hook post-run passed:
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
> create .omi/skills/quality/omi-skill-verify-evidence/SKILL.md
> create .omi/skills/ui/omi-skill-ui-a11y-review/SKILL.md
> create .omi/skills/ui/omi-skill-ui-direction/SKILL.md
> create .omi/skills/ui/omi-skill-ui-direction/references/style-presets.md
> [... truncated ...]
> ok
2026-10-30 14:55 omi-agent-engineer (claude):
> The full suite passed: `python3 tests/test_omi.py` exited 0 and printed `ok`. I wrote "not run" in my last report, which was wrong. The task file's Round 2 note says the same thing, and the Coordinator should correct it.
> 
> The wheel test was skipped because pip is missing here, so the check that the web files ship in the installed package did not run. I also haven't checked the page in a browser.
2026-10-30 14:59 hook post-run passed:
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
> create .omi/skills/quality/omi-skill-verify-evidence/SKILL.md
> create .omi/skills/ui/omi-skill-ui-a11y-review/SKILL.md
> create .omi/skills/ui/omi-skill-ui-direction/SKILL.md
> create .omi/skills/ui/omi-skill-ui-direction/references/style-presets.md
> [... truncated ...]
> ok
2026-10-30 15:10 omi-agent-reviewer (claude):
> VERDICT: FAIL
> - src/omi/board/web/app.js:370 After a failed poll, a later successful poll with unchanged JSON returns early and never clears the error. The old text is still in `seen[path]`, so `get()` throws UNCHANGED and the handler returns before `err.replaceChildren()`. The "Không tải được dữ liệu" message and the "Thử lại" button stay on screen after the server recovers. -> Clear `err` in the UNCHANGED branch, or delete `seen[path]` when a fetch fails.
> - src/omi/board/web/app.js:290 `seen[path]` is set before the view renders. If a render function throws, for example on a missing field, every later poll and "Thử lại" click gets UNCHANGED and returns silently, so the page stays broken with no error. -> Set `seen[path]` only after the render succeeds, or clear it in the catch block.
> - tests/test_board_web.py:473 The wheel test prints "skip: pip missing" here, so nothing was built and criterion 3 was never checked against a real package. -> Run it where pip is available. This is UNVERIFIED, not ✓.
> - The page was not opened in a browser, so the 360 px layout, keyboard navigation and the 30 s auto-refresh are unchecked. The task file also still says "Full test_omi.py not run", which is wrong because the engineer's later report says it passed.
> 
> AC: Home, dashboard (PO-waiting, plans, kanban, activity, decisions, usage, sync) and task detail render from the API; auto-refresh every 30 s with a toggle. ✗ UNVERIFIED in a browser. The JSON field names in `app.js` match `data.py`, and the 30 s `setInterval`, the toggle and the pause-when-hidden logic are in the code. The stale-error bug above means the recovery path is not correct.
> [... truncated ...]
> AC: Readable at 360 px width and keyboard navigable; all tests pass. UNVERIFIED for 360 px and keyboard use, since it was not opened in a browser. The CSS is one column below 768 px, and the page has a skip link and focus styles. `python3 tests/test_omi.py` exited 0 and printed `ok`.
2026-10-30 15:22 omi-agent-engineer (codex):
> BLOCKED — implementation complete; host verification pending.
> Files: `src/omi/board/web/{index.html,app.css,app.js,favicon.svg}`, `tests/test_board_web.py`, task checkpoint.
> Suggested commit: `feat(board): reproduce approved dashboard mockups`
> Tests: full `test_omi.py` and board static/DOM tests exited 0.
> Skipped: wheel/install check (pip missing); browser checks (Playwright missing).
> Open: verify mockup fidelity, mobile layout, keyboard navigation, and installed assets on host.
2026-10-30 15:26 hook post-run passed:
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
> create .omi/skills/quality/omi-skill-verify-evidence/SKILL.md
> create .omi/skills/ui/omi-skill-ui-a11y-review/SKILL.md
> create .omi/skills/ui/omi-skill-ui-direction/SKILL.md
> create .omi/skills/ui/omi-skill-ui-direction/references/style-presets.md
> [... truncated ...]
> ok
2026-10-30 15:39 omi-agent-reviewer (claude):
> VERDICT: FAIL
> - `tests/test_board_web.py:1318` The wheel test prints "skip: pip missing" here, so nothing was built or installed. Package-data criterion is not proven. -> Run it on a host with pip.
> - `src/omi/board/web/app.js:1135` The API has no `workflow_steps` field (`data.py` `_detail` doesn't return it), so the task page always shows a single step chip. The mockup shows a 6-step stepper with "Bước 4/6". -> Have the API supply the workflow definition, or get the PO to accept the chip.
> - `src/omi/board/web/app.js:1075` Home project cards omit the project path, the branch chip and the sync chip that the mockup shows. The `projects()` API doesn't return them. The dashboard heading also omits the path and the branch chip. -> Extend the API, or get the PO to accept the omissions.
> - `src/omi/board/web/app.js:1104` Kanban columns omit the "+ N task khác" overflow link from the mockup. The Phone mockup shows only a "9 lượt · 25.542 output" summary for usage, and the implementation renders the full table instead. The Phone Review and Blocked columns are not merged. -> Align with the mockup, or record the PO's acceptance.
> - `tests/test_board_web.py:1517` The Playwright browser test did not run here, so the 360/390/1280 px layout, dark mode and keyboard checks are unexecuted. The Node DOM test uses a hand-written fake DOM, so it says nothing about CSS or real focus behaviour. -> Run it on a host with Playwright.
> 
> AC: Home, dashboard (PO-waiting, plans, kanban, activity, decisions, usage, sync) and task detail render from the API; 30 s auto-refresh with a toggle ✓ in code and in the Node fake-DOM test (30000 ms interval, toggle, hidden pause, recovery). Field names match `data.py`. Not seen in a real browser.
> [... truncated ...]
> AC: Readable at 360 px and keyboard navigable; all tests pass: tests pass ✓ (`python3 tests/test_omi.py` exit 0, "ok"). The 360 px and keyboard parts are UNVERIFIED (Playwright skipped). The code has a skip link, focus styles and `max-width:767px` rules.
2026-10-30 15:52 omi-agent-engineer (codex):
> DONE — implemented round-2 changes and updated checkpoint.
> Files: `src/omi/board/{data.py,web/app.js,web/app.css}`, `tests/{test_board.py,test_board_web.py}`, `.omi/tasks/TASK-115.md`.
> Suggested commit: `feat(board): add workflow metadata and responsive dashboard controls`
> Tests: board API, frontend static/DOM, and full `python3 tests/test_omi.py` passed.
> Skipped: wheel/install (pip missing); browser checks (Playwright missing).
> Open: QA visual/keyboard verification; displayed path and branch describe detached state.
2026-10-30 15:56 hook post-run passed:
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
> create .omi/skills/quality/omi-skill-verify-evidence/SKILL.md
> create .omi/skills/ui/omi-skill-ui-a11y-review/SKILL.md
> create .omi/skills/ui/omi-skill-ui-direction/SKILL.md
> create .omi/skills/ui/omi-skill-ui-direction/references/style-presets.md
> [... truncated ...]
> ok
2026-10-30 18:27 omi-agent-reviewer (codex):
> VERDICT: FAIL
> 
> - src/omi/board/web/app.js:223 Countdown is absent; the timer only polls every 30 seconds and does not reset after manual refresh. -> Add the adjacent countdown, one-second updates, refresh resets, off/hidden states, and exclusion from live announcements.
> - tests/test_board_web.py:40 Installed-package verification skipped because pip is missing. -> Run the wheel/install test with pip available.
> - tests/test_board_web.py:265 Browser verification skipped because Playwright is missing. -> Run browser checks and compare rendered pages against all four approved mockups.
> 
> AC: API-rendered home, dashboard sections and task detail; 30-second refresh toggle UNVERIFIED Node behavior tests passed; browser rendering checks skipped. Real TASK-115 and its six-step workflow parsed correctly.
> AC: State uses textContent only; no external scripts, fonts or CDN ✓ Source inspection and static safety tests passed.
> AC: pip install ships board/web/*, verified in installed package UNVERIFIED Package-data configuration passed; wheel/install test skipped.
> AC: Pages match approved Main, Home, Task and Phone mockups UNVERIFIED Static structure checks passed; rendered visual comparison not executed.
> AC: Sticky header and scroll-padding prevent obscured focus/anchors UNVERIFIED CSS declarations exist; browser clearance checks skipped.
> AC: Accessible countdown with refresh resets and off/hidden states ✗ No countdown element or update logic exists.
> AC: Readable at 360 px, keyboard navigable; all tests pass UNVERIFIED `python3 tests/test_omi.py` exited 0 and printed `ok`; package-install and browser tests skipped.
2026-10-30 18:46 omi-agent-engineer (codex):
> DONE — implemented countdown, regression tests, and checkpoint update.
> Files: `src/omi/board/web/{app.js,app.css,index.html}`, `tests/test_board_web.py`, `.omi/tasks/TASK-115.md`.
> Suggested commit: `feat(board): add auto-refresh countdown`
> Tests: frontend static/Node tests and full `python3 tests/test_omi.py` exited 0.
> Skipped: wheel/install (pip missing); browser checks (Playwright missing).
> Open: browser QA remains pending. No commit made.
2026-10-30 19:00 omi-agent-reviewer (claude):
> ```
> VERDICT: FAIL
> - src/omi/board/web/app.js:194,205 route() clears the refresh timer before fetch, and fetch has no timeout or abort. If one request hangs (server stalls, network drops), schedule() never runs again: the countdown freezes at "Làm mới sau 0 giây" and auto-refresh stops until a manual click -> abort the fetch after ~10 s with an AbortController (or reschedule in the catch on timeout) so finally → schedule() always runs
> - tests/test_board_web.py:41 test_wheel_ships_web skipped here (pip missing), so the installed-package check did not run in this review -> run `python tests/test_board_web.py` where pip is present and record the output with no skip line
> - tests/test_board_web.py:314 test_browser_layout_and_keyboard skipped (Playwright missing): 360/390 px layout, sticky header, scroll-padding and keyboard were not run in a real browser -> run it in qa (TASK-128) with Playwright installed
> AC: Home, dashboard (PO-waiting, plans, kanban, activity, decisions, usage, sync) and task detail render from the API; 30 s auto-refresh with toggle ✓ Node DOM tests in test_board_web.py passed ("ok: API views, mockup DOM, … polling"); app.js:62-187 renderers, schedule() 30000 ms, #auto toggle stored in localStorage
> AC: State text via textContent only, no innerHTML; no external script/font/CDN ✓ el() sets textContent only (app.js:21); test_files_safe passed (no innerHTML/outerHTML/eval, no external URL/@import/@font-face, no inline script/style)
> [... truncated ...]
> I found no code bug in the countdown work other than the hanging-request case above. The FAIL comes from the review rule: four criteria depend on tests that were skipped in this container. The wheel test needs pip; the mockup, sticky-header and 360 px/keyboard checks need Playwright. None of these criteria names the host, so the HOST exception doesn't apply. All changed files are within the task's scope, and I made no edits.
2026-10-30 19:08 omi-agent-engineer (claude):
> DONE: `route()` now aborts the fetch after 10 s, so a hung request can no longer freeze the countdown or stop auto-refresh.
> - **Fix:** an `AbortController` aborts the fetch after 10 s. The existing error/retry UI then shows "quá thời gian chờ". `finally` clears the timeout, and `schedule()` still runs.
> - **Files changed:** `src/omi/board/web/app.js`, `tests/test_board_web.py`, `.omi/tasks/TASK-115.md` (checkpoint).
> - **Suggested commit:** `fix(board): abort hung refresh requests after 10 s` (plus the `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` line).
> - **Tests that ran:** `python3 tests/test_board_web.py` exited 0. A new Node test uses a never-resolving fetch: it checks the 10 s abort, the error and retry text, the countdown resetting to 30 s, and recovery on the next poll. `node --check app.js` passed. `python3 tests/test_omi.py` exited 0 and printed `ok`.
> - **Skipped:** the wheel/install test (pip missing) and the Playwright browser test (Playwright missing).
> - **Open:** none. No commit was made.
2026-10-30 19:13 hook post-run passed:
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
> create .omi/skills/quality/omi-skill-verify-evidence/SKILL.md
> create .omi/skills/ui/omi-skill-ui-a11y-review/SKILL.md
> create .omi/skills/ui/omi-skill-ui-direction/SKILL.md
> create .omi/skills/ui/omi-skill-ui-direction/references/style-presets.md
> [... truncated ...]
> ok
2026-10-30 19:20 omi-agent-reviewer (claude):
> ```
> VERDICT: FAIL
> - tests/test_board_web.py:41 test_wheel_ships_web printed "skip: pip missing", so nothing was built or installed here; the installed-package criterion is UNVERIFIED -> run `python tests/test_board_web.py` where pip exists. The task checkpoint says the host run had no skip line.
> - tests/test_board_web.py:314 test_browser_layout_and_keyboard printed "skip: playwright missing", so the layout, sticky-header and keyboard criteria were not run in a browser -> run it in the qa step (TASK-128).
> - I found no code defect in the timeout fix at src/omi/board/web/app.js:200-229. The 10 s AbortController aborts the fetch and the catch shows "quá thời gian chờ" plus "Thử lại". The finally block clears the timeout and calls schedule() when the request is still current, so the countdown no longer freezes.
> ```
> The files in the diff that I read are inside the task scope. I read only the app.js fix and the test grep, not the whole diff. The diff against the base is the whole branch (2117 lines) and I viewed only its first 685 lines.
> 
> Test results:
> - `python3 tests/test_omi.py` exited 0 and printed `ok`.
> - `python3 tests/test_board_web.py` printed `ok` for the Node tests. These include the never-resolving-fetch test (`tests/test_board_web.py:247-252`), which checks the 10 s timeout, the error text and the retry button.
> 
> AC: Home, dashboard (PO-waiting, plans, kanban, activity, decisions, usage, sync) and task detail render from the API; auto-refresh every 30 s with a toggle ✓ The Node DOM tests pass; the 30000 ms polling and the toggle are in app.js:235-248.
> AC: State text via `textContent` only, no `innerHTML`; no external script, font or CDN ✓ The static safety tests pass, and `el()` sets `textContent`.
> [... truncated ...]
> AC: Readable at 360 px and keyboard navigable; all tests pass UNVERIFIED All tests pass (`test_omi.py` exit 0, `ok`). The 360 px and keyboard parts were not run because Playwright is missing.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-designer-ui | claude-sonnet-5-5 | medium | 8 | 2698 | 87795 | 30s | 2/2 omi-skill-ui-direction omi-skill-ui-a11y-review | n/a |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 26 | 8533 | 386404 | 301s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 6 | 235 | 63674 | 288s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 16 | 3095 | 294311 | 368s | - | FAIL 1ed62b0 |
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 1548711 | 20265 | 1486720 | 616s | 2/2 omi-skill-ui-direction omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 10 | 2883 | 302266 | 316s | - | FAIL 1cfb48d |
| omi-agent-engineer | gpt-6-astra (codex) | high | 1622113 | 13573 | 1555328 | 509s | 2/2 omi-skill-ui-direction omi-skill-lean-implementation | - |
| omi-agent-reviewer | gpt-6-astra (codex) | high | 1304849 | 3250 | 1224704 | 265s | - | FAIL c763d1f |
| omi-agent-engineer | gpt-6-astra (codex) | high | 2914956 | 12126 | 2848896 | 1129s | 2/2 omi-skill-ui-direction omi-skill-lean-implementation | - |
| omi-agent-reviewer | gpt-6-astra (codex) | medium | n/a | n/a | n/a | 29s | - | QUOTA->claude |
| omi-agent-reviewer | claude-opus-5-5 | medium | 20 | 3769 | 310930 | 414s | - | FAIL 8c6c0f8 |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 24 | 3976 | 487241 | 389s | 2/2 omi-skill-ui-direction omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 12 | 2169 | 326601 | 310s | - | FAIL 277c46d |
