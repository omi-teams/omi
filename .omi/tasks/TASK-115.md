---
id: TASK-115
title: omi board frontend
status: in-progress
depends: TASK-114
plan: PLAN-006
scope: src/omi/board/web/**, pyproject.toml, tests/test_board_web.py, .omi/tasks/TASK-115.md
role: omi-agent-engineer
skills: []
refs: []
tool: claude
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
- [ ] Readable at 360 px width and keyboard navigable; all tests pass.

## Checkpoint
Done: web/index.html, app.css, app.js; pyproject package-data `board/web/*`; tests/test_board_web.py.
Not done: tests/test_omi.py does not import test_board_web (outside scope); real `pip install .` check (no pip/setuptools here, test checks package-data globs instead).
Tests: `python3 tests/test_board_web.py` ok. `python3 tests/test_omi.py` aborted in the sandbox on a docker container name/port conflict (environment), so full suite not confirmed.
Next: (done) build per designer spec in ## Reports. PO 2026-10-30: accept designer defaults for OPEN 1-4 (header "omi board", teal #0f6e6e, dark mode via prefers-color-scheme, Vietnamese date/number format, evergreen browsers).

Coordinator check round 1 FAIL:
- tests/test_board_web.py is not run by CI: import it and call main() in tests/test_omi.py (scope widened).
- Criterion 3 wants the files checked in the installed package, not just the globs: build a wheel into a temp dir (`python -m pip wheel . --no-deps -w <tmp>`), assert omi/board/web/index.html, app.js, app.css are in it; print a skip line only if pip is missing.
- Spec gaps in app.js: (a) poll failure must keep the old view and show the error inline with a "Thử lại" button, not replace the page; (b) re-render only when the JSON changed, so a 30 s poll never destroys the focused element (keyboard criterion); (c) "Cập nhật lần cuối hh:mm:ss" in a role="status" region; (d) manual "Làm mới" button; (e) pause polling while document.hidden; (f) keep the toggle choice in localStorage inside try/catch.

## Steps
- plan started 2026-10-30 14:35
- plan done 2026-10-30 14:35
- design started 2026-10-30 14:35
- design done 2026-10-30 14:39
- build started 2026-10-30 14:39

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

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-designer-ui | claude-sonnet-5-5 | medium | 8 | 2698 | 87795 | 30s | 2/2 omi-skill-ui-direction omi-skill-ui-a11y-review | n/a |
| omi-agent-engineer | claude-sonnet-5-5 | medium | 26 | 8533 | 386404 | 301s | 1/1 omi-skill-lean-implementation | - |
