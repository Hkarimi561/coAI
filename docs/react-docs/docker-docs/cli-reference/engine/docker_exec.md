# docker exec

Execute a command in a running container

**Aliases:** `docker container exec, docker exec`

## Usage

```console
docker exec [OPTIONS] CONTAINER COMMAND [ARG...]
```

## Description

Execute a command in a running container

## Options

| Option | Default | Description |
|---|---|---|
| `--detach, -d` | `false` | Detached mode: run command in the background |
| `--detach-keys` |  | Override the key sequence for detaching a container |
| `--env, -e` |  | Set environment variables |
| `--env-file` |  | Read in a file of environment variables |
| `--interactive, -i` | `false` | Keep STDIN open even if not attached |
| `--privileged` | `false` | Give extended privileges to the command |
| `--tty, -t` | `false` | Allocate a pseudo-TTY |
| `--user, -u` |  | Username or UID (format: `<name\|uid>[:<group\|gid>]`) |
| `--workdir, -w` |  | Working directory inside the container |
