# Module ngx_http_auth_request_module

 The `ngx_http_auth_request_module` module (1.5.4+) implements client authorization based on the result of a subrequest. If the subrequest returns a 2xx response code, the access is allowed. If it returns 401 or 403, the access is denied with the corresponding error code. Any other response code returned by the subrequest is considered an error. 

 For the 401 error, the client also receives the
`WWW-Authenticate` header from the subrequest response. 

 This module is not built by default, it should be enabled with the
`--with-http_auth_request_module` configuration parameter. 

 The module may be combined with other access modules, such as ngx_http_access_module, ngx_http_auth_basic_module, and ngx_http_auth_jwt_module, via the satisfy directive. > **Note:** Before version 1.7.3, responses to authorization subrequests could not be cached (using proxy_cache, proxy_store, etc.).   

## Example Configuration

```
location /private/ {
    auth_request /auth;
    ...
}

location = /auth {
    proxy_pass ...
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_set_header X-Original-URI $request_uri;
}
```

## Directives

### auth_request

**Syntax:** `auth_request uri | off;`  
**Default:** `auth_request off;`  
**Context:** http, server, location  

 Enables authorization based on the result of a subrequest and sets the URI to which the subrequest will be sent. 

### auth_request_set

**Syntax:** `auth_request_set $variable value;`  
**Default:** —  
**Context:** http, server, location  

 Sets the request *variable* to the given *value* after the authorization request completes. The value may contain variables from the authorization request, such as `$upstream_http_*`.
