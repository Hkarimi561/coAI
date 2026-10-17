# Module ngx_stream_set_module

 The `ngx_stream_set_module` module (1.19.3) allows setting a value for a variable. 

## Example Configuration

```
server {
    listen 12345;
    set    $true 1;
}
```

## Directives

### set

**Syntax:** `set $variable value;`  
**Default:** —  
**Context:** server  

 Sets a *value* for the specified *variable*. The *value* can contain text, variables, and their combination.
