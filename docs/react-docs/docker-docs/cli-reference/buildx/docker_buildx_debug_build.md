# docker buildx debug build

Start a build

**Aliases:** `docker build, docker builder build, docker image build, docker buildx b`

## Usage

```console
docker buildx debug build [OPTIONS] PATH | URL | -
```

## Description

Start a build

## Options

| Option | Default | Description |
|---|---|---|
| `--add-host` | `[]` | Add a custom host-to-IP mapping (format: `host:ip`) |
| `--allow` | `[]` | Allow extra privileged entitlement (e.g., `network.host`, `security.insecure`, `device`, `buildx.local.delete`) |
| `--annotation` | `[]` | Add annotation to the image |
| `--attest` | `[]` | Attestation parameters (format: `type=sbom,generator=image`) |
| `--build-arg` | `[]` | Set build-time variables |
| `--build-context` | `[]` | Additional build contexts (e.g., name=path) |
| `--cache-from` | `[]` | External cache sources (e.g., `user/app:cache`, `type=local,src=path/to/dir`) |
| `--cache-to` | `[]` | Cache export destinations (e.g., `user/app:cache`, `type=local,dest=path/to/dir`) |
| `--call` | `build` | Set method for evaluating build (`check`, `outline`, `targets`) |
| `--cgroup-parent` |  | Set the parent cgroup for the `RUN` instructions during build |
| `--check` |  | Shorthand for `--call=check` |
| `--file, -f` |  | Name of the Dockerfile (default: `PATH/Dockerfile`) |
| `--iidfile` |  | Write the image ID to a file |
| `--label` | `[]` | Set metadata for an image |
| `--load` | `false` | Shorthand for `--output=type=docker` |
| `--metadata-file` |  | Write build result metadata to a file |
| `--network` | `default` | Set the networking mode for the `RUN` instructions during build |
| `--no-cache` | `false` | Do not use cache when building the image |
| `--no-cache-filter` | `[]` | Do not cache specified stages |
| `--output, -o` | `[]` | Output destination (format: `type=local,dest=path`) |
| `--platform` | `[]` | Set target platform for build |
| `--policy` | `[]` | Policy configuration (format: `filename=path[,filename=path][,reset=true\|false][,disabled=true\|false][,strict=true\|false][,log-level=level]`) |
| `--progress` | `auto` | Set type of progress output (`auto`, `none`, `plain`, `quiet`, `rawjson`, `tty`). Use plain to show container output |
| `--provenance` |  | Shorthand for `--attest=type=provenance` |
| `--pull` | `false` | Always attempt to pull all referenced images |
| `--push` | `false` | Shorthand for `--output=type=registry,unpack=false` |
| `--quiet, -q` | `false` | Suppress the build output and print image ID on success |
| `--resource` | `[]` | Resource limits for build containers (format: `memory=2g`, `cpu-quota=50000`) |
| `--sbom` |  | Shorthand for `--attest=type=sbom` |
| `--secret` | `[]` | Secret to expose to the build (format: `id=mysecret[,src=/local/secret]`) |
| `--shm-size` | `0` | Shared memory size for build containers |
| `--ssh` | `[]` | SSH agent socket or keys to expose to the build (format: `default\|<id>[=<socket>\|<key>[,<key>]]`) |
| `--tag, -t` | `[]` | Image identifier (format: `[registry/]repository[:tag]`) |
| `--target` |  | Set the target build stage to build |
| `--ulimit` | `[]` | Ulimit options |
| `--builder` |  | Override the configured builder instance |
| `--debug, -D` | `false` | Enable debug logging |
