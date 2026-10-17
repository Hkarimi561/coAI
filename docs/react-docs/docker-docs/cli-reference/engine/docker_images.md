# docker images

List images

**Aliases:** `docker image ls, docker image list, docker images`

## Usage

```console
docker images [OPTIONS] [REPOSITORY[:TAG]]
```

## Description

List images

## Options

| Option | Default | Description |
|---|---|---|
| `--all, -a` | `false` | Show all images (default hides intermediate and dangling images) |
| `--digests` | `false` | Show digests |
| `--filter, -f` |  | Filter output based on conditions provided |
| `--format` |  | Format output using a custom template: 'table': Print output in table format with column headers (default) 'table TEMPLATE': Print output in table format using the given Go template 'json': Print in JSON format 'TEMPLATE': Print output using the given Go template. Refer to https://docs.docker.com/go/formatting/ for more information about formatting output with templates |
| `--no-trunc` | `false` | Don't truncate output |
| `--quiet, -q` | `false` | Only show image IDs |
| `--tree` | `false` | List multi-platform images as a tree (EXPERIMENTAL) |
