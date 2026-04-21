# Overlay: SQL (MC-OVO-30-SQL — 7 of 8 language overlays, multi-dialect)

Loads when CWD contains `*.sql`, `migrations/`, `schema.sql`, `alembic.ini`, `prisma/schema.prisma` with raw SQL, or any of: `postgresql.conf`, `my.cnf`, `sqlite3` database files. ~300 tokens.

Covers **Postgres + MySQL + SQLite** as specified by Owner. MSSQL and Oracle deferred — different enough operator semantics to warrant their own overlay.

## Dialect-agnostic baseline (applies to all three)

- **Parameterized queries only.** `f"SELECT * FROM users WHERE id = {user_id}"` is a delivery-blocker (SQL injection vector). Use the driver's placeholder syntax: `%s` (psycopg2/MySQLdb), `?` (sqlite3/asyncpg DSN), `$1` (asyncpg raw), `:name` (SQLAlchemy/Prisma). No exceptions.
- **Migrations over ad-hoc DDL.** Every schema change goes through a migration tool (Alembic, Flyway, Prisma Migrate, dbmate, golang-migrate). No `ALTER TABLE` via an ssh shell on production. Migrations are reversible where possible (`down` function defined).
- **Transactions bound:** wrap multi-statement writes in `BEGIN; ... COMMIT;` (or the ORM's `transaction` context manager). Isolation level SERIALIZABLE for financial/inventory writes; READ COMMITTED default otherwise. Retry on serialization conflict with exponential backoff.
- **Index hygiene:** every `WHERE` predicate on a table with >10k rows needs an index on the predicate column (or a covering composite). Run `EXPLAIN ANALYZE` (Postgres) / `EXPLAIN` (MySQL) / `EXPLAIN QUERY PLAN` (SQLite) on every new query in a hot path. Seq scans on big tables = delivery-blocker unless intentional.
- **NULL discipline:** `NOT NULL` by default on every column unless absence is a valid domain state. `COALESCE(col, default)` in queries where a NULL would break downstream arithmetic. `IS NULL` / `IS NOT NULL` — never `= NULL` (silently matches nothing).
- **Timestamps:** store as UTC (`timestamptz` on Postgres, `DATETIME` with explicit UTC convention on MySQL/SQLite). Never `timestamp` (without zone) on Postgres — ambiguity kills later.
- **No SELECT *:** name columns explicitly. `SELECT *` breaks when schema evolves (new columns silently flow through, potentially exposing secrets).

## Postgres-specific

- **Use `jsonb` not `json`.** `jsonb` is binary, indexed, queryable; `json` is text-only.
- **UUIDs as PK:** prefer `uuid` type with `gen_random_uuid()` default (from `pgcrypto` extension) over bigserial when rows cross shard/service boundaries.
- **Row-Level Security (RLS):** `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` on any table with per-user data. Policies declared explicitly; `FORCE ROW LEVEL SECURITY` to apply even to the table owner.
- **EXPLAIN ANALYZE (BUFFERS, FORMAT JSON)** for deep perf inspection. `pg_stat_statements` extension enabled in prod for query frequency tracking.
- **Vacuuming:** `autovacuum` default ON; monitor `pg_stat_user_tables.n_dead_tup` — dead-tuple bloat degrades perf silently. `VACUUM FULL` locks the table, use `pg_repack` for online.

## MySQL-specific (InnoDB assumed; MyISAM refused in new code)

- **Charset:** `utf8mb4` (NOT `utf8`, which is 3-byte only and silently truncates emojis). Collation: `utf8mb4_0900_ai_ci` on MySQL 8.0+, `utf8mb4_unicode_ci` on older.
- **InnoDB row format:** `DYNAMIC` (MySQL 8.0 default); avoids the 767-byte key prefix limit on legacy `COMPACT`.
- **Foreign keys enforced:** `foreign_key_checks = 1` always; disable only during bulk restores.
- **`ON DUPLICATE KEY UPDATE`** for upsert; MySQL 8.0.19+ supports `INSERT ... ON DUPLICATE KEY UPDATE` with `VALUES()` references but prefer explicit column list.
- **MySQL-specific functions don't portable:** `GROUP_CONCAT` (not in SQL standard), `FIND_IN_SET` — fine in a MySQL-only project, but flag if app needs dialect portability.

## SQLite-specific

- **WAL mode:** `PRAGMA journal_mode=WAL;` enables concurrent reads + single-writer. Default `DELETE` mode causes reader/writer contention.
- **Foreign keys OFF by default:** `PRAGMA foreign_keys=ON;` on EVERY connection (not persistent). Most ORMs do this automatically; verify.
- **Only ONE writer at a time:** concurrent writes serialize. For high-write workloads, move to Postgres — don't add complexity fighting SQLite.
- **Type affinity, not type enforcement:** SQLite stores anything anywhere unless you use `STRICT` tables (3.37+). Use `STRICT` for new schemas.
- **Backup:** `.backup` command via `sqlite3` CLI is atomic; safer than `cp` when DB is open.

## Verification gate (any dialect)

```
SQL lint:      sqlfluff lint --dialect <postgres|mysql|sqlite>   → 0 errors
Migration dry: <migration-tool> --dry-run                         → diff output reviewed
EXPLAIN:       EXPLAIN ANALYZE <new query>                        → no seq-scan on large tables
Destructive:   Migrations touching prod data MUST have a reversible down() OR a documented recovery procedure
```

Pre-deploy destructive migrations (DROP / ALTER ... DROP / TRUNCATE): require explicit owner sign-off + verified backup. No automatic reverse — a drop is a one-way door.
