# docker scout push

Push an image or image index to Docker Scout

## Usage

```console
docker scout push IMAGE
```

## Description

The `docker scout push` command lets you push an image or analysis result to Docker Scout.

## Options

| Option | Default | Description |
|---|---|---|
| `--author` |  | Name of the author of the image |
| `--dry-run` | `false` | Do not push the image but process it |
| `--org` |  | Namespace of the Docker organization to which image will be pushed |
| `--output, -o` |  | Write the report to a file |
| `--platform` |  | Platform of image to be pushed |
| `--sbom` | `false` | Create and upload SBOMs |
| `--secrets` | `false` | Scan for secrets in the image |
| `--timestamp` |  | Timestamp of image or tag creation |

## Examples

### Push an image to Docker Scout

```console
$ docker scout push --org my-org registry.example.com/repo:tag
```
