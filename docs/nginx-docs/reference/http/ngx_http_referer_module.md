# Module ngx_http_referer_module

 The `ngx_http_referer_module` module is used to block access to a site for requests with invalid values in the
`Referer` header field. It should be kept in mind that fabricating a request with an appropriate
`Referer` field value is quite easy, and so the intended purpose of this module is not to block such requests thoroughly but to block the mass flow of requests sent by regular browsers. It should also be taken into consideration that regular browsers may not send the `Referer` field even for valid requests. 

## Example Configuration

```
valid_referers none blocked server_names
               *.example.com example.* www.example.org/galleries/
               ~\.google\.;

if ($invalid_referer) {
    return 403;
}
```

## Directives

### referer_hash_bucket_size

**Syntax:** `referer_hash_bucket_size size;`  
**Default:** `referer_hash_bucket_size 64;`  
**Context:** server, location  
**Appeared in:** 1.0.5

 Sets the bucket size for the valid referers hash tables. The details of setting up hash tables are provided in a separate document. 

### referer_hash_max_size

**Syntax:** `referer_hash_max_size size;`  
**Default:** `referer_hash_max_size 2048;`  
**Context:** server, location  
**Appeared in:** 1.0.5

 Sets the maximum *size* of the valid referers hash tables. The details of setting up hash tables are provided in a separate document. 

### valid_referers

**Syntax:** `valid_referers none | blocked | server_names | string ...;`  
**Default:** —  
**Context:** server, location  

 Specifies the `Referer` request header field values that will cause the embedded `$invalid_referer` variable to be set to an empty string. Otherwise, the variable will be set to “`1`”. Search for a match is case-insensitive. 

Parameters can be as follows:
- **`none`** — the `Referer` field is missing in the request header;
- **`blocked`** — the `Referer` field is present in the request header, but its value has been deleted by a firewall or proxy server; such values are strings that do not start with “`http://`” or “`https://`”;
- **`server_names`** — the `Referer` request header field contains one of the server names;
- **arbitrary string** — defines a server name and an optional URI prefix. A server name can have an “`*`” at the beginning or end. During the checking, the server’s port in the `Referer` field is ignored;
- **regular expression** — the first symbol should be a “`~`”. It should be noted that an expression will be matched against the text starting after the “`http://`” or “`https://`”.

Example:

```
valid_referers none blocked server_names
               *.example.com example.* www.example.org/galleries/
               ~\.google\.;
```

## Embedded Variables

- **`$invalid_referer`** — Empty string, if the `Referer` request header field value is considered valid, otherwise “`1`”.
