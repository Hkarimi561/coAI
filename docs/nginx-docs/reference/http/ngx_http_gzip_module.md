# Module ngx_http_gzip_module

 The `ngx_http_gzip_module` module is a filter that compresses responses using the “gzip” method. This often helps to reduce the size of transmitted data by half or even more. > **Note:** When using the SSL/TLS protocol, compressed responses may be subject to [BREACH](https://en.wikipedia.org/wiki/BREACH) attacks.   

## Example Configuration

```
gzip            on;
gzip_min_length 1000;
gzip_proxied    expired no-cache no-store private auth;
gzip_types      text/plain application/xml;
```

 The `$gzip_ratio` variable can be used to log the achieved compression ratio. 

## Directives

### gzip

**Syntax:** `gzip on | off;`  
**Default:** `gzip off;`  
**Context:** http, server, location, if in location  

 Enables or disables gzipping of responses. 

### gzip_buffers

**Syntax:** `gzip_buffers number size;`  
**Default:** `gzip_buffers 32 4k|16 8k;`  
**Context:** http, server, location  

 Sets the *number* and *size* of buffers used to compress a response. By default, the buffer size is equal to one memory page. This is either 4K or 8K, depending on a platform. > **Note:** Until version 0.7.28, four 4K or 8K buffers were used by default.   

### gzip_comp_level

**Syntax:** `gzip_comp_level level;`  
**Default:** `gzip_comp_level 1;`  
**Context:** http, server, location  

 Sets a gzip compression *level* of a response. Acceptable values are in the range from 1 to 9. 

### gzip_disable

**Syntax:** `gzip_disable regex ...;`  
**Default:** —  
**Context:** http, server, location  
**Appeared in:** 0.6.23

 Disables gzipping of responses for requests with
`User-Agent` header fields matching any of the specified regular expressions. 

 The special mask “`msie6`” (0.7.12) corresponds to the regular expression “`MSIE [4-6]\.`”, but works faster. Starting from version 0.8.11, “`MSIE 6.0; ... SV1`” is excluded from this mask. 

### gzip_http_version

**Syntax:** `gzip_http_version 1.0 | 1.1;`  
**Default:** `gzip_http_version 1.1;`  
**Context:** http, server, location  

 Sets the minimum HTTP version of a request required to compress a response. 

### gzip_min_length

**Syntax:** `gzip_min_length length;`  
**Default:** `gzip_min_length 20;`  
**Context:** http, server, location  

 Sets the minimum length of a response that will be gzipped. The length is determined only from the `Content-Length` response header field. 

### gzip_proxied

**Syntax:** `gzip_proxied off | expired | no-cache | no-store | private | no_last_modified | no_etag | auth | any ...;`  
**Default:** `gzip_proxied off;`  
**Context:** http, server, location  

Enables or disables gzipping of responses for proxied
requests depending on the request and response.
The fact that the request is proxied is determined by
the presence of the `Via` request header field.
The directive accepts multiple parameters:
- **`off`** — disables compression for all proxied requests, ignoring other parameters;
- **`expired`** — enables compression if a response header includes the
  `Expires` field with a value that disables caching;
- **`no-cache`** — enables compression if a response header includes the
  `Cache-Control` field with the “`no-cache`” parameter;
- **`no-store`** — enables compression if a response header includes the
  `Cache-Control` field with the “`no-store`” parameter;
- **`private`** — enables compression if a response header includes the
  `Cache-Control` field with the “`private`” parameter;
- **`no_last_modified`** — enables compression if a response header does not include the
  `Last-Modified` field;
- **`no_etag`** — enables compression if a response header does not include the
  `ETag` field;
- **`auth`** — enables compression if a request header includes the
  `Authorization` field;
- **`any`** — enables compression for all proxied requests.

### gzip_types

**Syntax:** `gzip_types mime-type ...;`  
**Default:** `gzip_types text/html;`  
**Context:** http, server, location  

 Enables gzipping of responses for the specified MIME types in addition to “`text/html`”. The special value “`*`” matches any MIME type (0.8.29). Responses with the “`text/html`” type are always compressed. 

### gzip_vary

**Syntax:** `gzip_vary on | off;`  
**Default:** `gzip_vary off;`  
**Context:** http, server, location  

 Enables or disables inserting the `Vary: Accept-Encoding` response header field if the directives gzip, gzip_static, or gunzip are active. 

## Embedded Variables

- **`$gzip_ratio`** — achieved compression ratio, computed as the ratio between the original and compressed response sizes.
