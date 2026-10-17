# docker desktop logs

Print log entries for Docker Desktop

## Usage

```console
docker desktop logs [OPTIONS]
```

## Options

| Option | Default | Description |
|---|---|---|
| `--boot, -b` | `0` | Show logs from a specified boot. Zero means the current or boot, one the second last boot, and so on |
| `--color, -c` | `False` | Enable colored output. Priority levels are highlighted. |
| `--color-mode, -m` | `default` | Color mode to use. Can be `default` or `priority` |
| `--directory, -D` | `False` | Specifies a custom directory to search for log entries |
| `--priority, -p` | `-1` | Filter output by log priorities. `-1` is all, `0` is info or above, `1` filters for warnings or above, `2` filters for errors. |
| `--since, -S` |  | Start showing entries on or newer than the specified date and time. Uses the systemd.time(7) format. |
| `--unit, -u` | `[]` | Filter by one or more categories (e.g. `--unit=com.docker.backend.ipc`, `com.docker.backend.apiproxy`) |
| `--until, -U` | `False` | Start showing entries on or before the specified date and time. Uses the systemd.time(7) format. |
