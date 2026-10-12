"""Sample MCP server with read-only DevOps checks (streamable HTTP on port 9100).

Tools: dns_lookup, tcp_check, http_check, ssl_cert_expiry, current_time.
Run via docker compose (service `sample-mcp`), then add http://sample-mcp:9100/mcp in Admin -> MCP servers.
These tools only observe; they never change anything. They can reach whatever the container's network can reach.
"""

import asyncio
import socket
import ssl
import time
from datetime import UTC, datetime, timedelta, timezone

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("devops-tools", host="0.0.0.0", port=9100)


@mcp.tool()
async def dns_lookup(hostname: str) -> str:
    """Resolve a hostname to its IP addresses (A/AAAA)."""
    try:
        infos = await asyncio.get_running_loop().getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        return f"DNS lookup failed for {hostname}: {exc}"
    addrs = sorted({i[4][0] for i in infos})
    return f"{hostname} -> {', '.join(addrs)}"


@mcp.tool()
async def tcp_check(host: str, port: int, timeout_s: float = 3.0) -> str:
    """Check whether a TCP port accepts connections and how long the connect took."""
    t0 = time.monotonic()
    try:
        _, writer = await asyncio.wait_for(asyncio.open_connection(host, port), min(max(timeout_s, 0.5), 10))
    except (OSError, TimeoutError) as exc:
        return f"{host}:{port} is CLOSED or unreachable ({type(exc).__name__}: {exc}) after {int((time.monotonic() - t0) * 1000)} ms"
    writer.close()
    return f"{host}:{port} is OPEN (connect took {int((time.monotonic() - t0) * 1000)} ms)"


@mcp.tool()
async def http_check(url: str, timeout_s: float = 8.0) -> str:
    """Send an HTTP GET to a URL and report status code, redirects, latency and the Server header."""
    if not url.startswith(("http://", "https://")):
        return "URL must start with http:// or https://"
    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=min(max(timeout_s, 1), 20), verify=True) as client:
            r = await client.get(url)
    except httpx.HTTPError as exc:
        return f"Request to {url} failed: {type(exc).__name__}: {exc} (after {int((time.monotonic() - t0) * 1000)} ms)"
    return (
        f"{url} -> HTTP {r.status_code} in {int((time.monotonic() - t0) * 1000)} ms; "
        f"redirects: {len(r.history)}; final URL: {r.url}; server: {r.headers.get('server', 'n/a')}; "
        f"content-type: {r.headers.get('content-type', 'n/a')}; bytes: {len(r.content)}"
    )


@mcp.tool()
async def ssl_cert_expiry(host: str, port: int = 443) -> str:
    """Report the TLS certificate issuer, expiry date and days remaining for a host."""

    def fetch() -> dict:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=6) as sock, ctx.wrap_socket(sock, server_hostname=host) as tls:
            return tls.getpeercert()

    try:
        cert = await asyncio.to_thread(fetch)
    except (OSError, ssl.SSLError) as exc:
        return f"TLS check failed for {host}:{port}: {type(exc).__name__}: {exc}"
    expires = datetime.fromtimestamp(ssl.cert_time_to_seconds(cert["notAfter"]), UTC)
    days = (expires - datetime.now(UTC)).days
    issuer = ", ".join("=".join(x) for rdn in cert.get("issuer", ()) for x in rdn)
    return f"{host}:{port} certificate expires {expires:%Y-%m-%d} ({days} days left); issuer: {issuer}"


@mcp.tool()
def current_time(utc_offset_hours: float = 0.0) -> str:
    """Current date and time, optionally shifted by a UTC offset in hours (e.g. 3.5 for Tehran)."""
    now = datetime.now(timezone(timedelta(hours=utc_offset_hours)))
    return now.strftime("%Y-%m-%d %H:%M:%S %z")


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
