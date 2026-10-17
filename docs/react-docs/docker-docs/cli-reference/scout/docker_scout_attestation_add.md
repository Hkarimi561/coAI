# docker scout attestation add

Add attestation to image

**Aliases:** `docker scout attestation add, docker scout attest add`

## Usage

```console
docker scout attestation add OPTIONS IMAGE [IMAGE...]
```

## Description

The docker scout attestation add command adds attestations to images.

## Options

| Option | Default | Description |
|---|---|---|
| `--file` | `[]` | File location of attestations to attach |
| `--org` |  | Namespace of the Docker organization |
| `--predicate-type` |  | Predicate-type for attestations |
| `--referrer` | `false` | Use OCI referrer API for pushing attestation |
| `--referrer-repository` | `registry.scout.docker.com` | Repository to push referrer to |
