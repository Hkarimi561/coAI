# Module ngx_mail_ssl_module

 The `ngx_mail_ssl_module` module provides the necessary support for a mail proxy server to work with the SSL/TLS protocol. 

 This module is not built by default, it should be enabled with the
`--with-mail_ssl_module` configuration parameter. > **Note:** This module requires the [OpenSSL](http://www.openssl.org) library.   

## Example Configuration

To reduce the processor load, it is recommended to
- set the number of worker processes equal to the number of processors,
- enable the shared session cache,
- disable the built-in session cache,
- and possibly increase the session lifetime (by default, 5 minutes):

```
worker_processes auto;

mail {

    ...

    server {
        listen              993 ssl;

        ssl_protocols       TLSv1.2 TLSv1.3;
        ssl_ciphers         AES128-SHA:AES256-SHA:RC4-SHA:DES-CBC3-SHA:RC4-MD5;
        ssl_certificate     /usr/local/nginx/conf/cert.pem;
        ssl_certificate_key /usr/local/nginx/conf/cert.key;
        ssl_session_cache   shared:SSL:10m;
        ssl_session_timeout 10m;

        ...
    }
```

## Directives

### ssl

**Syntax:** `ssl on | off;`  
**Default:** `ssl off;`  
**Context:** mail, server  

 This directive was made obsolete in version 1.15.0 and was removed in version 1.25.1. The `ssl` parameter of the listen directive should be used instead. 

### ssl_certificate

**Syntax:** `ssl_certificate file;`  
**Default:** —  
**Context:** mail, server  

 Specifies a *file* with the certificate in the PEM format for the given server. If intermediate certificates should be specified in addition to a primary certificate, they should be specified in the same file in the following order: the primary certificate comes first, then the intermediate certificates. A secret key in the PEM format may be placed in the same file. 

Since version 1.11.0,
this directive can be specified multiple times
to load certificates of different types, for example, RSA and ECDSA:

```
server {
    listen              993 ssl;

    ssl_certificate     example.com.rsa.crt;
    ssl_certificate_key example.com.rsa.key;

    ssl_certificate     example.com.ecdsa.crt;
    ssl_certificate_key example.com.ecdsa.key;

    ...
}
```

> **Note:** Only OpenSSL 1.0.2 or higher supports separate certificate chains for different certificates. With older versions, only one certificate chain can be used.

 The value
`data`:*certificate* can be specified instead of the *file* (1.15.10), which loads a certificate without using intermediate files. Note that inappropriate use of this syntax may have its security implications, such as writing secret key data to error log. 

### ssl_certificate_compression

**Syntax:** `ssl_certificate_compression on | off;`  
**Default:** `ssl_certificate_compression off;`  
**Context:** mail, server  
**Appeared in:** 1.29.1

 Enables TLS 1.3 [compression](https://datatracker.ietf.org/doc/html/rfc8879) of server certificates. > **Note:** The directive is supported when using OpenSSL 3.2 or higher; the list of supported compression algorithms is provided by the library.   > **Note:** The directive is supported when using BoringSSL; the list of supported compression algorithms includes > `zlib` (1.29.3).   

### ssl_certificate_key

**Syntax:** `ssl_certificate_key file;`  
**Default:** —  
**Context:** mail, server  

 Specifies a *file* with the secret key in the PEM format for the given server. 

 The value
`engine`:*name*:*id* can be specified instead of the *file* (1.7.9), which loads a secret key with a specified *id* from the OpenSSL engine *name*. 

 The value
`store`:*scheme*:*id* can be specified instead of the *file* (1.29.0), which is used to load a secret key with a specified *id* and OpenSSL provider registered URI *scheme*, such as [`pkcs11`](https://datatracker.ietf.org/doc/html/rfc7512). 

 The value
`data`:*key* can be specified instead of the *file* (1.15.10), which loads a secret key without using intermediate files. Note that inappropriate use of this syntax may have its security implications, such as writing secret key data to error log. 

### ssl_ciphers

**Syntax:** `ssl_ciphers ciphers;`  
**Default:** `ssl_ciphers HIGH:!aNULL:!MD5;`  
**Context:** mail, server  

Specifies the enabled ciphers.
The ciphers are specified in the format understood by the
OpenSSL library, for example:

```
ssl_ciphers ALL:!aNULL:!EXPORT56:RC4+RSA:+HIGH:+MEDIUM:+LOW:+SSLv2:+EXP;
```

 The full list can be viewed using the “`openssl ciphers`” command. 

 > **Note:** The previous versions of nginx used different ciphers by default.   

### ssl_client_certificate

**Syntax:** `ssl_client_certificate file;`  
**Default:** —  
**Context:** mail, server  
**Appeared in:** 1.7.11

 Specifies a *file* with trusted CA certificates in the PEM format used to verify client certificates. 

 The list of certificates will be sent to clients. If this is not desired, the ssl_trusted_certificate directive can be used. 

### ssl_conf_command

**Syntax:** `ssl_conf_command name value;`  
**Default:** —  
**Context:** mail, server  
**Appeared in:** 1.19.4

 Sets arbitrary OpenSSL configuration [commands](https://www.openssl.org/docs/man1.1.1/man3/SSL_CONF_cmd.html). > **Note:** The directive is supported when using OpenSSL 1.0.2 or higher.   

Several `ssl_conf_command` directives
can be specified on the same level:

```
ssl_conf_command Options PrioritizeChaCha;
ssl_conf_command Ciphersuites TLS_CHACHA20_POLY1305_SHA256;
```

These directives are inherited from the previous configuration level
if and only if there are no `ssl_conf_command` directives
defined on the current level.

 > **Note:** Note that configuring OpenSSL directly might result in unexpected behavior.   

### ssl_crl

**Syntax:** `ssl_crl file;`  
**Default:** —  
**Context:** mail, server  
**Appeared in:** 1.7.11

 Specifies a *file* with revoked certificates (CRL) in the PEM format used to verify client certificates. When using intermediate certificates, their CRLs should be specified in the same file. 

### ssl_dhparam

**Syntax:** `ssl_dhparam file;`  
**Default:** —  
**Context:** mail, server  
**Appeared in:** 0.7.2

 Specifies a *file* with DH parameters for DHE ciphers. 

 By default no parameters are set, and therefore DHE ciphers will not be used. > **Note:** Prior to version 1.11.0, builtin parameters were used by default.   

### ssl_ecdh_curve

**Syntax:** `ssl_ecdh_curve curve;`  
**Default:** `ssl_ecdh_curve auto;`  
**Context:** mail, server  
**Appeared in:** 1.1.0

 Specifies a *curve* for ECDHE ciphers. 

When using OpenSSL 1.0.2 or higher,
it is possible to specify multiple curves (1.11.0), for example:

```
ssl_ecdh_curve prime256v1:secp384r1;
```

 The special value `auto` (1.11.0) instructs nginx to use a list built into the OpenSSL library when using OpenSSL 1.0.2 or higher, or `prime256v1` with older versions. 

 > **Note:** Prior to version 1.11.0, the `prime256v1` curve was used by default.   

 > **Note:** When using OpenSSL 1.0.2 or higher, this directive sets the list of curves supported by the server. Thus, in order for ECDSA certificates to work, it is important to include the curves used in the certificates.   

### ssl_password_file

**Syntax:** `ssl_password_file file;`  
**Default:** —  
**Context:** mail, server  
**Appeared in:** 1.7.3

 Specifies a *file* with passphrases for secret keys where each passphrase is specified on a separate line. Passphrases are tried in turn when loading the key. 

Example:

```
mail {
    ssl_password_file /etc/keys/global.pass;
    ...

    server {
        server_name mail1.example.com;
        ssl_certificate_key /etc/keys/first.key;
    }

    server {
        server_name mail2.example.com;

        # named pipe can also be used instead of a file
        ssl_password_file /etc/keys/fifo;
        ssl_certificate_key /etc/keys/second.key;
    }
}
```

### ssl_prefer_server_ciphers

**Syntax:** `ssl_prefer_server_ciphers on | off;`  
**Default:** `ssl_prefer_server_ciphers off;`  
**Context:** mail, server  

 Specifies that server ciphers should be preferred over client ciphers when the SSLv3 and TLS protocols are used. 

### ssl_protocols

**Syntax:** `ssl_protocols [SSLv2] [SSLv3] [TLSv1] [TLSv1.1] [TLSv1.2] [TLSv1.3];`  
**Default:** `ssl_protocols TLSv1.2 TLSv1.3;`  
**Context:** mail, server  

 Enables the specified protocols. > **Note:** The `TLSv1.1` and `TLSv1.2` parameters (1.1.13, 1.0.12) work only when OpenSSL 1.0.1 or higher is used.   > **Note:** The `TLSv1.3` parameter (1.13.0) works only when OpenSSL 1.1.1 or higher is used.   > **Note:** The `TLSv1.3` parameter is used by default since 1.23.4.   

### ssl_session_cache

**Syntax:** `ssl_session_cache off | none | [builtin[:size]] [shared:name:size];`  
**Default:** `ssl_session_cache none;`  
**Context:** mail, server  

Sets the types and sizes of caches that store session parameters.
A cache can be of any of the following types:
- **`off`** — the use of a session cache is strictly prohibited: nginx explicitly tells a client that sessions may not be reused.
- **`none`** — the use of a session cache is gently disallowed: nginx tells a client that sessions may be reused, but does not actually store session parameters in the cache.
- **`builtin`** — a cache built in OpenSSL; used by one worker process only. The cache size is specified in sessions. If size is not given, it is equal to 20480 sessions. Use of the built-in cache can cause memory fragmentation.
- **`shared`** — a cache shared between all worker processes. The cache size is specified in bytes; one megabyte can store about 4000 sessions. Each shared cache should have an arbitrary name. A cache with the same name can be used in several servers. It is also used to automatically generate, store, and periodically rotate TLS session ticket keys (1.23.2) unless configured explicitly using the ssl_session_ticket_key directive.

Both cache types can be used simultaneously, for example:

```
ssl_session_cache builtin:1000 shared:SSL:10m;
```

but using only shared cache without the built-in cache should
be more efficient.

### ssl_session_ticket_key

**Syntax:** `ssl_session_ticket_key file;`  
**Default:** —  
**Context:** mail, server  
**Appeared in:** 1.5.7

 Sets a *file* with the secret key used to encrypt and decrypt TLS session tickets. The directive is necessary if the same key has to be shared between multiple servers. By default, a randomly generated key is used. 

If several keys are specified, only the first key is
used to encrypt TLS session tickets.
This allows configuring key rotation, for example:

```
ssl_session_ticket_key current.key;
ssl_session_ticket_key previous.key;
```

The *file* must contain 80 or 48 bytes
of random data and can be created using the following command:

```
openssl rand 80 > ticket.key
```

Depending on the file size either AES256 (for 80-byte keys, 1.11.8)
or AES128 (for 48-byte keys) is used for encryption.

### ssl_session_tickets

**Syntax:** `ssl_session_tickets on | off;`  
**Default:** `ssl_session_tickets on;`  
**Context:** mail, server  
**Appeared in:** 1.5.9

 Enables or disables session resumption through [TLS session tickets](https://datatracker.ietf.org/doc/html/rfc5077). 

### ssl_session_timeout

**Syntax:** `ssl_session_timeout time;`  
**Default:** `ssl_session_timeout 5m;`  
**Context:** mail, server  

 Specifies a time during which a client may reuse the session parameters. 

### ssl_trusted_certificate

**Syntax:** `ssl_trusted_certificate file;`  
**Default:** —  
**Context:** mail, server  
**Appeared in:** 1.7.11

 Specifies a *file* with trusted CA certificates in the PEM format used to verify client certificates. 

 In contrast to the certificate set by ssl_client_certificate, the list of these certificates will not be sent to clients. 

### ssl_verify_client

**Syntax:** `ssl_verify_client on | off | optional | optional_no_ca;`  
**Default:** `ssl_verify_client off;`  
**Context:** mail, server  
**Appeared in:** 1.7.11

 Enables verification of client certificates. The verification result is passed in the
`Auth-SSL-Verify` header of the authentication request. 

 The `optional` parameter requests the client certificate and verifies it if the certificate is present. 

 The `optional_no_ca` parameter requests the client certificate but does not require it to be signed by a trusted CA certificate. This is intended for the use in cases when a service that is external to nginx performs the actual certificate verification. The contents of the certificate is accessible through requests sent to the authentication server. 

### ssl_verify_depth

**Syntax:** `ssl_verify_depth number;`  
**Default:** `ssl_verify_depth 1;`  
**Context:** mail, server  
**Appeared in:** 1.7.11

 Sets the verification depth in the client certificates chain. 

### starttls

**Syntax:** `starttls on | off | only;`  
**Default:** `starttls off;`  
**Context:** mail, server  

- **`on`** — allow usage of the `STLS` command for the POP3 and the `STARTTLS` command for the IMAP and SMTP;
- **`off`** — deny usage of the `STLS` and `STARTTLS` commands;
- **`only`** — require preliminary TLS transition.
