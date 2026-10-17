# docker cp

Copy files/folders between a container and the local filesystem

**Aliases:** `docker container cp, docker cp`

## Usage

```console
docker cp [OPTIONS] CONTAINER:SRC_PATH DEST_PATH|-
	docker cp [OPTIONS] SRC_PATH|- CONTAINER:DEST_PATH
```

## Description

Copy files/folders between a container and the local filesystem

Use '-' as the source to read a tar archive from stdin
and extract it to a directory destination in a container.
Use '-' as the destination to stream a tar archive of a
container source to stdout.

## Options

| Option | Default | Description |
|---|---|---|
| `--archive, -a` | `false` | Archive mode (copy all uid/gid information) |
| `--follow-link, -L` | `false` | Always follow symlinks in SRC_PATH |
| `--quiet, -q` | `false` | Suppress progress output during copy. Progress output is automatically suppressed if no terminal is attached |
