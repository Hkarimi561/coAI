# docker rmi

Remove one or more images

**Aliases:** `docker image rm, docker image remove, docker rmi`

## Usage

```console
docker rmi [OPTIONS] IMAGE [IMAGE...]
```

## Description

Remove one or more images

## Options

| Option | Default | Description |
|---|---|---|
| `--force, -f` | `false` | Force removal of the image |
| `--no-prune` | `false` | Do not delete untagged parents |
| `--platform` | `[]` | Remove only the given platform variant. Formatted as `os[/arch[/variant]]` (e.g., `linux/amd64`) |
