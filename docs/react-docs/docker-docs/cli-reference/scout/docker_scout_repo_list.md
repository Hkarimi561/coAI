# docker scout repo list

List Docker Scout repositories

## Usage

```console
docker scout repo list
```

## Description

The docker scout repo list command shows all repositories in an organization.

If ORG is not provided the default configured organization will be used.

## Options

| Option | Default | Description |
|---|---|---|
| `--filter` |  | Regular expression to filter repositories by name |
| `--only-disabled` | `false` | Filter to disabled repositories only |
| `--only-enabled` | `false` | Filter to enabled repositories only |
| `--only-registry` |  | Filter to a specific registry only: - hub.docker.com - ecr (AWS ECR) |
| `--org` |  | Namespace of the Docker organization |
