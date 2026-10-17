# docker buildx policy eval

Evaluate policy for a source

## Usage

```console
docker buildx policy eval [OPTIONS] source
```

## Description

Evaluate policy for a source

## Options

| Option | Default | Description |
|---|---|---|
| `--fields` | `[]` | Fields to evaluate |
| `--file, -f` | `Dockerfile` | Policy filename to evaluate |
| `--platform` |  | Target platform for policy evaluation |
| `--print` | `false` | Print policy output |
| `--builder` |  | Override the configured builder instance |
| `--debug, -D` | `false` | Enable debug logging |
