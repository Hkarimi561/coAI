# docker mcp secret set

Set a secret in the local OS Keychain

## Usage

```console
docker mcp secret set key[=value]
```

## Description

Set a secret in the local OS Keychain

## Examples

### Pass the secret via STDIN

```console
echo my-secret-password > pwd.txt
cat pwd.txt | docker mcp secret set postgres_password
```
