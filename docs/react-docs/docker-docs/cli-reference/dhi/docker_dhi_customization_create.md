# docker dhi customization create

Create a new customization from YAML file

## Usage

```console
docker dhi customization create <file>
```

## Description

Create a new Docker Hardened Images customization using a YAML file as input.
The file should contain the complete customization structure without an 'id' field.

Flags can override values from the YAML file (see --help for details).
Shell completions are available for --destination and --tag-definition-id flags.
Run 'docker dhi completion --help' to set up shell completions.

## Options

| Option | Default | Description |
|---|---|---|
| `--destination, -d` |  | Override the destination repository (e.g. myorg/dhi-golang) |
| `--json` | `false` | Output in JSON format |
| `--name, -n` |  | Override the customization name from the YAML file |
| `--tag-definition-id, -t` |  | Override the tag definition ID (single-target only) |
| `--org` |  | Docker Hub organization (overrides config) |
