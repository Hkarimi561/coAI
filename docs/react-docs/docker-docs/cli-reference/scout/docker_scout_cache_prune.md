# docker scout cache prune

Remove temporary or cached data

## Usage

```console
docker scout cache prune
```

## Description

The `docker scout cache prune` command removes temporary data and SBOM cache.

By default, `docker scout cache prune` only deletes temporary data.
To delete temporary data and clear the SBOM cache, use the `--sboms` flag.

## Options

| Option | Default | Description |
|---|---|---|
| `--force, -f` | `false` | Do not prompt for confirmation |
| `--sboms` | `false` | Prune cached SBOMs |

## Examples

### Delete temporary data

```console
$ docker scout cache prune
? Are you sure to delete all temporary data? Yes
    ✓ temporary data deleted
```

### Delete temporary and cache data

```console
$ docker scout cache prune --sboms
? Are you sure to delete all temporary data and all cached SBOMs? Yes
    ✓ temporary data deleted
    ✓ cached SBOMs deleted
```
