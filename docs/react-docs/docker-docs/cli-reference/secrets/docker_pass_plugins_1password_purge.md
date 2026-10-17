# docker pass plugins 1password purge

Disable the plugin and remove the stored 1Password service account token.

## Usage

```console
docker pass plugins 1password purge
```

## Description

Disable the `1password-sdk` plugin on the running secrets-engine daemon and remove the service account token from the local OS keychain.

After purge, the plugin no longer participates in secret resolution and the token is gone from local storage. Run `setup` again to re-enable it.
