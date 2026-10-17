# docker load

Load an image from a tar archive or STDIN

**Aliases:** `docker image load, docker load`

## Usage

```console
docker load [OPTIONS]
```

## Description

Load an image from a tar archive or STDIN

## Options

| Option | Default | Description |
|---|---|---|
| `--input, -i` |  | Read from tar archive file, instead of STDIN |
| `--platform` | `[]` | Load only the given platform(s). Formatted as a comma-separated list of `os[/arch[/variant]]` (e.g., `linux/amd64,linux/arm64/v8`). |
| `--quiet, -q` | `false` | Suppress the load output |
