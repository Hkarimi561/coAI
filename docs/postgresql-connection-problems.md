---
title: PostgreSQL connection errors and too many connections
status: approved
owner: dba-team
---

# PostgreSQL connection errors and too many connections

خلاصه (فارسی): خطاهای `connection refused`، `password authentication failed` و `too many connections` سه علت متفاوت دارند. ابتدا مشخص کنید PostgreSQL در حال اجراست، سپس آدرس/پورت، احراز هویت (`pg_hba.conf`) و تعداد اتصال‌ها را بررسی کنید.

## `could not connect to server: Connection refused`

1. Is PostgreSQL running and listening?

```bash
sudo systemctl status postgresql --no-pager
sudo ss -ltnp | grep 5432
```

2. For Docker deployments:

```bash
docker ps --filter name=postgres
docker logs --tail 50 <postgres-container>
```

3. If it only listens on `127.0.0.1`, remote clients and other containers cannot connect. Set `listen_addresses = '*'` in `postgresql.conf` and allow the client network in `pg_hba.conf`, then reload:

```bash
sudo -u postgres psql -c 'SELECT pg_reload_conf();'
```

## `FATAL: password authentication failed for user`

- Verify the credentials the application uses (environment variable / secret), not the ones you remember.
- Test manually:

```bash
psql "postgresql://<user>@<host>:5432/<db>" -c 'select 1'
```

- Check the matching rule in `pg_hba.conf` (method `scram-sha-256` vs `md5` vs `trust`). A client that only supports md5 cannot log in to a user whose password is stored as scram unless the rule allows it.
- After changing a password remember to update all consumers and restart them.

## `FATAL: sorry, too many clients already` / `remaining connection slots are reserved`

1. See who holds the connections:

```sql
SELECT usename, application_name, state, count(*)
FROM pg_stat_activity GROUP BY 1,2,3 ORDER BY 4 DESC;
SHOW max_connections;
```

2. Terminate idle-in-transaction sessions that leak connections (review first, this is destructive):

```sql
SELECT pg_terminate_backend(pid) FROM pg_stat_activity
WHERE state = 'idle in transaction' AND state_change < now() - interval '10 minutes';
```

3. Long-term fix: use a connection pool (PgBouncer) and size application pools so that `pool_size x instances < max_connections`.

## `FATAL: database "<name>" does not exist`

List databases with `psql -l`; create the missing one with `createdb <name>` or fix the `POSTGRES_DB` variable. In Docker the init variables only apply the first time the data volume is created.

## Verification

- `pg_isready -h <host> -p 5432` prints `accepting connections`.
- The application health endpoint reports the database as healthy.
- `SELECT count(*) FROM pg_stat_activity;` stays well below `max_connections`.
