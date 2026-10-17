# docker import

Import the contents from a tarball to create a filesystem image

**Aliases:** `docker image import, docker import`

## Usage

```console
docker import [OPTIONS] file|URL|- [REPOSITORY[:TAG]]
```

## Description

Import the contents from a tarball to create a filesystem image

## Options

| Option | Default | Description |
|---|---|---|
| `--change, -c` |  | Apply Dockerfile instruction to the created image |
| `--message, -m` |  | Set commit message for imported image |
| `--platform` |  | Set platform if server is multi-platform capable |
