# docker save

Save one or more images to a tar archive (streamed to STDOUT by default)

**Aliases:** `docker image save, docker save`

## Usage

```console
docker save [OPTIONS] IMAGE [IMAGE...]
```

## Description

Save one or more images to a tar archive (streamed to STDOUT by default)

## Options

| Option | Default | Description |
|---|---|---|
| `--output, -o` |  | Write to a file, instead of STDOUT |
| `--platform` | `[]` | Save only the given platform(s). Formatted as a comma-separated list of `os[/arch[/variant]]` (e.g., `linux/amd64,linux/arm64/v8`) |
