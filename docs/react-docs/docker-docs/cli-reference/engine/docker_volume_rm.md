# docker volume rm

Remove one or more volumes

**Aliases:** `docker volume rm, docker volume remove`

## Usage

```console
docker volume rm [OPTIONS] VOLUME [VOLUME...]
```

## Description

Remove one or more volumes. You can't remove a volume that's in use by a container.

## Options

| Option | Default | Description |
|---|---|---|
| `--force, -f` | `false` | Force the removal of one or more volumes |

## Examples

```console
$ docker volume rm hello

hello
```
