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
step: design
---
## Goal
Plain HTML/CSS/JS pages for home, project dashboard and task detail, in Vietnamese, calling the JSON API.

## Acceptance criteria
- [ ] Home, dashboard (PO-waiting, plans, kanban, activity, decisions, usage, sync) and task detail render from the API; auto-refresh every 30 s with a toggle.
- [ ] State text is inserted with `textContent` only, never `innerHTML`; no external script, font or CDN.
- [ ] `pip install .` ships `board/web/*` (package data); a test checks the files are in the installed package.
- [ ] Readable at 360 px width and keyboard navigable; all tests pass.

## Checkpoint
Done:
Not done:
Tests:
Next: build per designer spec in ## Reports. PO 2026-10-30: accept designer defaults for OPEN 1-4 (header "omi board", teal #0f6e6e, dark mode via prefers-color-scheme, Vietnamese date/number format, evergreen browsers).

## Steps
- plan started 2026-10-30 14:35
- plan done 2026-10-30 14:35
- design started 2026-10-30 14:35

## Reports
2026-10-30 14:38 omi-agent-designer-ui (claude):
> MODE: SPEC
> - Routing, `web/index.html` + `app.css` + `app.js`: the server serves only real files and `/` maps to `index.html`, so there are no SPA paths. Use hash routes `#/`, `#/p/<name>`, `#/p/<name>/t/<id>` in one page, with one `h1` that changes per route, `document.title` per route, and focus moved to the `h1` after each route change. Everything is same-origin because of the CSP `default-src 'self'`. That means no inline `<script>`, `<style>` or `style=""`, and no web fonts. Use the system font stack with `font-variant-numeric: tabular-nums`. Build all state text with `textContent` and `createElement`; build URLs with `encodeURIComponent`.
> - Layout and tokens (360 px first, one column; at 768 px and wider the kanban becomes a 5-column grid; max-width 1200 px; spacing 4/8/16/24): `<html lang="vi">`, a skip link, `header` with `nav` (Trang chủ / breadcrumb), `main`, and the refresh toggle in the header. Dashboard order is Chờ PO (first, accent border), Kế hoạch (done/total as text plus `<progress>`), Kanban (heading with count per column; cards are links to the task), Hoạt động, Quyết định, Sử dụng (a real `<table>` in a scroll wrapper with a `tabindex=0` caption), Đồng bộ (ahead/behind/dirty as text). Light and dark via `prefers-color-scheme`. Tinted gray family, one accent (a muted teal, for example `#0f6e6e` on `#fafaf9`, with no pure black). Radius 8 px outer, 4 px inner. Status uses text plus a glyph, not color alone.
> [... truncated ...]
> OPEN: (1) Brand, accent color and a logo or name for the header: use "omi board" and the teal above unless the PO says otherwise. (2) Dark mode: confirm it is wanted. (3) Date and number format in Vietnamese (dd/MM/yyyy and `.` thousands separators) or raw ISO values as the API gives them? (4) Target browsers: assume evergreen desktop and mobile with no IE or old Safari.

## Usage
| role | model | effort | input | output | cache | duration | skills read | verdict |
|---|---|---|---|---|---|---|---|---|
| omi-agent-designer-ui | claude-sonnet-5-5 | medium | 8 | 2698 | 87795 | 30s | 2/2 omi-skill-ui-direction omi-skill-ui-a11y-review | n/a |
