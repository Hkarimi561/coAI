# docker mcp catalog rm

Remove a catalog

## Usage

```console
docker mcp catalog rm <name>
```

## Description

Remove a locally configured catalog. This will delete the catalog and all its server definitions.
The Docker official catalog cannot be removed.

## Examples

# Remove a catalog
  docker mcp catalog rm old-servers
