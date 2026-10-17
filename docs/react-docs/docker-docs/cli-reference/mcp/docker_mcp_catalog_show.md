# docker mcp catalog show

Show a catalog

## Usage

```console
docker mcp catalog show <oci-reference> [--pull <pull-option>]
```

## Description

Show a catalog

## Options

| Option | Default | Description |
|---|---|---|
| `--format` | `human` | Supported: json, yaml, human. |
| `--no-tools` | `false` | Exclude tools from output (deprecated, use --yq instead) |
| `--pull` | `never` | Supported: missing, never, always, initial, exists, or duration (e.g. '1h', '1d'). Duration represents time since last update. |
| `--yq` |  | YQ expression to apply to the output |
