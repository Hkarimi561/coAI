# docker mcp server init

Initialize a new MCP server project

## Usage

```console
docker mcp server init <directory>
```

## Description

Initialize a new MCP server project in the specified directory with boilerplate code, Dockerfile, and compose.yaml

## Options

| Option | Default | Description |
|---|---|---|
| `--language` | `go` | Programming language for the server (currently only 'go' is supported) |
| `--template` | `basic` | Template to use (basic, chatgpt-app-basic) |
