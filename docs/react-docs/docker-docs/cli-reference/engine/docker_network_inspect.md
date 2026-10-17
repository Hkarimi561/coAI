# docker network inspect

Display detailed information on one or more networks

## Usage

```console
docker network inspect [OPTIONS] NETWORK [NETWORK...]
```

## Description

Returns information about one or more networks. By default, this command renders
all results in a JSON object.

## Options

| Option | Default | Description |
|---|---|---|
| `--format, -f` |  | Format output using a custom template: 'json': Print in JSON format 'TEMPLATE': Print output using the given Go template. Refer to https://docs.docker.com/go/formatting/ for more information about formatting output with templates |
| `--verbose, -v` | `false` | Verbose output for diagnostics |
