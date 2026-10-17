# docker scout attestation get

Get attestation for image

**Aliases:** `docker scout attestation get, docker scout attest get`

## Usage

```console
docker scout attestation get OPTIONS IMAGE [DIGEST]
```

## Description

The docker scout attestation get command gets attestations for images.

## Options

| Option | Default | Description |
|---|---|---|
| `--key` | `https://registry.scout.docker.com/keyring/dhi/latest.pub` | Signature key to use for verification |
| `--org` |  | Namespace of the Docker organization |
| `--output, -o` |  | Write the report to a file |
| `--platform` |  | Platform of image to analyze |
| `--predicate` | `false` | Get in-toto predicate only dropping the subject |
| `--predicate-type` |  | Predicate-type for attestation |
| `--ref` |  | Reference to use if the provided tarball contains multiple references. Can only be used with archive |
| `--skip-tlog` | `false` | Skip signature verification against public transaction log |
| `--verify` | `false` | Verify the signature on the attestation |
