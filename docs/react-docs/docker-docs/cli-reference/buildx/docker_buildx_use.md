# docker buildx use

Set the current builder instance

## Usage

```console
docker buildx use [OPTIONS] NAME
```

## Description

Switches the current builder instance. Build commands invoked after this command
will run on a specified builder. Alternatively, a context name can be used to
switch to the default builder of that context.

## Options

| Option | Default | Description |
|---|---|---|
| `--default` | `false` | Set builder as default for current context |
| `--global` | `false` | Builder persists context changes |
| `--builder` |  | Override the configured builder instance |
| `--debug, -D` | `false` | Enable debug logging |

## Examples

### Override the configured builder instance (--builder) {#builder}

Same as [`buildx --builder`](/reference/cli/docker/buildx/#builder).
