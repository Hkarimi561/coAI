# Module ngx_http_tunnel_module

 The `ngx_http_tunnel_module` (1.31.0) handles HTTP/1.1 [CONNECT](https://datatracker.ietf.org/doc/html/rfc9110#section-9.3.6) requests and establishes an end-to-end virtual connection. 

## Example Configuration

```
http {

    map $request_port $allow_port {
        443            1;
    }

    map $host $allow_host {
        hostnames;

        example.org    1;
        *.example.org  1;
    }

    server {
        listen 8000;

        resolver dns.example.com;

        if ($allow_port != 1) {
            return 502;
        }

        if ($allow_host != 1) {
            return 502;
        }

        tunnel_pass;
    }
}
```

## Directives

### tunnel_allow_upstream

**Syntax:** `tunnel_allow_upstream string ...;`  
**Default:** —  
**Context:** http, server, location  

Defines conditions under which access to the backend server
is allowed or denied.
If all string parameters are not empty
and not equal to “0” then the access is allowed.
The conditions are evaluated each time
before a connection to a backend server is established.
Parameter values can contain variables:

```
geo $upstream_last_addr $allow {
    volatile;
    10.10.0.0/24        1;
}

server {
    listen 127.0.0.1:8080;

    tunnel_pass;
    tunnel_allow_upstream $allow;
}
```

 > **Note:** This directive is available as part of our *(commercial subscription)* commercial subscription.   

### tunnel_bind

**Syntax:** `tunnel_bind address | off;`  
**Default:** —  
**Context:** http, server, location  

 Makes outgoing connections to a backend server originate from the specified local IP address with an optional port. Parameter value can contain variables. The special value `off` cancels the effect of the `tunnel_bind` directive inherited from the previous configuration level, which allows the system to auto-assign the local IP address and port. 

### tunnel_bind_dynamic

**Syntax:** `tunnel_bind_dynamic on | off;`  
**Default:** `tunnel_bind_dynamic off;`  
**Context:** http, server, location  

When enabled, makes the tunnel_bind operation
at each connection attempt:

```
geo $upstream_last_addr $bind_addr {
    volatile;
    10.0.0.0/24    10.0.0.1;
    192.168.0.0/24  192.168.0.1;
}

tunnel_bind         $bind_addr;
tunnel_bind_dynamic on;
```

 > **Note:** This directive is available as part of our *(commercial subscription)* commercial subscription.   

### tunnel_buffer_size

**Syntax:** `tunnel_buffer_size size;`  
**Default:** `tunnel_buffer_size 16k;`  
**Context:** http, server, location  

 Sets the *size* of the buffer used for reading data from the backend server. Also sets the *size* of the buffer used for reading data from the client. 

### tunnel_connect_timeout

**Syntax:** `tunnel_connect_timeout time;`  
**Default:** `tunnel_connect_timeout 60s;`  
**Context:** http, server, location  

 Defines a timeout for establishing a connection with a backend server. It should be noted that this timeout cannot usually exceed 75 seconds. 

### tunnel_next_upstream

**Syntax:** `tunnel_next_upstream error | timeout | denied | off ...;`  
**Default:** `tunnel_next_upstream error timeout;`  
**Context:** http, server, location  

Specifies in which cases a request should be passed to the next server:
- **`error`** — an error occurred while establishing a connection with the server or reading data from the server;
- **`timeout`** — a timeout has occurred while establishing a connection with the server, passing a request to it, or reading data from the server;
- **`denied`** — the server denied the connection; > **Note:** This parameter is available as part of our *(commercial subscription)* commercial subscription.
- **`off`** — disables passing a request to the next server.

 One should bear in mind that passing a request to the next server is only possible if nothing has been sent to a client yet. That is, if an error or timeout occurs in the middle of the transferring of a response, fixing this is impossible. 

 The directive also defines what is considered an unsuccessful attempt of communication with a server. The cases of `error`, `timeout`, and `denied` are always considered unsuccessful attempts, even if they are not specified in the directive. 

 Passing a request to the next server can be limited by the number of tries and by time. 

### tunnel_next_upstream_timeout

**Syntax:** `tunnel_next_upstream_timeout time;`  
**Default:** `tunnel_next_upstream_timeout 0;`  
**Context:** http, server, location  

 Limits the time during which a request can be passed to the next server. The `0` value turns off this limitation. 

### tunnel_next_upstream_tries

**Syntax:** `tunnel_next_upstream_tries number;`  
**Default:** `tunnel_next_upstream_tries 0;`  
**Context:** http, server, location  

 Limits the number of possible tries for passing a request to the next server. The `0` value turns off this limitation. 

### tunnel_pass

**Syntax:** `tunnel_pass [address];`  
**Default:** —  
**Context:** server, location, if in location  

 Enables handling of CONNECT requests and sets the address of a backend server. By default, the `address` is *$host:$request_port* and is taken from the client request. In most cases, `tunnel_pass` does not require configuring any arguments. 

The address can be specified as a domain name or IP address,
and a port:

```
tunnel_pass localhost:9000;
```

or as a UNIX-domain socket path:

```
tunnel_pass unix:/tmp/backend.socket;
```

 If a domain name resolves to several addresses, all of them will be used in a round-robin fashion. In addition, an address can be specified as a server group. 

 Parameter value can contain variables. In this case, if an address is specified as a domain name, the name is searched among the described server groups, and, if not found, is determined using a resolver. 

### tunnel_read_timeout

**Syntax:** `tunnel_read_timeout time;`  
**Default:** `tunnel_read_timeout 60s;`  
**Context:** http, server, location  

 Sets the timeout between two successive read or write operations on client or backend server connections. If no data is transmitted within this time, the connection is closed. 

### tunnel_send_lowat

**Syntax:** `tunnel_send_lowat size;`  
**Default:** `tunnel_send_lowat 0;`  
**Context:** http, server, location  

 If the directive is set to a non-zero value, nginx will try to minimize the number of send operations on outgoing connections to a backend server by using either
`NOTE_LOWAT` flag of the kqueue method, or the `SO_SNDLOWAT` socket option, with the specified *size*. 

 This directive is ignored on Linux, Solaris, and Windows. 

### tunnel_send_timeout

**Syntax:** `tunnel_send_timeout time;`  
**Default:** `tunnel_send_timeout 60s;`  
**Context:** http, server, location  

 Sets a timeout for transmitting a request to the backend server. The timeout is set only between two successive write operations, not for the transmission of the whole request. If the backend server does not receive anything within this time, the connection is closed. 

### tunnel_socket_keepalive

**Syntax:** `tunnel_socket_keepalive on | off;`  
**Default:** `tunnel_socket_keepalive off;`  
**Context:** http, server, location  

 Configures the “TCP keepalive” behavior for outgoing connections to a backend server. By default, the operating system’s settings are in effect for the socket. If the directive is set to the value “`on`”, the
`SO_KEEPALIVE` socket option is turned on for the socket. 

### tunnel_socket_rcvbuf

**Syntax:** `tunnel_socket_rcvbuf size;`  
**Default:** —  
**Context:** http, server, location  
**Appeared in:** 1.31.3

 Sets the receive buffer size (the `SO_RCVBUF` option) for outgoing connections to a backend server. The special value `0` cancels the effect of the `tunnel_socket_rcvbuf` directive inherited from the previous configuration level, which allows keeping the operating system’s settings in effect for the socket. 

### tunnel_socket_sndbuf

**Syntax:** `tunnel_socket_sndbuf size;`  
**Default:** —  
**Context:** http, server, location  
**Appeared in:** 1.31.3

 Sets the send buffer size (the `SO_SNDBUF` option) for outgoing connections to a backend server. The special value `0` cancels the effect of the `tunnel_socket_sndbuf` directive inherited from the previous configuration level, which allows keeping the operating system’s settings in effect for the socket.
