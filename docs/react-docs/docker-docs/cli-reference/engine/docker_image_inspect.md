# docker image inspect

Display detailed information on one or more images

## Usage

```console
docker image inspect [OPTIONS] IMAGE [IMAGE...]
```

## Description

Display detailed information on one or more images

## Options

| Option | Default | Description |
|---|---|---|
| `--format, -f` |  | Format output using a custom template: 'json': Print in JSON format 'TEMPLATE': Print output using the given Go template. Refer to https://docs.docker.com/go/formatting/ for more information about formatting output with templates |
| `--platform` |  | Inspect a specific platform of the multi-platform image. If the image or the server is not multi-platform capable, the command will error out if the platform does not match. 'os[/arch[/variant]]': Explicit platform (eg. linux/amd64) |
