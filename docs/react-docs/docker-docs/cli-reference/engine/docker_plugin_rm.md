# docker plugin rm

Remove one or more plugins

**Aliases:** `docker plugin rm, docker plugin remove`

## Usage

```console
docker plugin rm [OPTIONS] PLUGIN [PLUGIN...]
```

## Description

Removes a plugin. You cannot remove a plugin if it is enabled, you must disable
a plugin using the [`docker plugin disable`](/reference/cli/docker/plugin/disable/) before removing
it, or use `--force`. Use of `--force` is not recommended, since it can affect
functioning of running containers using the plugin.

## Options

| Option | Default | Description |
|---|---|---|
| `--force, -f` | `false` | Force the removal of an active plugin |

## Examples

The following example disables and removes the `sample-volume-plugin:latest`
plugin:

```console
$ docker plugin disable tiborvass/sample-volume-plugin

tiborvass/sample-volume-plugin

$ docker plugin rm tiborvass/sample-volume-plugin:latest

tiborvass/sample-volume-plugin
```
