# Module ngx_http_random_index_module

 The `ngx_http_random_index_module` module processes requests ending with the slash character (‘`/`’) and picks a random file in a directory to serve as an index file. The module is processed before the ngx_http_index_module module. 

 This module is not built by default, it should be enabled with the
`--with-http_random_index_module` configuration parameter. 

## Example Configuration

```
location / {
    random_index on;
}
```

## Directives

### random_index

**Syntax:** `random_index on | off;`  
**Default:** `random_index off;`  
**Context:** location  

 Enables or disables module processing in a surrounding location.
