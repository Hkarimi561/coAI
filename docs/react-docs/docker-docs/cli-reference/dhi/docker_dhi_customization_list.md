# docker dhi customization list

List all customizations

## Usage

```console
docker dhi customization list
```

## Description

List all Docker Hardened Images customizations

## Options

| Option | Default | Description |
|---|---|---|
| `--bulk-id` |  | Filter by bulk customization ID (exact match) |
| `--filter, -f` |  | Filter by customization name (case-insensitive substring match) |
| `--json` | `false` | Output in JSON format |
| `--repo, -r` |  | Filter by destination repository (case-insensitive substring match) |
| `--source` |  | Filter by DHI source repository (case-insensitive substring match) |
| `--org` |  | Docker Hub organization (overrides config) |
