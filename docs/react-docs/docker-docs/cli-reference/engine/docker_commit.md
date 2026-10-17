# docker commit

Create a new image from a container's changes

**Aliases:** `docker container commit, docker commit`

## Usage

```console
docker commit [OPTIONS] CONTAINER [REPOSITORY[:TAG]]
```

## Description

Create a new image from a container's changes

## Options

| Option | Default | Description |
|---|---|---|
| `--author, -a` |  | Author (e.g., `John Hannibal Smith <hannibal@a-team.com>`) |
| `--change, -c` |  | Apply Dockerfile instruction to the created image |
| `--message, -m` |  | Commit message |
| `--no-pause` | `false` | Disable pausing container during commit |
