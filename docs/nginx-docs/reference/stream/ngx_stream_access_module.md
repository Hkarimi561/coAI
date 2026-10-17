# Module ngx_stream_access_module

 The `ngx_stream_access_module` module (1.9.2) allows limiting access to certain client addresses. 

## Example Configuration

```
server {
    ...
    deny  192.168.1.1;
    allow 192.168.1.0/24;
    allow 10.1.1.0/16;
    allow 2001:0db8::/32;
    deny  all;
}
```

 The rules are checked in sequence until the first match is found. In this example, access is allowed only for IPv4 networks
`10.1.1.0/16` and `192.168.1.0/24` excluding the address `192.168.1.1`, and for IPv6 network `2001:0db8::/32`. 

## Directives

### allow

**Syntax:** `allow address | CIDR | unix: | all;`  
**Default:** —  
**Context:** stream, server  

 Allows access for the specified network or address. If the special value `unix:` is specified, allows access for all UNIX-domain sockets. 

### deny

**Syntax:** `deny address | CIDR | unix: | all;`  
**Default:** —  
**Context:** stream, server  

 Denies access for the specified network or address. If the special value `unix:` is specified, denies access for all UNIX-domain sockets.
