---
title: Docker container exits, restarts in a loop or is unhealthy
status: approved
owner: platform-team
---

# Docker container exits, restarts in a loop or is unhealthy

خلاصه (فارسی): وقتی کانتینر مدام ریستارت می‌شود یا `Exited` است، ابتدا کد خروج و لاگ‌ها را بررسی کنید: کد `137` یعنی کمبود حافظه (OOM) یا kill شدن، کد `1` معمولاً خطای برنامه و کد `139` یعنی segfault.

## Step 1 - collect facts (read-only)

```bash
docker ps -a --filter name=<container> --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'
docker inspect <container> --format 'exit={{.State.ExitCode}} oom={{.State.OOMKilled}} restarts={{.RestartCount}} health={{.State.Health.Status}}'
docker logs --tail 100 --timestamps <container>
```

## Step 2 - interpret the exit code

| Exit code | Meaning | Next action |
|-----------|---------|-------------|
| 0 | Process finished normally | Container is meant to be long running? Check the `CMD`/entrypoint. |
| 1 | Application error | Read the last lines of the log for the stack trace. |
| 125/126/127 | Docker could not run the command / not executable / not found | Fix `CMD`, file permissions or the image. |
| 137 | SIGKILL - usually out of memory (`OOMKilled=true`) or `docker kill` | Raise the memory limit or fix the leak, see below. |
| 139 | Segmentation fault | Upgrade the image/library; check native dependencies. |
| 143 | SIGTERM - stopped gracefully | Someone or an orchestrator stopped it. |

## Out of memory (exit 137, OOMKilled=true)

1. Confirm: `docker inspect <container> --format '{{.State.OOMKilled}}'` prints `true`.
2. Check the current limit and usage: `docker stats --no-stream <container>`.
3. Increase the limit in the compose file (`deploy.resources.limits.memory` or `mem_limit`) and recreate:

```bash
docker compose up -d <service>
```

## Unhealthy container

```bash
docker inspect <container> --format '{{json .State.Health}}' | head -c 2000
```

Look at the last health check outputs. A failing `curl`/`pg_isready` command means the service inside is not ready; check its logs and its dependencies (database, cache).

## Crash loop on startup: dependency not ready

Symptoms: logs show `connection refused` / `could not translate host name` right after start. Add `depends_on` with `condition: service_healthy` and a health check on the dependency, then recreate the stack with `docker compose up -d`.

## Verification

- `docker ps` shows `Up ... (healthy)` for at least a few minutes.
- `RestartCount` stops increasing: `docker inspect <container> --format '{{.RestartCount}}'`.
- The application endpoint responds as expected.
