# docker mcp profile server remove

Remove MCP servers from a profile

**Aliases:** `docker mcp profile server remove, docker mcp profile server rm`

## Usage

```console
docker mcp profile server remove <profile-id> --name <name1> --name <name2> ...
```

## Description

Remove MCP servers from a profile by server name.

## Options

| Option | Default | Description |
|---|---|---|
| `--name` | `[]` | Server name to remove (can be specified multiple times) |

## Examples

# Remove servers by name
  docker mcp profile server remove dev-tools --name github --name slack

  # Remove a single server
  docker mcp profile server remove dev-tools --name github
