# Module ngx_http_internal_redirect_module

 The `ngx_http_internal_redirect_module` module (1.23.4) allows making an internal redirect. In contrast to rewriting URIs, the redirection is made after checking request and connection processing limits, and access limits. 

 > **Note:** This module is available as part of our *(commercial subscription)* commercial subscription.   

## Example Configuration

```
limit_req_zone $jwt_claim_sub zone=jwt_sub:10m rate=1r/s;

server {
    location / {
        auth_jwt          "realm";
        auth_jwt_key_file key.jwk;

        internal_redirect @rate_limited;
    }

    location @rate_limited {
        internal;

        limit_req  zone=jwt_sub burst=10;
        proxy_pass http://backend;
    }
}
```

The example implements
[per-user](https://datatracker.ietf.org/doc/html/rfc7519#section-4.1.2)
rate limiting.
Implementation without internal_redirect
is vulnerable to DoS attacks by unsigned JWTs, as normally the
limit_req
check is performed
before
auth_jwt check.
Using internal_redirect
allows reordering these checks.

## Directives

### internal_redirect

**Syntax:** `internal_redirect uri;`  
**Default:** —  
**Context:** server, location  

 Sets the URI for internal redirection of the request. It is also possible to use a named location instead of the URI. The *uri* value can contain variables. If the *uri* value is empty, then the redirect will not be made.
