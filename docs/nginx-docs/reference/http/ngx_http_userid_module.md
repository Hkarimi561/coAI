# Module ngx_http_userid_module

 The `ngx_http_userid_module` module sets cookies suitable for client identification. Received and set cookies can be logged using the embedded variables $uid_got and $uid_set. This module is compatible with the [mod_uid](http://www.lexa.ru/programs/mod-uid-eng.html) module for Apache. 

## Example Configuration

```
userid         on;
userid_name    uid;
userid_domain  example.com;
userid_path    /;
userid_expires 365d;
userid_p3p     'policyref="/w3c/p3p.xml", CP="CUR ADM OUR NOR STA NID"';
```

## Directives

### userid

**Syntax:** `userid on | v1 | log | off;`  
**Default:** `userid off;`  
**Context:** http, server, location  

Enables or disables setting cookies and logging the received cookies:
- **`on`** — enables the setting of version 2 cookies and logging of the received cookies;
- **`v1`** — enables the setting of version 1 cookies and logging of the received cookies;
- **`log`** — disables the setting of cookies, but enables logging of the received cookies;
- **`off`** — disables the setting of cookies and logging of the received cookies.

### userid_domain

**Syntax:** `userid_domain name | none;`  
**Default:** `userid_domain none;`  
**Context:** http, server, location  

 Defines a domain for which the cookie is set. The `none` parameter disables setting of a domain for the cookie. 

### userid_expires

**Syntax:** `userid_expires time | max | off;`  
**Default:** `userid_expires off;`  
**Context:** http, server, location  

 Sets a time during which a browser should keep the cookie. The parameter `max` will cause the cookie to expire on “`31 Dec 2037 23:55:55 GMT`”. The parameter `off` will cause the cookie to expire at the end of a browser session. 

### userid_flags

**Syntax:** `userid_flags off | flag ...;`  
**Default:** `userid_flags off;`  
**Context:** http, server, location  
**Appeared in:** 1.19.3

 If the parameter is not `off`, defines one or more additional flags for the cookie:
`secure`,
`httponly`,
`samesite=strict`,
`samesite=lax`,
`samesite=none`. 

### userid_mark

**Syntax:** `userid_mark letter | digit | = | off;`  
**Default:** `userid_mark off;`  
**Context:** http, server, location  

 If the parameter is not `off`, enables the cookie marking mechanism and sets the character used as a mark. This mechanism is used to add or change userid_p3p and/or a cookie expiration time while preserving the client identifier. A mark can be any letter of the English alphabet (case-sensitive), digit, or the “`=`” character. 

 If the mark is set, it is compared with the first padding symbol in the base64 representation of the client identifier passed in a cookie. If they do not match, the cookie is resent with the specified mark, expiration time, and `P3P` header. 

### userid_name

**Syntax:** `userid_name name;`  
**Default:** `userid_name uid;`  
**Context:** http, server, location  

 Sets the cookie name. 

### userid_p3p

**Syntax:** `userid_p3p string | none;`  
**Default:** `userid_p3p none;`  
**Context:** http, server, location  

 Sets a value for the `P3P` header field that will be sent along with the cookie. If the directive is set to the special value `none`, the `P3P` header will not be sent in a response. 

### userid_path

**Syntax:** `userid_path path;`  
**Default:** `userid_path /;`  
**Context:** http, server, location  

 Defines a path for which the cookie is set. 

### userid_service

**Syntax:** `userid_service number;`  
**Default:** `userid_service IP address of the server;`  
**Context:** http, server, location  

 If identifiers are issued by multiple servers (services), each service should be assigned its own *number* to ensure that client identifiers are unique. For version 1 cookies, the default value is zero. For version 2 cookies, the default value is the number composed from the last four octets of the server’s IP address. 

## Embedded Variables

The `ngx_http_userid_module` module
supports the following embedded variables:
- **`$uid_got`** — The cookie name and received client identifier.
- **`$uid_reset`** — If the variable is set to a non-empty string that is not “`0`”, the client identifiers are reset. The special value “`log`” additionally leads to the output of messages about the reset identifiers to the error_log.
- **`$uid_set`** — The cookie name and sent client identifier.
