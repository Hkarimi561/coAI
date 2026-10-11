---
title: Triage a failed CI build or deployment
status: approved
owner: devex-team
---

# Triage a failed CI build or deployment

خلاصه (فارسی): برای بررسی علت شکست بیلد ابتدا اولین step شکست‌خورده را پیدا کنید (نه آخرین خطا)، بعد بین سه دسته تفکیک کنید: خطای کد/تست، خطای وابستگی/شبکه و خطای زیرساخت runner. پیام اولین خطای واقعی معمولاً علت ریشه‌ای است.

## Step 1 - find the first failing step

Open the failed run, expand the first red step and read upward from the first `error`/`Error:` line. Later errors are often consequences.

With the GitHub CLI:

```bash
gh run list --limit 5
gh run view <run-id> --log-failed | head -n 200
```

## Step 2 - classify

| Category | Typical messages | Action |
|----------|------------------|--------|
| Code / tests | `AssertionError`, `FAILED tests/...`, compiler errors | Reproduce locally with the same command; fix or revert the commit. |
| Dependencies / network | `npm ERR! code ETIMEDOUT`, `Could not resolve host`, `429 Too Many Requests` | Re-run once; if persistent, check registry/mirror status and cache keys. |
| Auth / secrets | `denied: requested access to the resource is denied`, `401`, `Resource not accessible by integration` | Check that the secret exists and the token has the needed scope; secrets are not available to forked PRs. |
| Runner / infra | `No space left on device`, `The runner has received a shutdown signal` | See the disk-full runbook; retry on another runner. |

## Docker build failures

- `failed to solve: ... returned a non-zero code: 1` - the failing command is printed just above; run the same `RUN` line in a shell inside the base image.
- `COPY failed: file not found in build context` - check `.dockerignore` and the build context path.
- Layer cache looks stale: re-run with `--no-cache` once to rule out cache corruption.

## Deployment failures

1. Roll back first if production is affected (see the deployment rollback runbook), investigate afterwards.
2. Check the container after deployment: `docker logs --tail 100 <container>` and its health status.
3. Compare the failing commit with the last green one: `git log --oneline <green-sha>..<failing-sha>`.

## Verification

- A re-run on the same commit passes, or the fix commit produces a green pipeline.
- The deployed service passes its health check and shows no new errors in logs for 10 minutes.
