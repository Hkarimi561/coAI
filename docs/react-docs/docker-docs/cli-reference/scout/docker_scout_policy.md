# docker scout policy

Evaluate local Rego policies against an image and display the results (experimental)

## Usage

```console
docker scout policy [IMAGE | REPO]
```

## Description

The `docker scout policy` command evaluates policies against an image.
The image analysis is uploaded to Docker Scout where policies get evaluated.

The policy evaluation results may take a few minutes to become available.

## Subcommands

- `docker scout policy publish`

## Options

| Option | Default | Description |
|---|---|---|
| `--exit-code, -e` | `false` | Return exit code '2' if policies are not met, '0' otherwise |
| `--only-policy` | `[]` | Comma separated list of policies to evaluate |
| `--org` |  | Namespace of the Docker organization |
| `--output, -o` |  | Write the report to a file |
| `--platform` |  | Platform of image to evaluate policies against |
| `--policy-bundle` | `[]` | OCI reference of a policy bundle to evaluate (repeatable) |
| `--policy-config` |  | Path or http(s) URL to a JSON file configuring policy enablement and inputs |
| `--policy-dir` | `[]` | Path to a directory of local .rego policy files (repeatable) |
| `--policy-file` | `[]` | Path or http(s) URL to a .rego policy file (repeatable) |
| `--result-file` |  | Write the full Rego evaluation result (pass, violations, query bindings and OPA metrics) of each evaluated policy to a JSON file (useful when iterating on local --policy-file policies) |

## Examples

### Evaluate policies against an image and display the results

```console
$ docker scout policy dockerscoutpolicy/customers-api-service:0.0.1
```

### Evaluate policies against an image for a specific organization

```console
$ docker scout policy dockerscoutpolicy/customers-api-service:0.0.1 --org dockerscoutpolicy
```

### Evaluate policies against an image with a specific platform

```console
$ docker scout policy dockerscoutpolicy/customers-api-service:0.0.1 --platform linux/amd64
```

### Compare policy results for a repository in a specific environment

```console
$ docker scout policy dockerscoutpolicy/customers-api-service --to-env production
```
