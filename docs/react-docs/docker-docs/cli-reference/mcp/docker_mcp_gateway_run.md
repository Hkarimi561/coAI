# docker mcp gateway run

Run the gateway

## Usage

```console
docker mcp gateway run
```

## Description

Run the gateway

## Options

| Option | Default | Description |
|---|---|---|
| `--additional-catalog` | `[]` | Additional catalog paths to append to the default catalogs |
| `--additional-config` | `[]` | Additional config paths to merge with the default config.yaml |
| `--additional-registry` | `[]` | Additional registry paths to merge with the default registry.yaml |
| `--additional-tools-config` | `[]` | Additional tools paths to merge with the default tools.yaml |
| `--block-network` | `false` | Block tools from accessing forbidden network resources |
| `--block-secrets` | `true` | Block secrets from being/received sent to/from tools |
| `--catalog` | `[]` | Paths to docker catalogs (absolute or relative to ~/.docker/mcp/catalogs/) |
| `--config` | `[]` | Paths to the config files (absolute or relative to ~/.docker/mcp/) |
| `--cpus` | `1` | CPUs allocated to each MCP Server (default is 1) |
| `--debug-dns` | `false` | Debug DNS resolution |
| `--dry-run` | `false` | Start the gateway but do not listen for connections (useful for testing the configuration) |
| `--enable-all-servers` | `false` | Enable all servers in the catalog (instead of using individual --servers options) |
| `--interceptor` | `[]` | List of interceptors to use (format: when:type:path, e.g. 'before:exec:/bin/path') |
| `--log-calls` | `true` | Log calls to the tools |
| `--long-lived` | `false` | Containers are long-lived and will not be removed until the gateway is stopped, useful for stateful servers |
| `--mcp-registry` | `[]` | MCP registry URLs to fetch servers from (can be repeated) |
| `--memory` | `2Gb` | Memory allocated to each MCP Server (default is 2Gb) |
| `--oci-ref` | `[]` | OCI image references to use |
| `--port` | `0` | TCP port to listen on (default is to listen on stdio) |
| `--profile` |  | Profile ID to use (mutually exclusive with --servers and --enable-all-servers) |
| `--registry` | `[]` | Paths to the registry files (absolute or relative to ~/.docker/mcp/) |
| `--secrets` | `docker-desktop` | Colon separated paths to search for secrets. Can be `docker-desktop` or a path to a .env file (default to using Docker Desktop's secrets API) |
| `--servers` | `[]` | Names of the servers to enable (if non empty, ignore --registry flag) |
| `--static` | `false` | Enable static mode (aka pre-started servers) |
| `--tools` | `[]` | List of tools to enable |
| `--tools-config` | `[]` | Paths to the tools files (absolute or relative to ~/.docker/mcp/) |
| `--transport` | `stdio` | stdio, sse or streaming. Uses MCP_GATEWAY_AUTH_TOKEN environment variable for localhost authentication to prevent dns rebinding attacks. |
| `--verbose` | `false` | Verbose output |
| `--verify-signatures` | `false` | Verify signatures of the server images |
| `--watch` | `true` | Watch for changes and reconfigure the gateway |
