# docker scout vex get

Get VEX attestation for image

## Usage

```console
docker scout vex get OPTIONS IMAGE
```

## Description

The docker scout vex get command gets a VEX attestation for images.

## Options

| Option | Default | Description |
|---|---|---|
| `--key` | `https://registry.scout.docker.com/keyring/dhi/latest.pub` | Signature key to use for verification |
| `--org` |  | Namespace of the Docker organization |
| `--output, -o` |  | Write the report to a file |
| `--platform` |  | Platform of image to analyze |
| `--ref` |  | Reference to use if the provided tarball contains multiple references. Can only be used with archive |
| `--skip-tlog` | `false` | Skip signature verification against public transaction log |
| `--verify` | `false` | Verify the signature on the attestation |
