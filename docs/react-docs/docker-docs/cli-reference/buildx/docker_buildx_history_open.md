# docker buildx history open

Open a build record in Docker Desktop

## Usage

```console
docker buildx history open [OPTIONS] [REF]
```

## Description

Open a build record in Docker Desktop for visual inspection. This requires
Docker Desktop to be installed and running on the host machine.

## Options

| Option | Default | Description |
|---|---|---|
| `--builder` |  | Override the configured builder instance |
| `--debug, -D` | `false` | Enable debug logging |

## Examples

### Open the most recent build in Docker Desktop

```console
docker buildx history open
```

By default, this opens the most recent build on the current builder.

### Open a specific build

```console
# Using a build ID
docker buildx history open qu2gsuo8ejqrwdfii23xkkckt

# Or using a relative offset
docker buildx history open ^1
```
