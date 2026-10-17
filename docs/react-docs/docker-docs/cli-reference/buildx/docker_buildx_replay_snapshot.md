# docker buildx replay snapshot

Export replay inputs for a subject as a reusable materials store

## Usage

```console
docker buildx replay snapshot [OPTIONS] SUBJECT
```

## Description

Export replay inputs for a subject as a reusable materials store

## Options

| Option | Default | Description |
|---|---|---|
| `--dry-run` | `false` | Print a JSON plan of the snapshot without writing output |
| `--include-materials` | `true` | Include material content in the snapshot |
| `--materials` | `[]` | Materials store (repeatable; format: `provenance` \| `oci-layout://<path>[:<tag>]` \| `<absolute-path>` \| `<key>=<value>`) |
| `--network` |  | Network mode for RUN instructions (`default` \| `none`; defaults to the mode of the original build) |
| `--output, -o` | `[]` | Output destination (default: `-` — oci tar to stdout; bare `<path>` writes an oci-layout directory; `type=oci,dest=X[,tar=true\|false]`) |
| `--platform` | `[]` | Platform of the subject to replay (defaults to the only platform of the subject or the builder default platform) |
| `--progress` | `auto` | Set type of progress output (`auto` \| `plain` \| `tty` \| `quiet` \| `rawjson`) |
| `--secret` | `[]` | Secret to expose to the replayed build (format: `id=mysecret[,src=/local/secret]`) |
| `--ssh` | `[]` | SSH agent socket or keys to expose (format: `default\|<id>[=<socket>\|<key>[,<key>]]`) |
| `--builder` |  | Override the configured builder instance |
| `--debug, -D` | `false` | Enable debug logging |
