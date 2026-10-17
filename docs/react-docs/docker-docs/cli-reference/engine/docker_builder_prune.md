# docker builder prune

Remove build cache

## Usage

```console
docker builder prune
```

## Description

Remove build cache

## Options

| Option | Default | Description |
|---|---|---|
| `--all, -a` | `false` | Remove all unused build cache, not just dangling ones |
| `--filter` |  | Provide filter values (e.g. `until=24h`) |
| `--force, -f` | `false` | Do not prompt for confirmation |
| `--keep-storage` | `0` | Amount of disk space to keep for cache |
