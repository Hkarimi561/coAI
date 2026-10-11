---
title: Disk full (No space left on device)
status: approved
owner: platform-team
---

# Disk full (`No space left on device`)

خلاصه (فارسی): با خطای `No space left on device` ابتدا بفهمید کدام پارتیشن پر شده (`df -h`) و بعد بزرگ‌ترین مصرف‌کننده را پیدا کنید. در سرورهای Docker معمولاً ایمیج‌ها، لاگ کانتینرها و volume های بدون استفاده مقصر هستند. پیش از حذف هر چیزی مطمئن شوید که قابل بازیابی است.

## Step 1 - which filesystem is full?

```bash
df -h
df -i   # inode exhaustion also reports "No space left on device"
```

## Step 2 - find the biggest directories

```bash
sudo du -xh --max-depth=2 /var | sort -rh | head -n 20
```

## Docker-specific cleanup

1. See what Docker uses:

```bash
docker system df
```

2. Remove stopped containers, unused networks and dangling images (safe, review the prompt):

```bash
docker system prune
```

3. Remove ALL unused images (not only dangling). Destructive: images must be pulled again.

```bash
docker image prune -a
```

4. Large container logs: find the biggest JSON log files.

```bash
sudo sh -c 'ls -lhS /var/lib/docker/containers/*/*-json.log | head'
```

Prevent regrowth by enabling log rotation in `/etc/docker/daemon.json`:

```json
{ "log-driver": "json-file", "log-opts": { "max-size": "50m", "max-file": "3" } }
```

Then restart the Docker daemon during a maintenance window (containers restart): `sudo systemctl restart docker`.

## System logs and package caches

```bash
sudo journalctl --vacuum-size=500M
sudo apt-get clean         # Debian/Ubuntu
sudo dnf clean all         # RHEL/Fedora
```

## Deleted files still held open

If `df` shows a full disk but `du` does not add up, a process holds deleted files open:

```bash
sudo lsof +L1 | head
```

Restart the owning service to release the space.

## Verification

- `df -h` shows the filesystem below 85% usage.
- Services that failed with write errors (databases, log writers) recovered; check their logs.
- Log rotation is configured so that the problem does not return.
