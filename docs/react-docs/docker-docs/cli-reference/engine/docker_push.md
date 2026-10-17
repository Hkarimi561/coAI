# docker push

Upload an image to a registry

**Aliases:** `docker image push, docker push`

## Usage

```console
docker push [OPTIONS] NAME[:TAG]
```

## Description

Upload an image to a registry

## Options

| Option | Default | Description |
|---|---|---|
| `--all-tags, -a` | `false` | Push all tags of an image to the repository |
| `--platform` |  | Push a platform-specific manifest as a single-platform image to the registry. Image index won't be pushed, meaning that other manifests, including attestations won't be preserved. 'os[/arch[/variant]]': Explicit platform (eg. linux/amd64) |
| `--quiet, -q` | `false` | Suppress verbose output |
