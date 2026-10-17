# docker buildx replay verify

Replay a subject and compare the result against the original artifact

## Usage

```console
docker buildx replay verify [OPTIONS] SUBJECT
```

## Description

Replay a subject and compare the result against the original artifact

## Options

| Option | Default | Description |
|---|---|---|
| `--compare` | `digest` | Comparison mode (`digest` \| `artifact`) |
| `--materials` | `[]` | Materials store (repeatable; format: `provenance` \| `oci-layout://<path>[:<tag>]` \| `<absolute-path>` \| `<key>=<value>`) |
| `--network` |  | Network mode for RUN instructions (`default` \| `none`; defaults to the mode of the original build) |
| `--output, -o` | `[]` | Output destination for the verification result (VSA) (format: `type=local,dest=path`) |
| `--platform` | `[]` | Platform of the subject to replay (defaults to the only platform of the subject or the builder default platform) |
| `--progress` | `auto` | Set type of progress output (`auto` \| `plain` \| `tty` \| `quiet` \| `rawjson`) |
| `--secret` | `[]` | Secret to expose to the replayed build (format: `id=mysecret[,src=/local/secret]`) |
| `--ssh` | `[]` | SSH agent socket or keys to expose (format: `default\|<id>[=<socket>\|<key>[,<key>]]`) |
| `--builder` |  | Override the configured builder instance |
| `--debug, -D` | `false` | Enable debug logging |
