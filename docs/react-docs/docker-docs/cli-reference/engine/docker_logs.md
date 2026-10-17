# docker logs

Fetch the logs of a container

**Aliases:** `docker container logs, docker logs`

## Usage

```console
docker logs [OPTIONS] CONTAINER
```

## Description

Fetch the logs of a container

## Options

| Option | Default | Description |
|---|---|---|
| `--details` | `false` | Show extra details provided to logs |
| `--follow, -f` | `false` | Follow log output |
| `--since` |  | Show logs since timestamp (e.g. `2013-01-02T13:23:37Z`) or relative (e.g. `42m` for 42 minutes) |
| `--tail, -n` | `all` | Number of lines to show from the end of the logs |
| `--timestamps, -t` | `false` | Show timestamps |
| `--until` |  | Show logs before a timestamp (e.g. `2013-01-02T13:23:37Z`) or relative (e.g. `42m` for 42 minutes) |
