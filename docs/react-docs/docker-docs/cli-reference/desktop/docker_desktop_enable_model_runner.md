# docker desktop enable model-runner

Manage Docker Model Runner settings

## Usage

```console
docker desktop enable model-runner [OPTIONS]
```

## Description

Enable and manage Docker Model Runner settings used by 'docker model'

## Options

| Option | Default | Description |
|---|---|---|
| `--no-tcp` | `false` | Disable TCP connection. Cannot be used with --tcp. |
| `--tcp` | `12434` | Enable or change TCP port for connection (1-65535). Cannot be used with --no-tcp. |
| `--cors` | `all` | CORS configuration. Can be `all`, `none`, or comma-separated list of allowed origins. |
| `--gpu` | `false` | Enable GPU support for Model Runner (Windows only). |
