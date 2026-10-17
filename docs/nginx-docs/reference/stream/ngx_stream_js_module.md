# Module ngx_stream_js_module

 The `ngx_stream_js_module` module is used to implement session and variable handlers in JavaScript with njs. 

 Download and install instructions are available here. 

## Example Configuration

The example works since
0.4.0.

```
stream {
    # since 0.9.1
    js_engine qjs;

    js_import stream.js;

    js_set $bar stream.bar;
    js_set $req_line stream.req_line;

    server {
        listen 12345;

        js_preread stream.preread;
        return     $req_line;
    }

    server {
        listen 12346;

        js_access  stream.access;
        proxy_pass 127.0.0.1:8000;
        js_filter  stream.header_inject;
    }
}

http {
    server {
        listen 8000;
        location / {
            return 200 $http_foo\n;
        }
    }
}
```

The `stream.js` file:

```
var line = '';

function bar(s) {
    var v = s.variables;
    s.log("hello from bar() handler!");
    return "bar-var" + v.remote_port + "; pid=" + v.pid;
}

function preread(s) {
    s.on('upload', function (data, flags) {
        var n = data.indexOf('\n');
        if (n != -1) {
            line = data.substr(0, n);
            s.done();
        }
    });
}

function req_line(s) {
    return line;
}

// Read HTTP request line.
// Collect bytes in 'req' until
// request line is read.
// Injects HTTP header into a client's request

var my_header =  'Foo: foo';
function header_inject(s) {
    var req = '';
    s.on('upload', function(data, flags) {
        req += data;
        var n = req.search('\n');
        if (n != -1) {
            var rest = req.substr(n + 1);
            req = req.substr(0, n + 1);
            s.send(req + my_header + '\r\n' + rest, flags);
            s.off('upload');
        }
    });
}

function access(s) {
    if (s.remoteAddress.match('^192.*')) {
        s.deny();
        return;
    }

    s.allow();
}

export default {bar, preread, req_line, header_inject, access};
```

## Directives

### js_access

**Syntax:** `js_access module.function;`  
**Default:** —  
**Context:** stream, server  

 Sets an njs function which will be called at the access phase. Since 0.4.0, a module function can be referenced. 

The function is called once at the moment when the stream session reaches
the access phase
for the first time.
The function is called with the following arguments:

- **`s`** — the Stream Session object

 At this phase, it is possible to perform initialization or register a callback with the `s.on()` method for each incoming data chunk until one of the following methods are called:
`s.allow()`,
`s.decline()`,
`s.done()`. As soon as one of these methods is called, the stream session processing switches to the next phase and all current
`s.on()` callbacks are dropped. 

### js_context_reuse

**Syntax:** `js_context_reuse number;`  
**Default:** `js_context_reuse 128;`  
**Context:** stream, server  
**Appeared in:** 0.8.6

 Sets a maximum number of JS context to be reused for QuickJS engine. Each context is used for a single stream session. The finished context is put into a pool of reusable contexts. If the pool is full, the context is destroyed. 

### js_engine

**Syntax:** `js_engine njs | qjs;`  
**Default:** `js_engine njs;`  
**Context:** stream, server  
**Appeared in:** 0.8.6

 Sets a JavaScript engine to be used for njs scripts. The `njs` parameter sets the njs engine, also used by default. The `qjs` parameter sets the QuickJS engine. 

 > **Note:** The `njs` engine is deprecated since 1.0.0; new configurations should use the `qjs` (QuickJS) engine.   

### js_fetch_buffer_size

**Syntax:** `js_fetch_buffer_size size;`  
**Default:** `js_fetch_buffer_size 16k;`  
**Context:** stream, server  
**Appeared in:** 0.7.4

 Sets the *size* of the buffer used for reading and writing with Fetch API. 

### js_fetch_ciphers

**Syntax:** `js_fetch_ciphers ciphers;`  
**Default:** `js_fetch_ciphers HIGH:!aNULL:!MD5;`  
**Context:** stream, server  
**Appeared in:** 0.7.0

 Specifies the enabled ciphers for HTTPS connections with Fetch API. The ciphers are specified in the format understood by the OpenSSL library. 

 The full list can be viewed using the “`openssl ciphers`” command. 

### js_fetch_max_response_buffer_size

**Syntax:** `js_fetch_max_response_buffer_size size;`  
**Default:** `js_fetch_max_response_buffer_size 1m;`  
**Context:** stream, server  
**Appeared in:** 0.7.4

 Sets the maximum *size* of the response received with Fetch API. 

### js_fetch_protocols

**Syntax:** `js_fetch_protocols [TLSv1] [TLSv1.1] [TLSv1.2] [TLSv1.3];`  
**Default:** `js_fetch_protocols TLSv1 TLSv1.1 TLSv1.2;`  
**Context:** stream, server  
**Appeared in:** 0.7.0

 Enables the specified protocols for HTTPS connections with Fetch API. 

### js_fetch_timeout

**Syntax:** `js_fetch_timeout time;`  
**Default:** `js_fetch_timeout 60s;`  
**Context:** stream, server  
**Appeared in:** 0.7.4

 Defines a timeout for reading and writing for Fetch API. The timeout is set only between two successive read/write operations, not for the whole response. If no data is transmitted within this time, the connection is closed. 

### js_fetch_trusted_certificate

**Syntax:** `js_fetch_trusted_certificate file;`  
**Default:** —  
**Context:** stream, server  
**Appeared in:** 0.7.0

 Specifies a *file* with trusted CA certificates in the PEM format used to verify the HTTPS certificate with Fetch API. 

### js_fetch_verify

**Syntax:** `js_fetch_verify on | off;`  
**Default:** `js_fetch_verify on;`  
**Context:** stream, server  
**Appeared in:** 0.7.4

 Enables or disables verification of the HTTPS server certificate with Fetch API. 

### js_fetch_verify_depth

**Syntax:** `js_fetch_verify_depth number;`  
**Default:** `js_fetch_verify_depth 100;`  
**Context:** stream, server  
**Appeared in:** 0.7.0

 Sets the verification depth in the HTTPS server certificates chain with Fetch API. 

### js_fetch_proxy

**Syntax:** `js_fetch_proxy url;`  
**Default:** —  
**Context:** stream, server  
**Appeared in:** 0.9.4

 Configures a forward proxy URL with Fetch API. The *url* supports the HTTP scheme only and can contain optional user credentials in the format `http://[user:password@]host:port` for Basic authentication. Supports both HTTP and HTTPS connections to destination servers. If the *url* is empty, proxy routing is disabled. The parameter value can contain variables. 

Example:

```
server {
    listen 12345;
    js_fetch_proxy http://user:pass@proxy.example.com:3128;
    js_preread main.fetch_handler;
}
```

### js_fetch_keepalive

**Syntax:** `js_fetch_keepalive connections;`  
**Default:** `js_fetch_keepalive 0;`  
**Context:** stream, server  
**Appeared in:** 0.9.2

 Activates the cache for connections to destination servers. When the value is greater than `0`, enables keepalive connections for Fetch API. 

 The *connections* parameter sets the maximum number of idle keepalive connections to destination servers that are preserved in the cache of each worker process. When this number is exceeded, the least recently used connections are closed. 

 In Stream, the cache is maintained separately for each server configuration. A value set at the `stream` level is inherited by servers, but each server uses its own cache. Cached connections are reused for requests with the same protocol, host, and port. 

 When enabled, keepalive assumes that destination servers send valid HTTP responses. 

Example:

```
server {
    listen 12345;
    js_fetch_keepalive 32;
    js_fetch_trusted_certificate /path/to/ISRG_Root_X1.pem;
    js_preread main.fetch_handler;
}
```

### js_fetch_keepalive_requests

**Syntax:** `js_fetch_keepalive_requests number;`  
**Default:** `js_fetch_keepalive_requests 1000;`  
**Context:** stream, server  
**Appeared in:** 0.9.2

 Sets the maximum number of requests that can be served through one keepalive connection with Fetch API. After the maximum number of requests is made, the connection is closed. 

 Closing connections periodically is necessary to free per-connection memory allocations. Therefore, using too high maximum number of requests could result in excessive memory usage and not recommended. 

### js_fetch_keepalive_time

**Syntax:** `js_fetch_keepalive_time time;`  
**Default:** `js_fetch_keepalive_time 1h;`  
**Context:** stream, server  
**Appeared in:** 0.9.2

 Limits the maximum time during which requests can be processed through one keepalive connection with Fetch API. After this time is reached, the connection is closed following the subsequent request processing. 

### js_fetch_keepalive_timeout

**Syntax:** `js_fetch_keepalive_timeout time;`  
**Default:** `js_fetch_keepalive_timeout 60s;`  
**Context:** stream, server  
**Appeared in:** 0.9.2

 Sets a timeout during which an idle keepalive connection to a destination server will stay open with Fetch API. 

### js_filter

**Syntax:** `js_filter module.function;`  
**Default:** —  
**Context:** stream, server  

 Sets a data filter. Since 0.4.0, a module function can be referenced. The filter function is called once at the moment when the stream session reaches the content phase. 

The filter function is called with the following arguments:
- **`s`** — the Stream Session object

 At this phase, it is possible to perform initialization or register a callback with the `s.on()` method for each incoming data chunk. The
`s.off()` method may be used to unregister a callback and stop filtering. 

 > **Note:** As the `js_filter` handler returns its result immediately, it supports only synchronous operations. Thus, asynchronous operations such as > `ngx.fetch()` or > `setTimeout()` are not supported.   

### js_import

**Syntax:** `js_import module.js | export_name from module.js;`  
**Default:** —  
**Context:** stream, server  
**Appeared in:** 0.4.0

Imports a module that implements session and variable handlers in njs.
The `export_name` is used as a namespace
to access module functions.
If the `export_name` is not specified,
the module name will be used as a namespace.

```
js_import stream.js;
```

Here, the module name `stream` is used as a namespace
while accessing exports.
If the imported module exports `foo()`,
`stream.foo` is used to refer to it.

 Several `js_import` directives can be specified. 

 > **Note:** The directive can be specified on the > `server` level since 0.7.7.   

### js_include

**Syntax:** `js_include file;`  
**Default:** —  
**Context:** stream  

Specifies a file that implements server and variable handlers in njs:

```
nginx.conf:
js_include stream.js;
js_set     $js_addr address;
server {
    listen 127.0.0.1:12345;
    return $js_addr;
}

stream.js:
function address(s) {
    return s.remoteAddress;
}
```

 The directive was made obsolete in version 0.4.0 and was removed in version 0.7.1. The js_import directive should be used instead. 

### js_load_stream_native_module

**Syntax:** `js_load_stream_native_module path [as name];`  
**Default:** —  
**Context:** main  
**Appeared in:** 0.9.5

 Loads a native module (shared library) for use in Stream JavaScript code. The directive is QuickJS-only and is not available when using the njs built-in JavaScript engine. 

 The *path* parameter specifies the absolute path to the shared library file. The optional `as` *name* parameter provides an alias name for importing the module in JavaScript code. If not specified, the module can be imported using its filename. 

Example:

```
js_load_stream_native_module /path/to/mylib.so;
js_load_stream_native_module /path/to/other.so as myalias;

stream {
    js_import main.js;
    # ... rest of stream configuration
}
```

In JavaScript code:

```
// Import by filename
import * as mylib from 'mylib.so';

// Import by alias
import * as myalias from 'myalias';

// Use exported functions
let result = mylib.add(5, 10);
```

 > **Note:** For security reasons, this directive is only allowed in the `main` configuration context. Native modules run with full process privileges; use absolute paths and ensure proper code review.   

### js_path

**Syntax:** `js_path path;`  
**Default:** —  
**Context:** stream, server  
**Appeared in:** 0.3.0

 Sets an additional path for njs modules. 

 > **Note:** The directive can be specified on the > `server` level since 0.7.7.   

### js_periodic

**Syntax:** `js_periodic module.function [interval=time] [jitter=number] [worker_affinity=mask];`  
**Default:** —  
**Context:** server  
**Appeared in:** 0.8.1

 Specifies a content handler to run at regular interval. The handler receives a session object as its first argument, it also has access to global objects such as ngx. 

 The optional `interval` parameter sets the interval between two consecutive runs, by default, 5 seconds. 

 The optional `jitter` parameter sets the time within which the location content handler will be randomly delayed, by default, there is no delay. 

 By default, the `js_periodic` handler is executed on worker process 0. The optional `worker_affinity` parameter allows specifying particular worker processes where the location content handler should be executed. Each worker process set is represented by a bitmask of allowed worker processes. The `all` mask allows the handler to be executed in all worker processes. 

Example:

```
example.conf:

location @periodics {
    # to be run at 1 minute intervals in worker process 0
    js_periodic main.handler interval=60s;

    # to be run at 1 minute intervals in all worker processes
    js_periodic main.handler interval=60s worker_affinity=all;

    # to be run at 1 minute intervals in worker processes 1 and 3
    js_periodic main.handler interval=60s worker_affinity=0101;

    resolver 10.0.0.1;
    js_fetch_trusted_certificate /path/to/ISRG_Root_X1.pem;
}

example.js:

async function handler(s) {
    let reply = await ngx.fetch('https://nginx.org/en/docs/njs/');
    let body = await reply.text();

    ngx.log(ngx.INFO, body);
}
```

### js_preload_object

**Syntax:** `js_preload_object name.json | name from file.json;`  
**Default:** —  
**Context:** stream, server  
**Appeared in:** 0.7.8

Preloads an
immutable object
at configure time.
The `name` is used as a name of the global variable
though which the object is available in njs code.
If the `name` is not specified,
the file name will be used instead.

```
js_preload_object map.json;
```

Here, the `map` is used as a name
while accessing the preloaded object.

 Several `js_preload_object` directives can be specified. 

### js_preread

**Syntax:** `js_preread module.function;`  
**Default:** —  
**Context:** stream, server  

 Sets an njs function which will be called at the preread phase. Since 0.4.0, a module function can be referenced. 

The function is called once
at the moment when the stream session reaches the
preread phase
for the first time.
The function is called with the following arguments:

- **`s`** — the Stream Session object

 At this phase, it is possible to perform initialization or register a callback with the `s.on()` method for each incoming data chunk until one of the following methods are called:
`s.allow()`,
`s.decline()`,
`s.done()`. When one of these methods is called, the stream session switches to the next phase and all current
`s.on()` callbacks are dropped. 

 > **Note:** As the `js_preread` handler returns its result immediately, it supports only synchronous callbacks. Thus, asynchronous callbacks such as > `ngx.fetch()` or > `setTimeout()` are not supported. Nevertheless, asynchronous operations are supported in > `s.on()` callbacks in the preread phase. See [this example](https://github.com/nginx/njs-examples#authorizing-connections-using-ngx-fetch-as-auth-request-stream-auth-request) for more information.   

### js_set

**Syntax:** `js_set $variable module.function [nocache];`  
**Default:** —  
**Context:** stream, server  

 Sets an njs `function` for the specified `variable`. Since 0.4.0, a module function can be referenced. 

 The function is called when the variable is referenced for the first time for a given request. The exact moment depends on a phase at which the variable is referenced. This can be used to perform some logic not related to variable evaluation. For example, if the variable is referenced only in the log_format directive, its handler will not be executed until the log phase. This handler can be used to do some cleanup right before the request is freed. 

 Since 0.8.6, when optional argument `nocache` is provided the handler is called every time it is referenced. Due to current limitations of the ngx_stream_set_module module, when a `nocache` variable is referenced by the set directive its handler should always return a fixed-length value. 

 > **Note:** As the `js_set` handler returns its result immediately, it supports only synchronous callbacks. Thus, asynchronous callbacks such as ngx.fetch() or setTimeout() are not supported.   

 > **Note:** The directive can be specified on the > `server` level since 0.7.7.   

### js_shared_dict_zone

**Syntax:** `js_shared_dict_zone zone=name:size [timeout=time] [type=string|number] [evict] [state=file];`  
**Default:** —  
**Context:** stream  
**Appeared in:** 0.8.0

 Sets the *name* and *size* of the shared memory zone that keeps the key-value dictionary shared between worker processes. 

 By default the shared dictionary uses a string as a key and a value. The optional `type` parameter allows redefining the value type to number. 

 The optional `timeout` parameter sets the time in milliseconds after which all shared dictionary entries are removed from the zone. If some entries require a different removal time, it can be set with the `timeout` argument of the add, incr, and set methods (0.8.5). 

 The optional `evict` parameter removes the oldest key-value pair when the zone storage is exhausted. 

 The optional `state` parameter specifies a *file* that keeps the shared dictionary state in JSON format and makes it persistent across nginx restarts (0.9.1). 

Example:

```
example.conf:
    # Creates a 1Mb dictionary with string values,
    # removes key-value pairs after 60 seconds of inactivity:
    js_shared_dict_zone zone=foo:1M timeout=60s;

    # Creates a 512Kb dictionary with string values,
    # forcibly removes oldest key-value pairs when the zone is exhausted:
    js_shared_dict_zone zone=bar:512K timeout=30s evict;

    # Creates a 32Kb permanent dictionary with number values:
    js_shared_dict_zone zone=num:32k type=number;

    # Creates a 1Mb dictionary with string values and persistent state:
    js_shared_dict_zone zone=persistent:1M state=/tmp/dict.json;

example.js:
    function get(r) {
        r.return(200, ngx.shared.foo.get(r.args.key));
    }

    function set(r) {
        r.return(200, ngx.shared.foo.set(r.args.key, r.args.value));
    }

    function del(r) {
        r.return(200, ngx.shared.bar.delete(r.args.key));
    }

    function increment(r) {
        r.return(200, ngx.shared.num.incr(r.args.key, 2));
    }
```

### js_var

**Syntax:** `js_var $variable [value];`  
**Default:** —  
**Context:** stream, server  
**Appeared in:** 0.5.3

 Declares a writable variable. The value can contain text, variables, and their combination. 

 > **Note:** The directive can be specified on the > `server` level since 0.7.7.   

## Session Object Properties

 Each stream njs handler receives one argument, a stream session object.
