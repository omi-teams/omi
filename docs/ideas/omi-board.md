# omi-board (idea, parked)

Status: parked. Build it in a separate repo, using omi-squad, after the current omi-squad improvements are done. Then connect the two.

## Why
GitHub Projects on the free plan fails often. The PO wants a task manager with a detailed hierarchy and a dashboard.

## Decisions so far (2026-10-26)
- Separate repo `omi-board`. The board DB is the source of truth (option A).
- One local Docker image: Go API (net/http, pgx, sqlc, goose) with a React (Vite, TS) UI embedded via `go:embed`. Realtime via SSE + Postgres LISTEN/NOTIFY. Bind 127.0.0.1:8080.
- DB: Supabase Postgres via a direct `DATABASE_URL` (not the Supabase Data API). Optional `offline` compose profile with local Postgres; switching is one env var.
- Free only. Rejected: Netlify (300 credits/month hard cap, ~15 per deploy), Northflank free (not for production), stdlib in-repo board (single repo only).

## Features
- Multi-project: one project per repo that uses omi.
- Hierarchy Epic → Feature → Task / Bug; depends, priority P0–P3, labels, milestone, estimate; bug severity, repro, found-in, fixed-by.
- Views: kanban (drag and drop), tree, table (filter/sort), bug list.
- Item detail: goal, acceptance-criteria checklist, checkpoint, reports, usage, comments, activity log.
- Dashboard: progress per epic/milestone, burndown, tokens per task and per tool, review rounds, open bugs, blocked items.
- Full-text search (Postgres FTS).
- Workflow/step rules enforced in the API, so UI and CLI follow the same rules.

## omi-squad integration
- `omi` calls the local API with a token; auto-runs `docker compose up` if it is down.
- `omi run` exports the task to a file in the worktree for agents, then posts reports and usage back.

## Risks
- Supabase free pauses a project after ~1 week idle; the board shows "DB paused" (restore in Supabase or use the `offline` profile).
- Auth/token/secrets code gets an opus review.

## Roadmap
1. Schema, API, migrations
2. Import existing `.omi/tasks`
3. UI
4. Dashboard
5. Switch omi-squad to the API
