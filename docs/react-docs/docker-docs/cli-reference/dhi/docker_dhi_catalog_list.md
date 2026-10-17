# docker dhi catalog list

List available Docker Hardened Images

## Usage

```console
docker dhi catalog list
```

## Description

List all available Docker Hardened Images and Helm charts in the catalog

## Options

| Option | Default | Description |
|---|---|---|
| `--filter, -f` |  | Filter by name (case-insensitive substring match) |
| `--fips` | `false` | Filter to FIPS compliant images (use --fips=false to exclude) |
| `--json` | `false` | Output in JSON format |
| `--stig` | `false` | Filter to STIG certified images (use --stig=false to exclude) |
| `--type` |  | Filter by type (image, helm, chart, or helm-chart) |
| `--org` |  | Docker Hub organization (overrides config) |
