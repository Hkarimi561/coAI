# Module ngx_stream_ssl_preread_module

 The `ngx_stream_ssl_preread_module` module (1.11.5) allows extracting information from the [ClientHello](https://datatracker.ietf.org/doc/html/rfc5246#section-7.4.1.2) message without terminating SSL/TLS, for example, the server name requested through [SNI](https://datatracker.ietf.org/doc/html/rfc6066#section-3) or protocols advertised in [ALPN](https://datatracker.ietf.org/doc/html/rfc7301). This module is not built by default, it should be enabled with the
`--with-stream_ssl_preread_module` configuration parameter. 

## Example Configuration

Selecting an upstream based on server name:

```
map $ssl_preread_server_name $name {
    backend.example.com      backend;
    default                  backend2;
}

upstream backend {
    server 192.168.0.1:12345;
    server 192.168.0.2:12345;
}

upstream backend2 {
    server 192.168.0.3:12345;
    server 192.168.0.4:12345;
}

server {
    listen      12346;
    proxy_pass  $name;
    ssl_preread on;
}
```

Selecting an upstream based on protocol:

```
map $ssl_preread_alpn_protocols $proxy {
    ~\bh2\b           127.0.0.1:8001;
    ~\bhttp/1.1\b     127.0.0.1:8002;
    ~\bxmpp-client\b  127.0.0.1:8003;
}

server {
    listen      9000;
    proxy_pass  $proxy;
    ssl_preread on;
}
```

Selecting an upstream based on SSL protocol version:

```
map $ssl_preread_protocol $upstream {
    ""        ssh.example.com:22;
    "TLSv1.2" new.example.com:443;
    default   tls.example.com:443;
}

# ssh and https on the same port
server {
    listen      192.168.0.1:443;
    proxy_pass  $upstream;
    ssl_preread on;
}
```

## Directives

### ssl_preread

**Syntax:** `ssl_preread on | off;`  
**Default:** `ssl_preread off;`  
**Context:** stream, server  

 Enables extracting information from the ClientHello message at the preread phase. 

## Embedded Variables

- **`$ssl_preread_protocol`** — the highest SSL protocol version supported by the client (1.15.2)
- **`$ssl_preread_server_name`** — server name requested through SNI
- **`$ssl_preread_alpn_protocols`** — list of protocols advertised by the client through ALPN (1.13.10). The values are separated by commas.
