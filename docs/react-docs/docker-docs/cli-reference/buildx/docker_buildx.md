# docker buildx

Docker Buildx

## Usage

```console
docker buildx
```

## Description

Extended build capabilities with BuildKit

## Subcommands

- `docker buildx bake`
- `docker buildx build`
- `docker buildx create`
- `docker buildx dap`
- `docker buildx debug`
- `docker buildx dial-stdio`
- `docker buildx du`
- `docker buildx history`
- `docker buildx imagetools`
- `docker buildx inspect`
- `docker buildx ls`
- `docker buildx policy`
- `docker buildx prune`
- `docker buildx replay`
- `docker buildx rm`
- `docker buildx stop`
- `docker buildx use`
- `docker buildx version`

## Options

| Option | Default | Description |
|---|---|---|
| `--builder` |  | Override the configured builder instance |
| `--debug, -D` | `false` | Enable debug logging |

## Examples

### Override the configured builder instance (--builder) {#builder}

You can also use the `BUILDX_BUILDER` environment variable.

### Enable the default policy

Set `BUILDX_DEFAULT_POLICY=1` to enable Buildx's built-in source policy. The
policy verifies signed tags for images managed by Docker, including BuildKit
builder images and Dockerfile frontends. Untagged digest references and images
outside the managed repositories are allowed unchanged. Tagged references
that also contain a digest still have their release identity verified.
