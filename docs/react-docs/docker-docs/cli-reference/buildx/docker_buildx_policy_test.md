# docker buildx policy test

Run policy tests

## Usage

```console
docker buildx policy test <path>
```

## Description

Run policy tests

## Options

| Option | Default | Description |
|---|---|---|
| `--filename` | `Dockerfile` | Name of the Dockerfile to validate |
| `--run` |  | Run only tests with name containing this substring |
| `--builder` |  | Override the configured builder instance |
| `--debug, -D` | `false` | Enable debug logging |
