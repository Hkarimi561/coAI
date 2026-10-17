# Module ngx_http_autoindex_module

 The `ngx_http_autoindex_module` module processes requests ending with the slash character (‘`/`’) and produces a directory listing. Usually a request is passed to the `ngx_http_autoindex_module` module when the ngx_http_index_module module cannot find an index file. 

## Example Configuration

```
location / {
    autoindex on;
}
```

## Directives

### autoindex

**Syntax:** `autoindex on | off;`  
**Default:** `autoindex off;`  
**Context:** http, server, location  

 Enables or disables the directory listing output. 

### autoindex_exact_size

**Syntax:** `autoindex_exact_size on | off;`  
**Default:** `autoindex_exact_size on;`  
**Context:** http, server, location  

 For the HTML format, specifies whether exact file sizes should be output in the directory listing, or rather rounded to kilobytes, megabytes, and gigabytes. 

### autoindex_format

**Syntax:** `autoindex_format html | xml | json | jsonp;`  
**Default:** `autoindex_format html;`  
**Context:** http, server, location  
**Appeared in:** 1.7.9

 Sets the format of a directory listing. 

 When the JSONP format is used, the name of a callback function is set with the `callback` request argument. If the argument is missing or has an empty value, then the JSON format is used. 

 The XML output can be transformed using the ngx_http_xslt_module module. 

### autoindex_localtime

**Syntax:** `autoindex_localtime on | off;`  
**Default:** `autoindex_localtime off;`  
**Context:** http, server, location  

 For the HTML format, specifies whether times in the directory listing should be output in the local time zone or UTC.
