---
id: TASK-115
title: omi board frontend
status: in-progress
depends: TASK-114
plan: PLAN-006
scope: src/omi/board/web/**, pyproject.toml, tests/test_board_web.py, tests/test_omi.py, .omi/tasks/TASK-115.md
role: omi-agent-engineer
skills: [omi-skill-ui-direction]
refs: []
tool: codex
model: sonnet
effort: medium
step_settings:
workflow: omi-flow-feature-ui
step: build
---
## Goal
Plain HTML/CSS/JS pages for home, project dashboard and task detail, in Vietnamese, calling the JSON API.

## Acceptance criteria
- [ ] Home, dashboard (PO-waiting, plans, kanban, activity, decisions, usage, sync) and task detail render from the API; auto-refresh every 30 s with a toggle.
- [ ] State text is inserted with `textContent` only, never `innerHTML`; no external script, font or CDN.
- [ ] `pip install .` ships `board/web/*` (package data); a test checks the files are in the installed package.
- [ ] Pages match the PO-approved mockup in `.omi/tasks/TASK-115-mockup/` (Main = dashboard, Home, Task, Phone = 390 px dashboard): same layout, sections, header controls, cards, chips, progress bars, kanban columns, workflow stepper and colours.
- [ ] Readable at 360 px width and keyboard navigable; all tests pass.

## Checkpoint
Done: rebuilt the Home project cards, dashboard PO panel/stat tiles/plan progress/kanban/activity/decisions/usage/sync chips, and task workflow/checklist/reports/sidebar from the approved mockup structure and CSS. Added responsive 360/390 px rules, dark palette, keyboard focus styles, local favicon, and safe text-only API rendering. Polling retains the old view on failure, clears recovered errors even for unchanged JSON, caches only successful renders, ignores stale requests, pauses while hidden, and persists the toggle defensively.
Not done: browser visual/keyboard verification and installed-package verification cannot run in this worker (no browser/Playwright or pip; registry policy blocks Playwright download). No fabricated path/branch values are shown when the API does not provide them. The current API provides no workflow definition, so task pages show the current-step chip; a supplied workflow_steps list renders the stepper.
Tests: `python3 tests/test_board_web.py` exited 0: static safety/package-data/layout checks and Node DOM behavior tests ran. Wheel build/install test explicitly skipped (pip missing); real-browser 360/390/1280 px, dark-mode, CSP and keyboard tests explicitly skipped (Playwright missing). `python3 tests/test_omi.py` exited 0 and printed `ok`, including the board DOM/safety tests (wheel skipped: pip missing). The final standalone board run also exercised the added browser-test entry point and explicitly reported its Playwright skip. `node --check src/omi/board/web/app.js` exited 0 (syntax check only).
Next: Coordinator runs the retained wheel/install test and browser test on a host with pip and Playwright/Chromium, and compares Home/Main/Task/Phone against the approved mockups.

### Approved direction
PO 2026-10-30 approved `.omi/tasks/TASK-115-mockup/*.dc.html` and defaults: header "omi board", teal #0f6e6e, dark mode via prefers-color-scheme, Vietnamese date/number format, evergreen browsers.
The implementation copies/merges mockup CSS and DOM structure, keeps class names, moves inline styles into CSS classes for CSP, uses system fonts, and leaves design files/API unchanged. Stats use task_counts/po_waiting_count; plans use progress bars; kanban cards use IDs/titles/chips; criteria use a checklist; reports use details. Workflow steps may only come from an API definition; absent that list, show the current step chip.

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

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-designer-ui | claude-sonnet-5-5 | medium | 8 | 2698 | 87795 | 30s | 2/2 omi-skill-ui-direction omi-skill-ui-a11y-review | n/a |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 26 | 8533 | 386404 | 301s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 6 | 235 | 63674 | 288s | 1/1 omi-skill-lean-implementation | - |
| omi-agent-reviewer | claude-sonnet-5-5 | medium | 16 | 3095 | 294311 | 368s | - | FAIL 1ed62b0 |
| omi-agent-engineer | gpt-6.1-sol (codex) | medium | 1548711 | 20265 | 1486720 | 616s | 2/2 omi-skill-ui-direction omi-skill-lean-implementation | - |
