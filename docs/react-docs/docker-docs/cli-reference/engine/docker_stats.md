# docker stats

Display a live stream of container(s) resource usage statistics

**Aliases:** `docker container stats, docker stats`

## Usage

```console
docker stats [OPTIONS] [CONTAINER...]
```

## Description

Display a live stream of container(s) resource usage statistics

## Options

| Option | Default | Description |
|---|---|---|
| `--all, -a` | `false` | Show all containers (default shows just running) |
| `--format` |  | Format output using a custom template: 'table': Print output in table format with column headers (default) 'table TEMPLATE': Print output in table format using the given Go template 'json': Print in JSON format 'TEMPLATE': Print output using the given Go template. Refer to https://docs.docker.com/go/formatting/ for more information about formatting output with templates |
| `--no-stream` | `false` | Disable streaming stats and only pull the first result |
| `--no-trunc` | `false` | Do not truncate output |
