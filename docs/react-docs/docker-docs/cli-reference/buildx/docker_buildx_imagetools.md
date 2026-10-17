# docker buildx imagetools

Commands to work on images in registry

## Usage

```console
docker buildx imagetools
```

## Description

The `imagetools` commands contains subcommands for working with manifest lists
in container registries. These commands are useful for inspecting manifests
to check multi-platform configuration and attestations.

## Subcommands

- `docker buildx imagetools create`
- `docker buildx imagetools inspect`

## Options

| Option | Default | Description |
|---|---|---|
| `--builder` |  | Override the configured builder instance |
| `--debug, -D` | `false` | Enable debug logging |

## Examples

### Override the configured builder instance (--builder) {#builder}

Same as [`buildx --builder`](/reference/cli/docker/buildx/#builder).
