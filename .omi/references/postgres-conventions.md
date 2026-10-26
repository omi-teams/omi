---
id: postgres-conventions
summary: PostgreSQL schema, migration and query conventions
---
# PostgreSQL conventions

Use this reference when designing schemas, migrations or database queries.

## Schema
Use descriptive snake_case names and name constraints and indexes. Prefer
`timestamptz` for instants and `text` for strings without a domain length limit.
Use identity columns for generated numeric keys. Make nullability explicit.

## Migrations
Keep each migration focused and preserve applied migration files. For large
tables, add nullable columns first, backfill in batches, then enforce constraints.
Plan concurrent index creation separately from transaction-wrapped changes.

## Queries
Bind user values as parameters. Use EXPLAIN to inspect expensive queries with
representative data; run EXPLAIN ANALYZE only where executing the query is safe.
Index foreign keys used in joins and filters; check index use before adding more.
