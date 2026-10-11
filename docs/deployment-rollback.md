---
title: Roll back a bad deployment (Docker Compose)
status: approved
owner: platform-team
---

# Roll back a bad deployment (Docker Compose)

خلاصه (فارسی): اگر دیپلوی جدید باعث خطا شده، سریع‌ترین راه بازگشت به تگ ایمیج قبلی و اجرای دوباره‌ی `docker compose up -d` است. هرگز از تگ `latest` برای تولید استفاده نکنید تا بازگشت ممکن باشد.

## Preconditions

- Images are tagged with an immutable version or git SHA (not only `latest`).
- You know the last known good tag. Find it with:

```bash
docker image ls <registry>/<app> --format '{{.Tag}}\t{{.CreatedAt}}' | head
git log --oneline -n 10
```

## Procedure

1. Announce the rollback in the team channel.
2. Pin the previous tag in the environment file or compose override:

```bash
sed -i 's/^APP_IMAGE_TAG=.*/APP_IMAGE_TAG=<previous-tag>/' .env
```

3. Pull and recreate only the affected service:

```bash
docker compose pull <service>
docker compose up -d <service>
```

4. Watch the rollout:

```bash
docker compose ps
docker compose logs --tail 100 -f <service>
```

## Database migrations

If the bad release ran a migration, check whether it is backwards compatible **before** rolling the code back. A destructive migration (dropped column) requires restoring from backup or a forward fix. Do not downgrade a database without a verified backup.

## Verification

- `docker compose ps` shows the service `healthy`.
- The smoke test endpoint returns 200: `curl -fsS https://<host>/health`.
- Error rate in monitoring returns to the pre-deployment baseline.
- A post-mortem ticket is opened with the failing tag and the symptoms.
