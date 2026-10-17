# docker rm

Remove one or more containers

**Aliases:** `docker container rm, docker container remove, docker rm`

## Usage

```console
docker rm [OPTIONS] CONTAINER [CONTAINER...]
```

## Description

Remove one or more containers

## Options

| Option | Default | Description |
|---|---|---|
| `--force, -f` | `false` | Force the removal of a running container (uses SIGKILL) |
| `--link, -l` | `false` | Remove the specified link |
| `--volumes, -v` | `false` | Remove anonymous volumes associated with the container |
