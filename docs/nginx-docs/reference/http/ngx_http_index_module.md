# Module ngx_http_index_module

 The `ngx_http_index_module` module processes requests ending with the slash character (‘`/`’). Such requests can also be processed by the ngx_http_autoindex_module and ngx_http_random_index_module modules. 

## Example Configuration

```
location / {
    index index.$geo.html index.html;
}
```

## Directives

### index

**Syntax:** `index file ...;`  
**Default:** `index index.html;`  
**Context:** http, server, location  

Defines files that will be used as an index.
The *file* name can contain variables.
Files are checked in the specified order.
The last element of the list can be a file with an absolute path.
Example:

```
index index.$geo.html index.0.html /index.html;
```

It should be noted that using an index file causes an internal redirect,
and the request can be processed in a different location.
For example, with the following configuration:

```
location = / {
    index index.html;
}

location / {
    ...
}
```

a “`/`” request will actually be processed in the
second location as “`/index.html`”.
