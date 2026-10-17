# docker dhi customization edit

Edit an existing customization from YAML file

**Aliases:** `docker dhi customization edit, docker dhi customization update`

## Usage

```console
docker dhi customization edit <file>
```

## Description

Edit an existing Docker Hardened Images customization using a YAML file as input. The file should contain the complete customization structure with an 'id' field to identify which customization to update.

## Options

| Option | Default | Description |
|---|---|---|
| `--json` | `false` | Output in JSON format |
| `--org` |  | Docker Hub organization (overrides config) |
