# docker mcp secret

Manage secrets in the local OS Keychain

## Description

Manage secrets in the local OS Keychain

## Subcommands

- `docker mcp secret ls`
- `docker mcp secret rm`
- `docker mcp secret set`

## Examples

### Pass the secret via STDIN

> echo my-secret-password > pwd.txt
> cat pwd.txt | docker mcp secret set POSTGRES_PASSWORD
