# Module ngx_http_v3_module

 The `ngx_http_v3_module` module (1.25.0) provides experimental support for [HTTP/3](https://datatracker.ietf.org/doc/html/rfc9114). 

 This module is not built by default, it should be enabled with the
`--with-http_v3_module` configuration parameter. > **Note:** This module requires the [OpenSSL](http://www.openssl.org) library version 1.1.1 or higher.   > **Note:** 0-RTT support requires the [OpenSSL](http://www.openssl.org) library version 3.5.1 or higher. Alternatively, [BoringSSL](https://boringssl.googlesource.com/boringssl), [LibreSSL](https://www.libressl.org), or [QuicTLS](https://github.com/quictls/openssl) libraries can be used to build and run this module.   

## Known Issues

 The module is experimental, caveat emptor applies. 

 Before version 1.29.1, 0-RTT support could not be enabled with OpenSSL regardless of the ssl_early_data directive value. 

 The module cannot be built on the Win32 platform. 

## Example Configuration

```
http {
    log_format quic '$remote_addr - $remote_user [$time_local] '
                    '"$request" $status $body_bytes_sent '
                    '"$http_referer" "$http_user_agent" "$http3"';

    access_log logs/access.log quic;

    server {
        # for better compatibility it's recommended
        # to use the same port for http/3 and https
        listen 8443 quic reuseport;
        listen 8443 ssl;

        ssl_certificate     certs/example.com.crt;
        ssl_certificate_key certs/example.com.key;

        location / {
            # used to advertise the availability of HTTP/3
            add_header Alt-Svc 'h3=":8443"; ma=86400';
        }
    }
}
```

## Directives

### http3

**Syntax:** `http3 on | off;`  
**Default:** `http3 on;`  
**Context:** http, server  

 Enables [HTTP/3](https://datatracker.ietf.org/doc/html/rfc9114) protocol negotiation. 

### http3_hq

**Syntax:** `http3_hq on | off;`  
**Default:** `http3_hq off;`  
**Context:** http, server  

 Enables HTTP/0.9 protocol negotiation used in [QUIC interoperability tests](https://github.com/marten-seemann/quic-interop-runner). 

### http3_max_concurrent_streams

**Syntax:** `http3_max_concurrent_streams number;`  
**Default:** `http3_max_concurrent_streams 128;`  
**Context:** http, server  

 Sets the maximum number of concurrent HTTP/3 request streams in a connection. 

### http3_stream_buffer_size

**Syntax:** `http3_stream_buffer_size size;`  
**Default:** `http3_stream_buffer_size 64k;`  
**Context:** http, server  

 Sets the size of the buffer used for reading and writing of the QUIC streams. 

### quic_active_connection_id_limit

**Syntax:** `quic_active_connection_id_limit number;`  
**Default:** `quic_active_connection_id_limit 2;`  
**Context:** http, server  

 Sets the QUIC `active_connection_id_limit` transport parameter value. This is the maximum number of client connection IDs which can be stored on the server. 

### quic_bpf

**Syntax:** `quic_bpf on | off;`  
**Default:** `quic_bpf off;`  
**Context:** main  

 Enables routing of QUIC packets using [eBPF](https://ebpf.io/). When enabled, this allows supporting QUIC connection migration. 

 > **Note:** The directive is only supported on Linux 5.7+.   

### quic_gso

**Syntax:** `quic_gso on | off;`  
**Default:** `quic_gso off;`  
**Context:** http, server  

 Enables sending in optimized batch mode using segmentation offloading. 

 > **Note:** Optimized sending is supported only on Linux featuring `UDP_SEGMENT`.   

### quic_host_key

**Syntax:** `quic_host_key file;`  
**Default:** —  
**Context:** http, server  

 Sets a *file* with the secret key used to encrypt stateless reset and address validation tokens. By default, a random key is generated on each reload. Tokens generated with old keys are not accepted. 

### quic_retry

**Syntax:** `quic_retry on | off;`  
**Default:** `quic_retry off;`  
**Context:** http, server  

 Enables the [QUIC Address Validation](https://datatracker.ietf.org/doc/html/rfc9000#name-address-validation) feature. This includes sending a new token in a `Retry` packet or a `NEW_TOKEN` frame and validating a token received in the `Initial` packet. 

## Embedded Variables

The `ngx_http_v3_module` module
supports the following embedded variables:
- **`$http3`** — negotiated protocol identifier: “`h3`” for HTTP/3 connections, “`hq`” for hq connections, or an empty string otherwise.
