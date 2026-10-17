# docker buildx stop

Stop builder instance

## Usage

```console
docker buildx stop [NAME]
```

## Description

Stops the specified or current builder. This does not prevent buildx build to
restart the builder. The implementation of stop depends on the driver.

## Options

| Option | Default | Description |
|---|---|---|
| `--builder` |  | Override the configured builder instance |
| `--debug, -D` | `false` | Enable debug logging |

## Examples

### Override the configured builder instance (--builder) {#builder}

Same as [`buildx --builder`](/reference/cli/docker/buildx/#builder).
