# Module ngx_mail_proxy_module

## Directives

 <directive name="proxy"> <syntax><literal>on</literal> | <literal>off</literal></syntax> <default>off</default> <context>mail</context> <context>server</context>  <para> Not tested anywhere in the current version. </para>  </directive> 
### proxy_buffer

**Syntax:** `proxy_buffer size;`  
**Default:** `proxy_buffer 4k|8k;`  
**Context:** mail, server  

 Sets the size of the buffer used for proxying. By default, the buffer size is equal to one memory page. Depending on a platform, it is either 4K or 8K. 

### proxy_pass_error_message

**Syntax:** `proxy_pass_error_message on | off;`  
**Default:** `proxy_pass_error_message off;`  
**Context:** mail, server  

 Indicates whether to pass the error message obtained during the authentication on the backend to the client. 

 Usually, if the authentication in nginx is a success, the backend cannot return an error. If it nevertheless returns an error, it means some internal error has occurred. In such case the backend message can contain information that should not be shown to the client. However, responding with an error for the correct password is a normal behavior for some POP3 servers. For example, CommuniGatePro informs a user about [mailbox overflow](http://www.stalker.com/CommuniGatePro/Alerts.html#Quota) or other events by periodically outputting the [authentication error](http://www.stalker.com/CommuniGatePro/POP.html#Alerts). The directive should be enabled in this case. 

### proxy_protocol

**Syntax:** `proxy_protocol on | off | v2;`  
**Default:** `proxy_protocol off;`  
**Context:** mail, server  
**Appeared in:** 1.19.8

 Enables the [PROXY protocol](http://www.haproxy.org/download/1.8/doc/proxy-protocol.txt) for connections to a backend. The `on` parameter enables version 1 of the PROXY protocol (text format). The `v2` parameter (1.31.4) enables version 2 of the PROXY protocol (binary format). 

### proxy_smtp_auth

**Syntax:** `proxy_smtp_auth on | off;`  
**Default:** `proxy_smtp_auth off;`  
**Context:** mail, server  
**Appeared in:** 1.19.4

 Enables or disables user authentication on the SMTP backend using the `AUTH` command. 

 If XCLIENT is also enabled, then the `XCLIENT` command will not send the `LOGIN` parameter. 

### proxy_timeout

**Syntax:** `proxy_timeout timeout;`  
**Default:** `proxy_timeout 24h;`  
**Context:** mail, server  

 Sets the *timeout* between two successive read or write operations on client or proxied server connections. If no data is transmitted within this time, the connection is closed. 

### xclient

**Syntax:** `xclient on | off;`  
**Default:** `xclient on;`  
**Context:** mail, server  

 Enables or disables the passing of the [XCLIENT](http://www.postfix.org/XCLIENT_README.html) command with client parameters when connecting to the SMTP backend. 

 With `XCLIENT`, the MTA is able to write client information to the log and apply various limitations based on this data. 

If `XCLIENT` is enabled
then nginx passes the following commands when connecting to the backend:
- `EHLO` with the server name
- `XCLIENT`
- `EHLO` or `HELO`, as passed by the client

 If the name found by the client IP address points to the same address, it is passed in the `NAME` parameter of the `XCLIENT` command. If the name could not be found, points to a different address, or resolver is not specified, the `[UNAVAILABLE]` is passed in the `NAME` parameter. If an error has occurred in the process of resolving, the `[TEMPUNAVAIL]` value is used. 

 If `XCLIENT` is disabled then nginx passes the `EHLO` command with the server name when connecting to the backend if the client has passed
`EHLO`, or `HELO` with the server name, otherwise.
