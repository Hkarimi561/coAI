# Module ngx_http_v2_module

 The `ngx_http_v2_module` module (1.9.5) provides support for [HTTP/2](https://datatracker.ietf.org/doc/html/rfc7540). 

 This module is not built by default, it should be enabled with the `--with-http_v2_module` configuration parameter. 

## Known Issues

 Before version 1.9.14, buffering of a client request body could not be disabled regardless of proxy_request_buffering, fastcgi_request_buffering, uwsgi_request_buffering, and scgi_request_buffering directive values. 

 Before version 1.19.1, the lingering_close mechanism was not used to control closing HTTP/2 connections. 

## Example Configuration

```
server {
    listen 443 ssl;

    http2 on;

    ssl_certificate server.crt;
    ssl_certificate_key server.key;
}
```

Note that accepting HTTP/2 connections over TLS requires
the “Application-Layer Protocol Negotiation” (ALPN) TLS extension
support, which is available since
[OpenSSL](http://www.openssl.org) version 1.0.2.

 Also note that if the ssl_prefer_server_ciphers directive is set to the value “`on`”, the ciphers should be configured to comply with [RFC 9113, Appendix A](https://datatracker.ietf.org/doc/html/rfc9113#appendix-A) black list and supported by clients. 

## Directives

### http2

**Syntax:** `http2 on | off;`  
**Default:** `http2 off;`  
**Context:** http, server  
**Appeared in:** 1.25.1

 Enables the [HTTP/2](https://datatracker.ietf.org/doc/html/rfc9113) protocol. 

### http2_body_preread_size

**Syntax:** `http2_body_preread_size size;`  
**Default:** `http2_body_preread_size 64k;`  
**Context:** http, server  
**Appeared in:** 1.11.0

 Sets the *size* of the buffer per each request in which the request body may be saved before it is started to be processed. 

### http2_chunk_size

**Syntax:** `http2_chunk_size size;`  
**Default:** `http2_chunk_size 8k;`  
**Context:** http, server, location  

 Sets the maximum size of chunks into which the response body is sliced. A too low value results in higher overhead. A too high value impairs prioritization due to [HOL blocking](http://en.wikipedia.org/wiki/Head-of-line_blocking). 

### http2_idle_timeout

**Syntax:** `http2_idle_timeout time;`  
**Default:** `http2_idle_timeout 3m;`  
**Context:** http, server  

 > **Note:** This directive is obsolete since version 1.19.7. The keepalive_timeout directive should be used instead.   

 Sets the timeout of inactivity after which the connection is closed. 

### http2_max_concurrent_pushes

**Syntax:** `http2_max_concurrent_pushes number;`  
**Default:** `http2_max_concurrent_pushes 10;`  
**Context:** http, server  
**Appeared in:** 1.13.9

 > **Note:** This directive is obsolete since version 1.25.1.   

 Limits the maximum number of concurrent push requests in a connection. 

### http2_max_concurrent_streams

**Syntax:** `http2_max_concurrent_streams number;`  
**Default:** `http2_max_concurrent_streams 128;`  
**Context:** http, server  

 Sets the maximum number of concurrent HTTP/2 streams in a connection. 

### http2_max_field_size

**Syntax:** `http2_max_field_size size;`  
**Default:** `http2_max_field_size 4k;`  
**Context:** http, server  

 > **Note:** This directive is obsolete since version 1.19.7. The large_client_header_buffers directive should be used instead.   

 Limits the maximum size of an [HPACK](https://datatracker.ietf.org/doc/html/rfc7541)-compressed request header field. The limit applies equally to both name and value. Note that if Huffman encoding is applied, the actual size of decompressed name and value strings may be larger. For most requests, the default limit should be enough. 

### http2_max_header_size

**Syntax:** `http2_max_header_size size;`  
**Default:** `http2_max_header_size 16k;`  
**Context:** http, server  

 > **Note:** This directive is obsolete since version 1.19.7. The large_client_header_buffers directive should be used instead.   

 Limits the maximum size of the entire request header list after [HPACK](https://datatracker.ietf.org/doc/html/rfc7541) decompression. For most requests, the default limit should be enough. 

### http2_max_requests

**Syntax:** `http2_max_requests number;`  
**Default:** `http2_max_requests 1000;`  
**Context:** http, server  
**Appeared in:** 1.11.6

 > **Note:** This directive is obsolete since version 1.19.7. The keepalive_requests directive should be used instead.   

 Sets the maximum number of requests (including push requests) that can be served through one HTTP/2 connection, after which the next client request will lead to connection closing and the need of establishing a new connection. 

 Closing connections periodically is necessary to free per-connection memory allocations. Therefore, using too high maximum number of requests could result in excessive memory usage and not recommended. 

### http2_push

**Syntax:** `http2_push uri | off;`  
**Default:** `http2_push off;`  
**Context:** http, server, location  
**Appeared in:** 1.13.9

 > **Note:** This directive is obsolete since version 1.25.1. The early_hints directive can be used instead.   

Pre-emptively sends
([pushes](https://datatracker.ietf.org/doc/html/rfc9113#section-8.4))
a request to the specified *uri*
along with the response to the original request.
Only relative URIs with absolute path will be processed,
for example:

```
http2_push /static/css/main.css;
```

The *uri* value can contain variables.

 Several `http2_push` directives can be specified on the same configuration level. The `off` parameter cancels the effect of the `http2_push` directives inherited from the previous configuration level. 

### http2_push_preload

**Syntax:** `http2_push_preload on | off;`  
**Default:** `http2_push_preload off;`  
**Context:** http, server, location  
**Appeared in:** 1.13.9

 > **Note:** This directive is obsolete since version 1.25.1.   

 Enables automatic conversion of [preload links](https://www.w3.org/TR/preload/#server-push-http-2) specified in the `Link` response header fields into [push](https://datatracker.ietf.org/doc/html/rfc9113#section-8.4) requests. 

### http2_recv_buffer_size

**Syntax:** `http2_recv_buffer_size size;`  
**Default:** `http2_recv_buffer_size 256k;`  
**Context:** http  

 Sets the size of the per worker input buffer. 

### http2_recv_timeout

**Syntax:** `http2_recv_timeout time;`  
**Default:** `http2_recv_timeout 30s;`  
**Context:** http, server  

 > **Note:** This directive is obsolete since version 1.19.7. The client_header_timeout directive should be used instead.   

 Sets the timeout for expecting more data from the client, after which the connection is closed. 

## Embedded Variables

The `ngx_http_v2_module` module
supports the following embedded variables:
- **`$http2`** — negotiated protocol identifier: “`h2`” for HTTP/2 over TLS, “`h2c`” for HTTP/2 over cleartext TCP, or an empty string otherwise.
