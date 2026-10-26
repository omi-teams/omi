---
id: omi-skill-data-review
group: data
description: Use when reviewing or writing SQL, migrations, indexes, schema or row-level permissions for a PostgreSQL database, or when queries are slow or rows leak across users.
tokens: 1061
tools: Read, Grep, Bash
source_repo: https://github.com/supabase/agent-skills
source_ref: c9be0e931b7930f7d02126d04774d904c381e7d7
source_file: skills/supabase-postgres-best-practices/SKILL.md
source_license: MIT
source_use: adapt
---
<!-- Adapted from the Supabase postgres-best-practices skill (https://github.com/supabase/agent-skills), MIT, Copyright (c) 2026 Supabase, pinned at c9be0e931b7930f7d02126d04774d904c381e7d7.
     Only the skill's overview (8 priority categories) was available; the checks below follow those categories and the PostgreSQL documentation (https://www.postgresql.org/docs/current/). Changes: stack-neutral, Supabase parts moved to a labelled optional section. -->
# Data review (PostgreSQL)

## When to use
- A diff touches `.sql`, migrations, ORM models, indexes, policies or query code; a query is slow, times out, or a user sees another tenant's rows.

## When not to use
- Non-relational stores; pure application logic with no query change.

## Inputs
- The migration or query, table definitions, expected row counts, and `EXPLAIN (ANALYZE, BUFFERS)` output if a database is available (never on production).

## Steps
Check in this order; report blocking findings first, then continue with the remaining groups.
1. Queries (critical): no `SELECT *` on wide tables; every `WHERE`, `JOIN` and `ORDER BY` column on big tables is indexed; no N+1 (batch with `= ANY($1)` or a join); keyset pagination instead of large `OFFSET`; no function on an indexed column (`lower(col)` needs an expression index); read the plan: Seq Scan on a big table, bad row estimates, sorts spilling to disk.
2. Indexes: composite order is equality columns first, then range; partial index for hot subsets (`WHERE deleted_at IS NULL`); index every foreign-key column used in joins or deletes; drop duplicates and unused ones; `CREATE INDEX CONCURRENTLY` on live tables.
3. Connections (critical): a pool with a bounded size, short transactions, no network call inside a transaction, statement and idle timeouts set.
4. Row-level permissions (critical): every table with per-user or per-tenant rows has row-level security enabled (`ENABLE` and, for owners, `FORCE`) and policies for each command; `USING` and `WITH CHECK` both set for writes; policy columns are indexed; wrap per-row function calls as `(select auth_fn())` so they run once; no `SECURITY DEFINER` function without a fixed `search_path`; app roles lack `BYPASSRLS`, superuser and table ownership. Test with two users: user A must read and write zero rows of user B.
5. Schema: primary key on every table; `bigint` or `uuid` keys, `timestamptz` not `timestamp`, `numeric` for money, `text` over `varchar(n)` unless a limit is a rule; constraints (`NOT NULL`, `CHECK`, `FOREIGN KEY`, `UNIQUE`) in the database, not only in code; lowercase snake_case names.
6. Migrations and locking: no long `ALTER TABLE` that rewrites or locks a hot table (add column nullable, backfill in batches, then constrain with `NOT VALID` + `VALIDATE`); set `lock_timeout`; consistent lock order; short transactions; `SKIP LOCKED` for queues.
7. Data access: batch inserts (multi-row or `COPY`), upsert with `ON CONFLICT`, no per-row loops from the app.
8. Monitoring: `pg_stat_statements` for top queries; `VACUUM`/`ANALYZE` after big loads; watch table bloat.

## Optional: Supabase projects only
- RLS lives in the `public` schema; use `auth.uid()` as `(select auth.uid())`; the `service_role` key bypasses RLS and must never reach a browser; views run with owner rights unless `security_invoker = true`.

## Outputs and evidence
- Findings as `file:line - category - problem - fix (SQL)`, most severe first; plan before/after for performance claims; the two-user result for permissions.

## Stop and escalate
- The fix needs production access, a destructive migration (`DROP`, `TRUNCATE`, mass `UPDATE`) or files outside the task scope: stop and report NEEDS SCOPE or ask the PO.

## Tools needed
- Read, Grep; Bash for `psql` against a local or test database only.
