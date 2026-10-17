# Module ngx_stream_mqtt_filter_module

 The `ngx_stream_mqtt_filter_module` module (1.23.4) provides support for Message Queuing Telemetry Transport protocol (MQTT) versions [3.1.1](https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/mqtt-v3.1.1.html) and [5.0](https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html). 

 > **Note:** This module is available as part of our *(commercial subscription)* commercial subscription.   

## Example Configuration

```
listen            127.0.0.1:18883;
proxy_pass        backend;
proxy_buffer_size 16k;

mqtt             on;
mqtt_set_connect clientid "$client";
mqtt_set_connect username "$name";
```

## Directives

### mqtt

**Syntax:** `mqtt on | off;`  
**Default:** `mqtt off;`  
**Context:** stream, server  

 Enables the MQTT protocol for the given virtual server. 

### mqtt_buffers

**Syntax:** `mqtt_buffers number size;`  
**Default:** `mqtt_buffers 100 1k;`  
**Context:** stream, server  
**Appeared in:** 1.25.1

 Sets the *number* and *size* of the buffers used for handling MQTT messages, for a single connection. 

### mqtt_rewrite_buffer_size

**Syntax:** `mqtt_rewrite_buffer_size size;`  
**Default:** `mqtt_rewrite_buffer_size 4k|8k;`  
**Context:** server  

 > **Note:** This directive is obsolete since version 1.25.1. The mqtt_buffers directive should be used instead.   

 Sets the *size* of the buffer used for writing a modified message. By default, the buffer size is equal to one memory page. This is either 4K or 8K, depending on a platform. It can be made smaller, however. 

### mqtt_set_connect

**Syntax:** `mqtt_set_connect field value;`  
**Default:** —  
**Context:** server  

 Sets the message `field` to the given `value` for CONNECT message. The following fields are supported:
`clientid`,
`username`, and
`password`. The value can contain text, variables, and their combination. 

Several `mqtt_set_connect` directives
can be specified on the same level:

```
mqtt_set_connect clientid "$client";
mqtt_set_connect username "$name";
```
