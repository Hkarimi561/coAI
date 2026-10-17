# Module ngx_http_empty_gif_module

 The `ngx_http_empty_gif_module` module emits single-pixel transparent GIF. 

## Example Configuration

```
location = /_.gif {
    empty_gif;
}
```

## Directives

### empty_gif

**Syntax:** `empty_gif ;`  
**Default:** —  
**Context:** location  

 Turns on module processing in a surrounding location.
