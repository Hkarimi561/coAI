---
title: Restart, reload and troubleshoot Nginx
status: approved
owner: platform-team
---

# Restart, reload and troubleshoot Nginx

خلاصه (فارسی): برای اعمال تغییر تنظیمات Nginx ابتدا `nginx -t` را اجرا کنید و سپس از `reload` استفاده کنید؛ `restart` فقط وقتی لازم است که پروسه‌ی master هنگ کرده باشد. ریستارت Nginx باعث قطع اتصال‌های فعال می‌شود.

## When to use reload vs restart

- **Reload** re-reads the configuration without dropping active connections. Use it for every config change.
- **Restart** stops and starts the master process; active connections are dropped. Use it only when the master process is hung or after upgrading the binary.

## Procedure: apply a configuration change (host install)

1. Validate the configuration first. Never reload a config that fails the test:

```bash
sudo nginx -t
```

2. Reload gracefully:

```bash
sudo systemctl reload nginx
```

3. Verify the service is healthy and serving:

```bash
systemctl status nginx --no-pager
curl -sI http://localhost | head -n 1
```

## Procedure: restart Nginx (host install)

> Impact: all in-flight HTTP connections are dropped for 1-2 seconds. Do this outside peak hours.

```bash
sudo nginx -t && sudo systemctl restart nginx
```

## Procedure: Nginx running in Docker

```bash
# validate inside the running container
docker exec <nginx-container> nginx -t
# graceful reload
docker exec <nginx-container> nginx -s reload
# full restart of the container (drops connections)
docker restart <nginx-container>
```

## Common errors

### `bind() to 0.0.0.0:80 failed (98: Address already in use)`

Another process owns the port, often a previous Nginx instance or Apache.

```bash
sudo ss -ltnp | grep ':80 '
sudo systemctl stop apache2   # if Apache is the culprit
sudo systemctl start nginx
```

### `502 Bad Gateway` / `connect() failed (111: Connection refused) while connecting to upstream`

The upstream application is down or listening on another port.

1. Check the upstream service: `systemctl status <app>` or `docker ps --filter name=<app>`.
2. Confirm the port in the `upstream`/`proxy_pass` block matches what the app listens on: `ss -ltnp | grep <port>`.
3. Check the error log: `sudo tail -n 100 /var/log/nginx/error.log`.

### `nginx: [emerg] unknown directive` after editing

A typo or a missing module. Run `nginx -t` to get the exact file and line, fix it, and test again before reloading.

## Verification

- `nginx -t` prints `syntax is ok` and `test is successful`.
- `curl -sI https://<your-domain>` returns the expected status code.
- `error.log` shows no new `[emerg]` or `[crit]` entries after the reload.
