---
id: postgres
summary: PostgreSQL: migrations, queries, indexes, safety
applies: **/*.sql, **/migrations/**
---
# postgres

- Migrations are forward-only files, one change each; never edit an applied one.
- Use parameterized queries; never build SQL from strings with user input.
- Name constraints and indexes; add an index for every foreign key you query by.
- Use `timestamptz`, `text`, `bigint` identity keys; add `NOT NULL` unless null has a meaning.
- New columns on big tables: add nullable, backfill in batches, then add the constraint.
- Create indexes with `CONCURRENTLY` on live tables; wrap data changes in a transaction.
