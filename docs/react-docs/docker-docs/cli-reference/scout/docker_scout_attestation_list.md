# docker scout attestation list

List attestations for image

**Aliases:** `docker scout attestation list, docker scout attest list`

## Usage

```console
docker scout attestation list OPTIONS IMAGE
```

## Description

The docker scout attestation list command lists attestations for images.

## Options

| Option | Default | Description |
|---|---|---|
| `--format` | `list` | Output format: - list: list of attestations of the image - json: json representation of the attestation list (default "json") |
| `--org` |  | Namespace of the Docker organization |
| `--output, -o` |  | Write the report to a file |
| `--platform` |  | Platform of image to analyze |
| `--predicate-type` |  | Predicate-type for attestations |
| `--ref` |  | Reference to use if the provided tarball contains multiple references. Can only be used with archive |
