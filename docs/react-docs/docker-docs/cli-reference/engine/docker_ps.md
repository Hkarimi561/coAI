# docker ps

List containers

**Aliases:** `docker container ls, docker container list, docker container ps, docker ps`

## Usage

```console
docker ps [OPTIONS]
```

## Description

List containers

## Options

| Option | Default | Description |
|---|---|---|
| `--all, -a` | `false` | Show all containers (default shows just running) |
| `--filter, -f` |  | Filter output based on conditions provided |
| `--format` |  | Format output using a custom template: 'table': Print output in table format with column headers (default) 'table TEMPLATE': Print output in table format using the given Go template 'json': Print in JSON format 'TEMPLATE': Print output using the given Go template. Refer to https://docs.docker.com/go/formatting/ for more information about formatting output with templates |
| `--last, -n` | `-1` | Show n last created containers (includes all states) |
| `--latest, -l` | `false` | Show the latest created container (includes all states) |
| `--no-trunc` | `false` | Don't truncate output |
| `--quiet, -q` | `false` | Only display container IDs |
| `--size, -s` | `false` | Display total file sizes |
