# Module ngx_http_slice_module

 The `ngx_http_slice_module` module (1.9.8) is a filter that splits a request into subrequests, each returning a certain range of response. The filter provides more effective caching of big responses. 

 This module is not built by default, it should be enabled with the
`--with-http_slice_module` configuration parameter. 

## Known Issues

 Currently, the module does not work as expected in subrequests such as background cache update. In this case, a request is constructed without byte-range support. 

## Example Configuration

```
location / {
    slice             1m;
    proxy_cache       cache;
    proxy_cache_key   $uri$is_args$args$slice_range;
    proxy_set_header  Range $slice_range;
    proxy_cache_valid 200 206 1h;
    proxy_pass        http://localhost:8000;
}
```

In this example,
the response is split into 1-megabyte cacheable slices.

## Directives

### slice

**Syntax:** `slice size;`  
**Default:** `slice 0;`  
**Context:** http, server, location  

 Sets the *size* of the slice. The zero value disables splitting responses into slices. Note that a too low value may result in excessive memory usage and opening a large number of files. 

 In order for a subrequest to return the required range, the `$slice_range` variable should be passed to the proxied server as the `Range` request header field. If caching is enabled, `$slice_range` should be added to the cache key and caching of responses with 206 status code should be enabled. 

## Embedded Variables

The `ngx_http_slice_module` module
supports the following embedded variables:
- **`$slice_range`** — the current slice range in [HTTP byte range](https://datatracker.ietf.org/doc/html/rfc7233#section-2.1) format, for example, `bytes=0-1048575`.
