# Reference

 njs provides objects, methods and properties for extending nginx functionality. 

 This reference contains only njs specific properties, methods and modules not compliant with ECMAScript. Definitions of njs properties and methods compliant with ECMAScript can be found in [ECMAScript specification](http://www.ecma-international.org/ecma-262/). List of all njs properties and methods can be found in Compatibility. 

## nginx objects

### HTTP Request

| `r.args{}` |
|---|
| `r.decline()` |
| `r.done()` |
| `r.error()` |
| `r.finish()` |
| `r.headersIn{}` |
| `r.headersOut{}` |
| `r.httpVersion` |
| `r.internal` |
| `r.internalRedirect()` |
| `r.jsVarNames()` |
| `r.log()` |
| `r.method` |
| `r.parent` |
| `r.readRequestArrayBuffer()` |
| `r.readRequestForm()` |
| `r.readRequestJSON()` |
| `r.readRequestText()` |
| `r.remoteAddress` |
| `r.requestBody` |
| `r.requestBuffer` |
| `r.requestText` |
| `r.rawHeadersIn[]` |
| `r.rawHeadersOut[]` |
| `r.responseBody` |
| `r.responseBuffer` |
| `r.responseText` |
| `r.return()` |
| `r.send()` |
| `r.sendBuffer()` |
| `r.sendHeader()` |
| `r.setReturnValue()` |
| `r.status` |
| `r.subrequest()` |
| `r.uri` |
| `r.rawVariables{}` |
| `r.variables{}` |
| `r.warn()` |

The HTTP request object is available only in the
ngx_http_js_module module.
Before 0.8.5,
all string properties of the object
were byte strings.

- **`r.args{}`** — request arguments object, read-only.
   The query string is returned as an object. Since 0.7.6, duplicate keys are returned as an array, keys are case-sensitive, both keys and values are percent-decoded. 
  
  
  
  
  For example, the query string
  
  ```
  'a=1&b=%32&A=3&b=4&B=two%20words'
  ```
  
  is converted to `r.args` as:
  
  ```
  {a: "1", b: ["2", "4"], A: "3", B: "two words"}
  ```
  
  More advanced parsing scenarios can be achieved with the
  Query String module
  and with the
  `$args`
  variable, for example:
  
  
  ```
  import qs from 'querystring';
  
  function args(r) {
      return qs.parse(r.variables.args);
  }
  ```
  
  The argument object
  is evaluated at the first access to `r.args`.
  If only a single argument is needed, for example `foo`,
  nginx variables can be used:
  
  ```
  r.variables.arg_foo
  ```
  
  Here, nginx variables object
  returns the first value for a given key,
  case-insensitive, without percent-decoding.
  
  
  
  
   To convert `r.args` back to a string, the Query String
  `stringify` method can be used.
- **`r.decline()`** — makes the js_access handler express no opinion about access, deferring the decision to other access checkers under
  `satisfy any` (0.9.9). A handler that returns without calling
  `r.decline()` or
  `r.return()` implicitly grants access. May be called only from the js_access function.
- **`r.done()`** — after calling this function, next data chunks will be passed to client without calling js_body_filter (0.5.2). May be called only from the js_body_filter function
- **`r.error(*string*)`** — writes a `string` to the error log on the `error` level of logging > **Note:** As nginx has a hardcoded maximum line length limit, only first 2048 bytes of the string can be logged.
- **`r.finish()`** — finishes sending a response to the client
- **`r.headersIn{}`** — incoming headers object, read-only. The `Foo` request header can be accessed with the syntax:
  `headersIn.foo` or `headersIn['Foo']`.    The
  `Authorization`,
  `Content-Length`,
  `Content-Range`,
  `Content-Type`,
  `ETag`,
  `Expect`,
  `From`,
  `Host`,
  `If-Match`,
  `If-Modified-Since`,
  `If-None-Match`,
  `If-Range`,
  `If-Unmodified-Since`,
  `Max-Forwards`,
  `Proxy-Authorization`,
  `Referer`,
  `Transfer-Encoding`, and
  `User-Agent` request headers can have only one field value (0.4.1). Duplicate field values in `Cookie` headers are separated by semicolon (`;`). Duplicate field values in all other request headers are separated by commas.
- **`r.headersOut{}`** — outgoing headers object for the main request, writable.
  
   If `r.headersOut{}` is the response object of a subrequest, it represents response headers. In this case, field values in
  `Accept-Ranges`,
  `Connection`,
  `Content-Disposition`,
  `Content-Encoding`,
  `Content-Length`,
  `Content-Range`,
  `Date`,
  `Keep-Alive`,
  `Server`,
  `Transfer-Encoding`,
  `X-Accel-*` response headers may be omitted. 
  
  
  
   The `Foo` response header can be accessed with the syntax:
  `headersOut.foo` or `headersOut['Foo']`. 
  
  
  
  
  Outgoing headers should be set before a response header is sent to a client,
  otherwise header update will be ignored.
  This means that `r.headersOut{}` is effectively writable in:
  
  - the js_content handler before
    `r.sendHeader()` or
    `r.return()` are called
  - the js_header_filter handler
  
  
  
  
  
  
  
  Field values of multi-value response headers
  (0.4.0)
  can be set with the syntax:
  
  ```
  r.headersOut['Foo'] = ['a', 'b']
  ```
  
  where the output will be:
  
  ```
  Foo: a
  Foo: b
  ```
  
  All previous field values of the `Foo` response header
  will be deleted.
  
  
  
  
   For standard response headers that accept only a single field value such as
  `Content-Type`, only the last element of the array will take effect. Field values of the `Set-Cookie` response header are always returned as an array. Duplicate field values in
  `Age`,
  `Content-Encoding`,
  `Content-Length`,
  `Content-Type`,
  `ETag`,
  `Expires`,
  `Last-Modified`,
  `Location`,
  `Retry-After` response headers are ignored. Duplicate field values in all other response headers are separated by commas.
- **`r.httpVersion`** — HTTP version, read-only
- **`r.internal`** — boolean value, true for internal locations
- **`r.internalRedirect(*uri*)`** — performs an internal redirect to the specified `uri`. If the uri starts with the “`@`” prefix, it is considered a named location. In a new location, all request processing is repeated starting from NGX_HTTP_SERVER_REWRITE_PHASE for ordinary locations and from NGX_HTTP_REWRITE_PHASE for named locations. As a result, a redirect to a named location does not check client_max_body_size limit. See dev guide for more details. Redirected requests become internal and can access the internal locations. The actual redirect happens after the handler execution is completed. > **Note:** After redirect, a new njs VM is started in the target location, the VM in the original location is stopped. Values of nginx variables are kept and can be used to pass information to the target location. Since 0.5.3, the variable declared with the `js_var` directive for http or stream can be used.    > **Note:** Since 0.7.4, the method accepts escaped URIs.
- **`r.log(*string*)`** — writes a `string` to the error log on the `info` level of logging > **Note:** As nginx has a hardcoded maximum line length limit, only first 2048 bytes of the string can be logged.
- **`r.method`** — HTTP method, read-only
- **`r.parent`** — references the parent request object for a subrequest response object received through a completion callback or the `Promise` returned by `r.subrequest()`. For a request object passed to a JavaScript handler, including a subrequest handler,
  `undefined` is returned.
- **`r.remoteAddress`** — client address, read-only
- **`r.readRequestArrayBuffer()`** — returns a `Promise` that resolves with the client request body as an `ArrayBuffer` (0.9.9). See
  `r.readRequestText()` for availability, body caching, and concurrency semantics.
- **`r.readRequestForm(*[options]*)`** — reads the client request body and parses it as an HTML form,
  returning a `Promise` that resolves with a form object
  (0.9.9).
  Supported content types are
  `application/x-www-form-urlencoded`
  and `multipart/form-data`.
  
  
  The form object provides the following methods:
  - **`get(*name*)`** — returns the first value for *name*, or `null` if absent.
  - **`getAll(*name*)`** — returns an array with all values for *name*.
  - **`has(*name*)`** — returns `true` if at least one entry exists for *name*.
  - **`forEach(*callback*[,
  *thisArg*])`** — invokes *callback* for each entry with arguments
    `(value, key, form)`.
  - **`hasFiles()`** — returns `true` if the form contains any file parts.
  
  
  
  
  
  
   For text fields, values are decoded strings. For file parts, the value is an object with the client-supplied filename available as the `name` property; file contents are not exposed. The filename is client-supplied and is not sanitized. 
  
  
  
  
  The optional *options* object accepts the following
  properties:
  - **`maxKeys`
  *number*** — the maximum number of fields to parse, by default is `128`. Exceeding the limit rejects the returned promise.
  
  
  
  
  
  
   See
  `r.readRequestText()` for availability, body caching, and concurrency semantics. The parsed form is itself cached on the request: a subsequent call returns the same form object and ignores any new *options* argument.
- **`r.readRequestJSON()`** — returns a `Promise` that resolves with the client request body parsed as JSON (0.9.9). See
  `r.readRequestText()` for availability, body caching, and concurrency semantics.
- **`r.readRequestText()`** — returns a `Promise` that resolves with the client request body as a string (0.9.9). The size of the request body is limited by client_max_body_size. The method is available in the js_access and js_content directives.  The body is read once and cached on the request: subsequent calls to
  `r.readRequestText()`,
  `r.readRequestArrayBuffer()`,
  `r.readRequestJSON()`, or
  `r.readRequestForm()` resolve from the cached body without re-reading the wire. A second call issued while a previous read is still pending throws
  `"request body is already being read"`.    Note that it may convert bytes invalid in UTF-8 encoding into the replacement character.
- **`r.requestBody`** — the property was made obsolete in 0.5.0 and was removed in 0.8.0. The `r.requestBuffer` or
  `r.requestText` property should be used instead.
- **`r.requestBuffer`** — client request body if it has not been written to a temporary file (since 0.5.0). To ensure that the client request body is in memory, its size should be limited by client_max_body_size, and a sufficient buffer size should be set using client_body_buffer_size. The property is available only in the js_content directive. For asynchronous access, or for use in js_access, see
  `r.readRequestText()` and other “`r.readRequest*()`” methods.
- **`r.requestText`** — the same as `r.requestBuffer`, but returns a `string`. Note that it may convert bytes invalid in UTF-8 encoding into the replacement character. For asynchronous access, or for use in js_access, see
  `r.readRequestText()`.
- **`r.rawHeadersIn[]`** — returns an array of key-value pairs
  exactly as they were received from the client
  (0.4.1).
  
  For example, with the following request headers:
  
  ```
  Host: localhost
  Foo:  bar
  foo:  bar2
  ```
  
  the output of `r.rawHeadersIn` will be:
  
  ```
  [
      ['Host', 'localhost'],
      ['Foo', 'bar'],
      ['foo', 'bar2']
  ]
  ```
  
  All `foo` headers
  can be collected with the syntax:
  
  ```
  r.rawHeadersIn.filter(v=>v[0].toLowerCase() == 'foo').map(v=>v[1])
  ```
  
  the output will be:
  
  ```
  ['bar', 'bar2']
  ```
  
  Header field names are not converted to lower case,
  duplicate field values are not merged.
- **`r.rawHeadersOut[]`** — returns an array of key-value pairs of response headers (0.4.1). Header field names are not converted to lower case, duplicate field values are not merged.
- **`r.responseBody`** — the property was made obsolete in 0.5.0 and was removed in 0.8.0. The `r.responseBuffer` or the `r.responseText` property should be used instead.
- **`r.responseBuffer`** — holds the subrequest response body, read-only (since 0.5.0). The size of `r.responseBuffer` is limited by the subrequest_output_buffer_size directive.
- **`r.responseText`** — the same as `r.responseBuffer` but returns a string (since 0.5.0). Note that it may convert bytes invalid in UTF-8 encoding into the replacement character.
- **`r.return(status[,
string | Buffer])`** — sends the entire response with the specified `status` to the client. The response can be a string or Buffer (0.5.0). May be called from the js_content or, since 0.9.9, js_access handler.   It is possible to specify either a redirect URL (for codes 301, 302, 303, 307, and 308) or the response body text (for other codes) as the second argument
- **`r.send(string
| Buffer)`** — sends a part of the response body to the client. The data sent can be a string or Buffer (0.5.0)
- **`r.sendBuffer(*data*[,
*options*])`** — adds data to the chain of data chunks to be forwarded to the next body filter
  (0.5.2).
  The actual forwarding happens later,
  when the all the data chunks of the current chain are processed.
  
  The data can be a string or Buffer.
  The `options` is an object used
  to override nginx buffer flags derived from an incoming data chunk buffer.
  The flags can be overridden with the following flags:
  - **`last`** — boolean, true if the buffer is the last buffer
  - **`flush`** — boolean, true if the buffer should have the `flush` flag
  
  
  
  
  
  The method may be called only from the
  js_body_filter function.
- **`r.sendHeader()`** — sends the HTTP headers to the client
- **`r.setReturnValue(*value*)`** — sets the return value of the
  js_set handler
  (0.7.0).
  
  The method was made obsolete in
  0.9.5.
  Since this version, an `async` handler
  can return its value with an ordinary return statement:
  
  ```
  async function js_set(r) {
      const digest = await crypto.subtle.digest('SHA-256', r.headersIn.host);
      return Buffer.from(digest).toString('hex');
  }
  ```
- **`r.status`** — status, writable
- **`r.subrequest(*uri*[,
*options*[, *callback*]])`** — creates a subrequest with the given `uri` and
  `options`, and installs
  an optional completion `callback`.
  
   A subrequest shares its input headers with the client request. To send headers different from original headers to a proxied server, the proxy_set_header directive can be used. To send a completely new set of headers to a proxied server, the proxy_pass_request_headers directive can be used. 
  
  
  
  
  If `options` is a string, then it
  holds the subrequest arguments string.
  Otherwise, `options` is expected to be
  an object with the following keys:
  - **`args`** — arguments string, by default an empty string is used
  - **`body`** — request body, by default the request body of the parent request object is used
  - **`method`** — HTTP method, by default the `GET` method is used
  - **`detached`** — boolean flag (0.3.9), if `true`, the created subrequest is a detached subrequest. Responses to detached subrequests are ignored. Unlike ordinary subrequests, a detached subrequest can be created inside a variable handler. The `detached` flag and callback argument are mutually exclusive.
  
  
  
  
  
  
   The completion `callback` receives a subrequest response object with methods and properties identical to the parent request object. 
  
  
  
   Since 0.3.8, if a `callback` is not provided, the `Promise` object that resolves to the subrequest response object is returned. 
  
  
  
  
  For example, to view all response headers in the subrequest:
  
  ```
  async function handler(r) {
      const reply = await r.subrequest('/path');
  
      for (const h in reply.headersOut) {
          r.log(`${h}: ${reply.headersOut[h]}`);
      }
  
      r.return(200);
  }
  ```
- **`r.uri`** — current URI in request, normalized, read-only
- **`r.rawVariables{}`** — nginx variables as Buffers, writable (since 0.5.0)
- **`r.jsVarNames(*[prefix]*)`** — returns a new array of names of nginx variables declared with the js_var directive (since 0.9.9). The optional *prefix* argument must be a string. If it is specified, only names that start with the prefix are returned.
- **`r.variables{}`** — nginx variables object, writable
  (since 0.2.8).
  
  
  For example, to get the `$foo` variable,
  one of the following syntax can be used:
  
  ```
  r.variables['foo']
  r.variables.foo
  ```
  
  Since 0.8.6,
  regular expression captures can be accessed using the following syntax:
  
  ```
  r.variables['1']
  r.variables[1]
  ```
  
  
  
  
  
  
  nginx treats variables referenced in `nginx.conf`
  and unreferenced variables differently.
  When a variable is referenced, it may be cacheable,
  but when it is unreferenced it is always uncacheable.
  For example, when the
  $request_id
  variable is only accessed from njs,
  it has a new value every time it is evaluated.
  But, when the
  $request_id
  is referenced, for example:
  
  ```
  proxy_set_header X-Request-Id $request_id;
  ```
  
  the `r.variables.request_id` returns the same value every time.
  
  
  
  
  
  A variable is writable if:
  - it was created using the `js_var` directive for http or stream (since 0.5.3)
  - it is referenced in nginx configuration file
  
  
  Even so, some embedded variables still cannot be assigned a value (for example,
  `$http_`).
- **`r.warn(*string*)`** — writes a `string` to the error log on the `warning` level of logging > **Note:** As nginx has a hardcoded maximum line length limit, only first 2048 bytes of the string can be logged.

### Stream Session

| `s.allow()` |
|---|
| `s.decline()` |
| `s.deny()` |
| `s.done()` |
| `s.error()` |
| `s.jsVarNames()` |
| `s.log()` |
| `s.off()` |
| `s.on()` |
| `s.remoteAddress` |
| `s.rawVariables{}` |
| `s.send()` |
| `s.sendDownstream()` |
| `s.sendUpstream()` |
| `s.status` |
| `s.setReturnValue()` |
| `s.variables{}` |
| `s.warn()` |

 The stream session object is available only in the ngx_stream_js_module module. Before 0.8.5, all string properties of the object were byte strings. 

- **`s.allow()`** — an alias to
  `s.done(0)` (0.2.4)
- **`s.decline()`** — an alias to
  `s.done(-5)` (0.2.4)
- **`s.deny()`** — an alias to
  `s.done(403)` (0.2.4)
- **`s.done([*code*]`)** — sets an exit `code` for the current
  phase handler
  to a code value, by default `0`.
  The actual finalization happens when the js handler is completed
  and all pending events, for example, from
  `ngx.fetch()` or
  `setTimeout()`,
  are processed
  (0.2.4).
  
  Possible code values:
  - `0` — successful finalization, passing control to the next phase
  - `-5` — undecided, passing control to the next handler of the current phase (if any)
  - `403` — access is forbidden
  
  
  
  
  
  May be called only from a phase handler function:
  `js_access`
  or
  `js_preread`.
- **`s.error(*string*)`** — writes a sent `string` to the error log on the `error` level of logging > **Note:** As nginx has a hardcoded maximum line length limit, only first 2048 bytes of the string can be logged.
- **`s.log(*string*)`** — writes a sent *string* to the error log on the `info` level of logging > **Note:** As nginx has a hardcoded maximum line length limit, only first 2048 bytes of the string can be logged.
- **`s.off(*eventName*)`** — unregisters the callback set by the s.on() method (0.2.4)
- **`s.on(*event*,
*callback*)`** — registers a `callback`
  for the specified `event`
  (0.2.4).
  
  
  An `event` may be one of the following strings:
  - **`upload`** — new data (string) from a client
  - **`download`** — new data (string) to a client
  - **`upstream`** — new data (Buffer) from a client (since 0.5.0)
  - **`downstream`** — new data (Buffer) to a client (since 0.5.0)
  
  
  
  
  
  
  
  The completion callback has the following prototype:
  `callback(data, flags)`, where
  `data` is string or Buffer (depending on the event type)
  `flags` is an object
  with the following properties:
  - **`last`** — a boolean value, true if data is a last buffer.
- **`s.remoteAddress`** — client address, read-only
- **`s.rawVariables`** — nginx variables as Buffers, writable (since 0.5.0)
- **`s.jsVarNames(*[prefix]*)`** — returns a new array of names of nginx variables declared with the js_var directive (since 0.9.9). The optional *prefix* argument must be a string. If it is specified, only names that start with the prefix are returned.
- **`s.send(*data*[,
*options*])`** — adds data to the chain of data chunks that will be forwarded in
  the forward direction:
  in download callback to a client; in upload to an upstream server
  (0.2.4).
  The actual forwarding happens later,
  when the all the data chunks of the current chain are processed.
  
  The data can be a string or Buffer
  (0.5.0).
  The `options` is an object used
  to override nginx buffer flags derived from an incoming data chunk buffer.
  The flags can be overridden with the following flags:
  - **`last`** — boolean, true if the buffer is the last buffer
  - **`flush`** — boolean, true if the buffer should have the `flush` flag
  
  
  
  
  
  The method can be called multiple times per callback invocation.
- **`s.sendDownstream()`** — is identical to s.send(), except for it always sends data to a client (since 0.7.8).
- **`s.sendUpstream()`** — is identical to s.send(), except for it always sends data from a client (since 0.7.8).
- **`s.status`** — session status code, an alias to the
  `$status` variable, read only (since 0.5.2)
- **`s.setReturnValue(*value*)`** — sets the return value of the
  js_set handler
  (0.7.0).
  
  The method was made obsolete in
  0.9.5.
  Since this version, an `async` handler
  can return its value with an ordinary return statement:
  
  ```
  async function js_set(s) {
      const digest = await crypto.subtle.digest('SHA-256', s.remoteAddress);
      return Buffer.from(digest).toString('hex');
  }
  ```
- **`s.variables{}`** — nginx variables object, writable (since 0.2.8). A variable can be writable only if it is referenced in nginx configuration file. Even so, some embedded variables still cannot be assigned a value.
- **`s.warn(*string*)`** — writes a sent `string` to the error log on the `warning` level of logging > **Note:** As nginx has a hardcoded maximum line length limit, only first 2048 bytes of the string can be logged.

### Periodic Session

| `PeriodicSession.rawVariables{}` |
|---|
| `PeriodicSession.variables{}` |

 The `Periodic Session` object is provided as the first argument for the `js_periodic` handler for http and stream (since 0.8.1). 

- **`PeriodicSession.rawVariables{}`** — nginx variables as Buffers, writable.
- **`PeriodicSession.variables{}`** — nginx variables object, writable.

### Headers

| `Headers()` |
|---|
| `Headers.append()` |
| `Headers.delete()` |
| `Headers.get()` |
| `Headers.getAll()` |
| `Headers.forEach()` |
| `Headers.has()` |
| `Headers.set()` |

 The `Headers` interface of the
`Fetch API` is available since 0.5.1. 

A new `Headers` object can be created using the
`Headers()` constructor:
(since 0.7.10):

- **`Headers([*init*])`** — - **`init`** — An object containing HTTP headers for prepopulating the `Headers` object, can be a `string`, an `array` of name-value pairs, or an existing `Headers` object.

A new `Headers` object can be created
with the following properties and methods:

- **`append()`** — Appends a new value into an existing header in the
  `Headers` object, or adds the header if it does not already exist (since 0.7.10).
- **`delete()`** — Deletes a header from the `Headers` object (since 0.7.10).
- **`get()`** — Returns a string containing the values of all headers with the specified name separated by a comma and a space.
- **`getAll(*name*)`** — Returns an array containing the values of all headers with the specified name.
- **`forEach()`** — Executes a provided function once for each key/value pair in the `Headers` object (since 0.7.10).
- **`has()`** — Returns a boolean value indicating whether a header with the specified name exists.
- **`set()`** — Sets a new value for an existing header inside the `Headers` object, or adds the header if it does not already exist (since 0.7.10).

### Request

| `Request()` |
|---|
| `Request.arrayBuffer()` |
| `Request.bodyUsed` |
| `Request.cache` |
| `Request.credentials` |
| `Request.headers` |
| `Request.json()` |
| `Request.method` |
| `Request.mode` |
| `Request.text()` |
| `Request.url` |

 The `Request` interface of the
`Fetch API` is available since 0.7.10. 

A new `Request` object can be created using the
`Request()` constructor:

- **`Request[*resource*[,
*options*]])`** — Creates a `Request` object to fetch
  that can be passed later to
  `ngx.fetch()`.
  The `resource` can be a URL
  or an existing `Request` object.
  The `options` is an optional argument
  that is expected to be an object with the following keys:
  
  - **`body`** — The request body, by default is empty.
  - **`headers`** — The response headers object — the object containing HTTP headers for prepopulating the `Headers` object, can be a `string`, an `array` of name-value pairs, or an existing `Headers` object.
  - **`method`** — The HTTP method, by default the GET method is used.

A new `Request` object can be created
with the following properties and methods:

- **`arrayBuffer()`** — Returns a `Promise` that resolves with an `ArrayBuffer`.
- **`bodyUsed`** — A boolean value, `true` if the body was used in the request.
- **`cache`** — Contains the cache mode of the request.
- **`credentials`** — Contains the credentials of the request, by default is `same-origin`.
- **`headers`** — The `Headers` read-only object associated with the
  `Request`.
- **`json()`** — Returns a `Promise` that resolves with the result of parsing the request body as JSON.
- **`method`** — Contains the request method.
- **`mode`** — Contains the mode of the request.
- **`text()`** — Returns a `Promise` that resolves with a string representation of the request body.
- **`url`** — Contains the URL of the request.

### Response

| `Response()` |
|---|
| `Response.arrayBuffer()` |
| `Response.bodyUsed` |
| `Response.headers` |
| `Response.json()` |
| `Response.ok` |
| `Response.redirected` |
| `Response.status` |
| `Response.statusText` |
| `Response.text()` |
| `Response.type` |
| `Response.url` |

 The `Response` interface is available since 0.5.1. 

A new `Response` object can be created using the
`Response()` constructor
(since 0.7.10):

- **`Response[*body*[,
*options*]])`** — Creates a `Response` object.
  The `body` is an optional argument,
  can be a `string` or a `buffer`,
  by default is `null`.
  The `options` is an optional argument
  that is expected to be an object with the following keys:
  
  - **`headers`** — The response headers object — the object containing HTTP headers for prepopulating the `Headers` object, can be a `string`, an `array` of name-value pairs, or an existing `Headers` object.
  - **`status`** — The status code of the response.
  - **`statusText`** — The status message corresponding to the status code.

A new `Response()` object can be created
with the following properties and methods:

- **`arrayBuffer()`** — Takes a `Response` stream and reads it to completion. Returns a `Promise` that resolves with an `ArrayBuffer`.
- **`bodyUsed`** — A boolean value, `true` if the body was read.
- **`headers`** — The `Headers` read-only object associated with the
  `Response`.
- **`json()`** — Takes a `Response` stream and reads it to completion. Returns a `Promise` that resolves with the result of parsing the body text as JSON.
- **`ok`** — A boolean value, `true` if the response was successful (status codes between 200–299).
- **`redirected`** — A boolean value, `true` if the response is the result of a redirect.
- **`status`** — The status code of the response.
- **`statusText`** — The status message corresponding to the status code.
- **`text()`** — Takes a `Response` stream and reads it to completion. Returns a `Promise` that resolves with a string.
- **`type`** — The type of the response.
- **`url`** — The URL of the response.

### ngx

| `ngx.build` |
|---|
| `ngx.conf_file_path` |
| `ngx.conf_prefix` |
| `ngx.error_log_path` |
| `ngx.fetch()` |
| `ngx.log()` |
| `ngx.prefix` |
| `ngx.version` |
| `ngx.version_number` |
| `ngx.worker_id` |

The `ngx` global object is available
since 0.5.0.
- **`ngx.build`** — a string containing an optional nginx build name, corresponds to the
  `--build=name` argument of the configure script, by default is `""` (0.8.0)
- **`ngx.conf_file_path`** — a string containing the file path to current nginx configuration file (0.8.0)
- **`ngx.conf_prefix`** — a string containing the file path to nginx configuration prefix — the directory where nginx is currently looking for configuration (0.7.8)
- **`ngx.error_log_path`** — a string containing the file path to the current error log file (0.8.0)
- **`ngx.fetch(*resource*,
[*options*])`** — Makes a request to fetch a *resource* (0.5.1), which can be an URL or the `Request` object (0.7.10). Returns a `Promise` that resolves with the `Response` object. Since 0.7.0, the `https://` scheme is supported, redirects are not handled. 
  
  
  
   If the URL in the *resource* is specified as a domain name, it is determined using a resolver. If the `https://` scheme is specified, the js_fetch_trusted_certificate directive should be configured for the authentication of the *resource*'s HTTPS server. 
  
  
  
  
  The `options` parameter is expected to be an object
  with the following keys:
  - **`body`** — request body, by default is empty
  - **`buffer_size`** — the buffer size for reading the response, by default is `4096`
  - **`headers`** — request headers object
  - **`max_response_body_size`** — the maximum size of the response body in bytes, by default is `32768`
  - **`method`** — HTTP method, by default the `GET` method is used
  - **`verify`** — enables or disables verification of the HTTPS server certificate, by default is `true` (0.7.0)
  
  
  Example:
  
  ```
  let reply = await ngx.fetch('http://nginx.org/');
  let body = await reply.text();
  
  r.return(200, body);
  ```
- **`ngx.log`(*level*,
*message*)** — writes a message to the error log with the specified level of logging. The *level* parameter specifies one of the log levels, the *message* parameter can be a string or Buffer. The following log levels can be specified:
  `ngx.INFO`,
  `ngx.WARN`, and
  `ngx.ERR`. > **Note:** As nginx has a hardcoded maximum line length limit, only first 2048 bytes of the string can be logged.
- **`ngx.prefix`** — a string containing the file path to nginx prefix — a directory that keeps server files (0.8.0)
- **`ngx.version`** — a string containing nginx version, for example: `1.25.0` (0.8.0)
- **`ngx.version_number`** — a number containing nginx version, for example: `1025000` (0.8.0)
- **`ngx.worker_id`** — a number that corresponds to nginx internal worker id, the value is between `0` and the value specified in the worker_processes directive (0.8.0)

### ngx.shared

 The `ngx.shared` global object is available since 0.8.0. 

#### SharedDict

| `ngx.shared.SharedDict.add()` |
|---|
| `ngx.shared.SharedDict.capacity` |
| `ngx.shared.SharedDict.clear()` |
| `ngx.shared.SharedDict.delete()` |
| `ngx.shared.SharedDict.freeSpace()` |
| `ngx.shared.SharedDict.get()` |
| `ngx.shared.SharedDict.has()` |
| `ngx.shared.SharedDict.incr()` |
| `ngx.shared.SharedDict.items()` |
| `ngx.shared.SharedDict.keys()` |
| `ngx.shared.SharedDict.name` |
| `ngx.shared.SharedDict.pop()` |
| `ngx.shared.SharedDict.replace()` |
| `ngx.shared.SharedDict.set()` |
| `ngx.shared.SharedDict.size()` |
| `ngx.shared.SharedDict.ttl()` |
| `ngx.shared.SharedDict.type` |

 The shared dictionary object is available since 0.8.0. The shared dictionary name, type, and size are set with the `js_shared_dict_zone` directive in http or stream. 

A `SharedDict()` object
has the following properties and methods:
- **`ngx.shared.SharedDict.add(*key*,
*value* [,*timeout*])`** — Sets the `value` for the specified `key` in the dictionary only if the key does not exist yet. The `key` is a string representing the key of the item to add, the `value` is the value of the item to add. The optional `timeout` argument is specified in milliseconds and overrides the `timeout` parameter of the
  `js_shared_dict_zone` directive in http or stream (since 0.8.5). It can be useful when some keys are expected to have unique timeouts.    Returns `true` if the value has been successfully added to  the `SharedDict` dictionary,
  `false` if the key already exists in the dictionary. Throws `SharedMemoryError` if there is not enough free space in the `SharedDict` dictionary. Throws `TypeError` if the `value` is of a different type than expected by this dictionary.
- **`ngx.shared.SharedDict.capacity`** — Returns the capacity of the `SharedDict` dictionary, corresponds to the `size` parameter of
  `js_shared_dict_zone` directive in http or stream.
- **`ngx.shared.SharedDict.clear()`** — Removes all items from the `SharedDict` dictionary.
- **`ngx.shared.SharedDict.delete(*key*)`** — Removes the item associated with the specified key from the `SharedDict` dictionary,
  `true` if the item in the dictionary existed and was removed,
  `false` otherwise.
- **`ngx.shared.SharedDict.freeSpace()`** — Returns the free page size in bytes. If the size is zero, the `SharedDict` dictionary will still accept new values if there is space in the occupied pages.
- **`ngx.shared.SharedDict.get(*key*)`** — Retrieves the item by its `key`, returns the value associated with the `key` or `undefined` if there is none.
- **`ngx.shared.SharedDict.has(*key*)`** — Searches for an item by its `key`, returns `true` if such item exists or
  `false` otherwise.
- **`ngx.shared.SharedDict.incr(*key*,*delta*[[,*init*], *timeout*]))`** — Increments the integer value associated with the `key` by `delta`. The `key` is a string, the `delta` is the number to increment or decrement the value by. If the key does not exist, the item will be initialized to an optional `init` argument, by default is `0`.  The optional `timeout` argument is specified in milliseconds and overrides the `timeout` parameter of the
  `js_shared_dict_zone` directive in http or stream (since 0.8.5). If the `timeout` argument is not specified, the existing per-entry TTL is preserved (since 0.9.7). Before version 0.9.7, omitting `timeout` would reset the entry expiry to the directive default.    Returns the new value. Throws `SharedMemoryError` if there is not enough free space in the `SharedDict` dictionary. Throws `TypeError` if this dictionary does not expect numbers.    > **Note:** This method can be used only if the dictionary type was declared with > `type=number` parameter of the > `js_shared_dict_zone` directive in http or stream.
- **`ngx.shared.SharedDict.items([*maxCount*])`** — Returns an array of the `SharedDict` dictionary key-value items (since 0.8.1). The `maxCount` parameter sets maximum number of items to retrieve, by default is `1024`.
- **`ngx.shared.SharedDict.keys([*maxCount*])`** — Returns an array of the `SharedDict` dictionary keys. The `maxCount` parameter sets maximum number of keys to retrieve, by default is `1024`.
- **`ngx.shared.SharedDict.name`** — Returns the name of the `SharedDict` dictionary, corresponds to the `zone=` parameter of
  `js_shared_dict_zone` directive in http or stream.
- **`ngx.shared.SharedDict.pop(*key*)`** — Removes the item associated with the specified `key` from the `SharedDict` dictionary, returns the value associated with the `key` or `undefined` if there is none.
- **`ngx.shared.SharedDict.replace(*key*,
*value*)`** — Replaces the `value` for the specified `key` only if the key already exists, returns `true` if the value was successfully replaced,
  `false` if the key does not exist in the `SharedDict` dictionary. Throws `SharedMemoryError` if there is not enough free space in the `SharedDict` dictionary. Throws `TypeError` if the `value` is of a different type than expected by this dictionary.
- **`ngx.shared.SharedDict.set(*key*,
*value* [,*timeout*])`** — Sets the `value` for the specified `key`, returns this `SharedDict` dictionary (for method chaining).  The optional `timeout` argument is specified in milliseconds and overrides the `timeout` parameter of the
  `js_shared_dict_zone` directive in http or stream (since 0.8.5). It can be useful when some keys are expected to have unique timeouts.
- **`ngx.shared.SharedDict.size()`** — Returns the number of items for the `SharedDict` dictionary.
- **`ngx.shared.SharedDict.ttl(*key*)`** — Returns the remaining time-to-live in milliseconds for the specified `key`, or `undefined` if the key does not exist or has expired (since 0.9.7).  Throws `TypeError` if the dictionary was declared without the `timeout` parameter of the
  `js_shared_dict_zone` directive in http or stream.
- **`ngx.shared.SharedDict.type`** — Returns `string` or `number` that corresponds to the `SharedDict` dictionary type set by the `type=` parameter of
  `js_shared_dict_zone` directive in http or stream.

## built-in objects

### console

| `console.error()` |
|---|
| `console.info()` |
| `console.log()` |
| `console.time()` |
| `console.timeEnd()` |
| `console.warn()` |

The `console` object is available
in nginx since 0.8.2,
in CLI since 0.2.6.
- **`console.error(*msg*[, *msg2* ...])`** — Outputs one or more error messages. The message may be a string or an object.
- **`console.info(*msg*[, *msg2* ...])`** — Outputs one or more info messages. The message may be a string or an object.
- **`console.log(*msg*[, *msg2* ...])`** — Outputs one or more log messages. The message may be a string or an object.
- **`console.time(*label*)`** — Starts a timer that can track how long an operation takes. The `label` parameter allows naming different timers. If `console.timeEnd()` with the same name is called, the time that elapsed since the timer was started will be output, in milliseconds.
- **`console.timeEnd(*label*)`** — Stops a timer previously started by
  `console.time()` The `label` parameter allows naming different timers.
- **`console.warn(*msg*[, *msg2* ...])`** — Outputs one or more warning messages. The message may be a string or an object.

### crypto

| `сrypto.getRandomValues()` |
|---|
| `сrypto.randomUUID()` |
| `сrypto.subtle.encrypt()` |
| `сrypto.subtle.decrypt()` |
| `сrypto.subtle.deriveBits()` |
| `сrypto.subtle.deriveKey()` |
| `сrypto.subtle.digest()` |
| `сrypto.subtle.exportKey()` |
| `сrypto.subtle.generateKey()` |
| `сrypto.subtle.importKey()` |
| `сrypto.subtle.sign()` |
| `сrypto.subtle.verify()` |
| `сrypto.subtle.wrapKey()` |
| `сrypto.subtle.unwrapKey()` |

 The `crypto` object is a global object that allows using cryptographic functionality (since 0.7.0). Since 0.9.7, the full [Web Crypto API](https://www.w3.org/TR/webcrypto-2/) specification is supported. 

- **`сrypto.getRandomValues`(`typedArray`)** — Gets cryptographically strong random values.
  Returns the same array passed as `typedArray`
  but with its contents replaced with the newly generated random numbers.
  Possible values:
  
  - **`typedArray`** — can be
    `Int8Array`,
    `Int16Array`,
    `Uint16Array`,
    `Int32Array`, or
    `Uint32Array`
- **`сrypto.randomUUID`()** — Returns a randomly generated, 36 character long v4 UUID string, for example `"36b8f84d-df4e-4d49-b662-bcde71a8764f"` (since 0.9.7).
- **`сrypto.subtle.encrypt`(`algorithm`,
`key`,
`data`)** — Encrypts `data`
  using the provided
  `algorithm` and
  `key`.
  Returns a `Promise` that fulfills with
  an `ArrayBuffer` containing the ciphertext.
  Possible values:
  
  - **`algorithm`** — an object that specifies
    the algorithm to be used and any extra parameters if required:
    
    - for `RSA-OAEP`,
      pass the object with the following keys:
      
      - `name` is a string,
        should be set to `RSA-OAEP`:
        
        
        ```
        crypto.subtle.encrypt({name: "RSA-OAEP"}, key, data)
        ```
    - for `AES-CTR`,
      pass the object with the following keys:
      
      - `name` is a string, should be set to `AES-CTR`
      - `counter` is an
        `ArrayBuffer`,
        `TypedArray`, or
        `DataView` — the initial value of the counter block, must be 16 bytes long (the AES block size). The rightmost length bits of this block are used for the counter, and the rest is used for the nonce. For example, if length is set to 64, then the first half of counter is the nonce and the second half is used for the counter
      - `length` is the number of bits in the counter block that are used for the actual counter. The counter must be big enough that it doesn't wrap.
    - for `AES-CBC`, pass the object with the following keys:
      
      - `name` is a string, should be set to `AES-CBC`
      - `iv` or the initialization vector, is an
        `ArrayBuffer`,
        `TypedArray`, or
        `DataView`, must be 16 bytes, unpredictable, and preferably cryptographically random. However, it need not be secret, for example, it may be transmitted unencrypted along with the ciphertext.
    - for `AES-GCM`, pass the object with the following keys:
      
      - `name` is a string, should be set to `AES-GCM`
      - `iv` or the initialization vector, is an
        `ArrayBuffer`,
        `TypedArray`, or
        `DataView`, must be 16 bytes, and must be unique for every encryption operation carried out with a given key
      - `additionalData` (optional) is an
        `ArrayBuffer`,
        `TypedArray`, or
        `DataView` that contains additional data that will not be encrypted but will be authenticated along with the encrypted data. If `additionalData` is specified, then the same data must be specified in the corresponding call to
        `decrypt()`: if the data given to the `decrypt()` call does not match the original data, the decryption will throw an exception. The bit length of `additionalData` must be smaller than `2^64 - 1`.
      - `tagLength` (optional, default is `128`) - a `number` that determines the size in bits of the authentication tag generated in the encryption operation and used for authentication in the corresponding decryption Possible values:
        `32`,
        `64`,
        `96`,
        `104`,
        `112`,
        `120`, or
        `128`. The AES-GCM specification recommends that it should be
        `96`,
        `104`,
        `112`,
        `120`, or
        `128`, although
        `32` or
        `64` bits may be acceptable in some applications.
  - **`key`** — a `CryptoKey` that contains the key to be used for encryption
  - **`data`** — an
    `ArrayBuffer`,
    `TypedArray`, or
    `DataView` that contains the data to be encrypted (also known as the plaintext)
- **`сrypto.subtle.decrypt`(`algorithm`,
`key`,
`data`)** — Decrypts encrypted data.
  Returns a `Promise` with the decrypted data.
  Possible values:
  
  - **`algorithm`** — an object
    that specifies the algorithm to be used, and any extra parameters as required.
    The values given for the extra parameters must match
    those passed into the corresponding `encrypt()` call.
    
    - for `RSA-OAEP`,
      pass the object with the following keys:
      
      - `name` is a string,
        should be set to `RSA-OAEP`:
        
        
        ```
        crypto.subtle.encrypt({name: "RSA-OAEP"}, key, data)
        ```
    - for `AES-CTR`,
      pass the object with the following keys:
      
      - `name` is a string, should be set to `AES-CTR`
      - `counter` is an
        `ArrayBuffer`,
        `TypedArray`, or
        `DataView` — the initial value of the counter block, must be 16 bytes long (the AES block size). The rightmost length bits of this block are used for the counter, and the rest is used for the nonce. For example, if length is set to 64, then the first half of counter is the nonce and the second half is used for the counter.
      - `length` is the number of bits in the counter block that are used for the actual counter. The counter must be big enough that it doesn't wrap.
    - for `AES-CBC`, pass the object with the following keys:
      
      - `name` is a string, should be set to `AES-CBC`
      - `iv` or the initialization vector, is an
        `ArrayBuffer`,
        `TypedArray`, or
        `DataView`, must be 16 bytes, unpredictable, and preferably cryptographically random. However, it need not be secret (for example, it may be transmitted unencrypted along with the ciphertext).
    - for `AES-GCM`, pass the object with the following keys:
      
      - `name` is a string, should be set to `AES-GCM`
      - `iv` or the initialization vector, is an
        `ArrayBuffer`,
        `TypedArray`, or
        `DataView`, must be 16 bytes, and must be unique for every encryption operation carried out with a given key
      - `additionalData` (optional) is an
        `ArrayBuffer`,
        `TypedArray`, or
        `DataView` that contains additional data that will not be encrypted but will be authenticated along with the encrypted data. If `additionalData` is specified, then the same data must be specified in the corresponding call to
        `decrypt()`: if the data given to the `decrypt()` call does not match the original data, the decryption will throw an exception. The bit length of `additionalData` must be smaller than `2^64 - 1`.
      - `tagLength` (optional, default is `128`) - a `number` that determines the size in bits of the authentication tag generated in the encryption operation and used for authentication in the corresponding decryption. Possible values:
        `32`,
        `64`,
        `96`,
        `104`,
        `112`,
        `120`, or
        `128`. The AES-GCM specification recommends that it should be
        `96`,
        `104`,
        `112`,
        `120`, or
        `128`, although
        `32` or
        `64` bits may be acceptable in some applications.
  - **`key`** — a `CryptoKey` that contains the key to be used for decryption. If `RSA-OAEP` is used, this is the
    `privateKey` property of the
    `CryptoKeyPair` object.
  - **`data`** — an
    `ArrayBuffer`,
    `TypedArray`, or
    `DataView` that contains the data to be decrypted (also known as ciphertext)
- **`сrypto.subtle.deriveBits`(`algorithm`,
`baseKey`,
`length`)** — Derives an array of bits from a base key.
  Returns a `Promise`
  which will be fulfilled with an
  `ArrayBuffer` that contains the derived bits.
  Possible values:
  
  - **`algorithm`** — is an object that defines the derivation algorithm to use:
    
    - for `HKDF`,
      pass the object with the following keys:
      
      - `name` is a string, should be set to `HKDF`
      - `hash` is a string with the digest algorithm to use:
        `SHA-1`,
        `SHA-256`,
        `SHA-384`, or
        `SHA-512`
      - `salt` is an
        `ArrayBuffer`,
        `TypedArray`, or
        `DataView` that represents random or pseudo-random value with the same length as the output of the `digest` function. Unlike the input key material passed into `deriveKey()`, salt does not need to be kept secret.
      - `info` is an
        `ArrayBuffer`,
        `TypedArray`, or
        `DataView` that represents application-specific contextual information used to bind the derived key to an application or context, and enables deriving different keys for different contexts while using the same input key material. This property is required but may be an empty buffer.
    - for `PBKDF2`,
      pass the object with the following keys:
      
      - `name` is a string, should be set to `PBKDF2`
      - `hash` is a string with the digest algorithm to use:
        `SHA-1`,
        `SHA-256`,
        `SHA-384`, or
        `SHA-512`
      - `salt` is an
        `ArrayBuffer`,
        `TypedArray`, or
        `DataView` that represents random or pseudo-random value of at least `16` bytes. Unlike the input key material passed into `deriveKey()`, salt does not need to be kept secret.
      - `iterations` is a `number` that represents the number of times the hash function will be executed in `deriveKey()`
    - for `ECDH`,
      pass the object with the following keys
      (since 0.9.1):
      
      - `name` is a string, should be set to `ECDH`
      - `public` is a `CryptoKey` that represents the public key of the other party. The key must be generated using the same curve as the base key.
    - for `X25519`,
      pass the object with the following keys
      (since 0.9.7):
      
      - `name` is a string, should be set to `X25519`
      - `public` is a `CryptoKey` that represents the public key of the other party
  - **`baseKey`** — is a `CryptoKey`
    that represents the input to the derivation algorithm
    - the initial key material for the derivation function:
    for example, for `PBKDF2` it might be a password,
    imported as a `CryptoKey` using
    `сrypto.subtle.importKey()`
  - **`length`** — is a number representing the number of bits to derive. For browsers compatibility, the number should be a multiple of `8`
- **`сrypto.subtle.deriveKey`(`algorithm`,
`baseKey`,
`derivedKeyAlgorithm`,
`extractable`,
`keyUsages`)** — Derives a secret key from a master key.
  Possible values:
  
  - **`algorithm`** — is an object that defines the derivation algorithm to use:
    
    - for `HKDF`,
      pass the object with the following keys:
      
      - `name` is a string, should be set to `HKDF`
      - `hash` is a string with the digest algorithm to use:
        `SHA-1`,
        `SHA-256`,
        `SHA-384`, or
        `SHA-512`
      - `salt` is an
        `ArrayBuffer`,
        `TypedArray`, or
        `DataView` that represents random or pseudo-random value with the same length as the output of the `digest` function. Unlike the input key material passed into `deriveKey()`, salt does not need to be kept secret.
      - `info` is an
        `ArrayBuffer`,
        `TypedArray`, or
        `DataView` that represents application-specific contextual information used to bind the derived key to an application or context, and enables deriving different keys for different contexts while using the same input key material. This property is required but may be an empty buffer.
    - for `PBKDF2`,
      pass the object with the following keys:
      
      - `name` is a string, should be set to `PBKDF2`
      - `hash` is a string with the digest algorithm to use:
        `SHA-1`,
        `SHA-256`,
        `SHA-384`, or
        `SHA-512`
      - `salt` is an
        `ArrayBuffer`,
        `TypedArray`, or
        `DataView` that represents random or pseudo-random value of at least `16` bytes. Unlike the input key material passed into `deriveKey()`, salt does not need to be kept secret.
      - `iterations` is a `number` that represents the number of times the hash function will be executed in `deriveKey()`
    - for `ECDH`,
      pass the object with the following keys
      (since 0.9.1):
      
      - `name` is a string, should be set to `ECDH`
      - `public` is a `CryptoKey` that represents the public key of the other party. The key must be generated using the same curve as the base key.
    - for `X25519`,
      pass the object with the following keys
      (since 0.9.7):
      
      - `name` is a string, should be set to `X25519`
      - `public` is a `CryptoKey` that represents the public key of the other party
  - **`baseKey`** — is a `CryptoKey`
    that represents the input to the derivation algorithm
    - the initial key material for the derivation function:
    for example, for `PBKDF2` it might be a password,
    imported as a `CryptoKey` using
    `сrypto.subtle.importKey()`.
  - **`derivedKeyAlgorithm`** — is an object
    that defines the algorithm the derived key will be used for:
    
    - for `HMAC`,
      pass the object with the following keys:
      
      - `name` is a string, should be set to `HMAC`
      - `hash` is a string with the name of the digest function to use:
        `SHA-1`,
        `SHA-256`,
        `SHA-384`, or
        `SHA-512`
      - `length` (optional) is a `number` that represents the length in bits of the key. If not specified, the length of the key is equal to the block size of the chozen hash function
    - for
      `AES-CTR`,
      `AES-CBC`,
      `AES-GCM`, or
      `AES-KW`
      (since 0.9.7),
      pass the object with the following keys:
      
      - `name` is a string, should be set to
        `AES-CTR`,
        `AES-CBC`,
        `AES-GCM`, or
        `AES-KW`, depending on the algorithm used
      - `length` is a `number` that represents the length in bits of the key to generate:
        `128`,
        `192`, or
        `256`
  - **`extractable`** — is a boolean value that indicates whether it will be possible to export the key
  - **`keyUsages`** — is an `Array`
    that indicates what can be done with the derived key.
    The key usages must be allowed by the algorithm
    set in `derivedKeyAlgorithm`.
    Possible values:
    - **`encrypt`** — key for encrypting messages
    - **`decrypt`** — key for decrypting messages
    - **`sign`** — key for signing messages
    - **`verify`** — key for verifying signatures
    - **`deriveKey`** — key for deriving a new key
    - **`deriveBits`** — key for deriving bits
    - **`wrapKey`** — key for wrapping a key
    - **`unwrapKey`** — key for unwrapping a key
- **`сrypto.subtle.digest`(`algorithm`,
`data`)** — Generates a digest of the given data.
  Takes as its arguments an identifier for the digest algorithm to use
  and the data to digest.
  Returns a `Promise` which will be fulfilled with the digest.
  Possible values:
  
  - **`algorithm`** — is a string that defines the hash function to use:
    `SHA-1` (not for cryptographic applications),
    `SHA-256`,
    `SHA-384`, or
    `SHA-512`
  - **`data`** — is an
    `ArrayBuffer`,
    `TypedArray`, or
    `DataView` that contains the data to be digested
- **`сrypto.subtle.exportKey`(`format`,
`key`)** — Exports a key: takes a key as
  a `CryptoKey` object
  and returns the key in an external, portable format
  (since 0.7.10).
  If the `format` was `jwk`,
  then the `Promise` fulfills with a JSON object
  containing the key.
  Otherwise, the promise fulfills with an
  `ArrayBuffer` containing the key.
  Possible values:
  - **`format`** — a string that describes the data format in which the key should be exported,
    can be the following:
    - **`raw`** — the raw data format
    - **`pkcs8`** — the [PKCS #8](https://datatracker.ietf.org/doc/html/rfc5208) format
    - **`spki`** — the [SubjectPublicKeyInfo](https://datatracker.ietf.org/doc/html/rfc5280#section-4.1) format
    - **`jwk`** — the [JSON Web Key](https://datatracker.ietf.org/doc/html/rfc7517) (JWK) format (since 0.7.10)
  - **`key`** — the `CryptoKey` that contains the key to be exported
- **`сrypto.subtle.generateKey`(`algorithm`,
`extractable`,
`usage`)** — Generates a new key for symmetric algorithms
  or key pair for public-key algorithms
  (since 0.7.10).
  Returns a `Promise` that fulfills with the generated key
  as
  a `CryptoKey`
  or `CryptoKeyPair` object.
  Possible values:
  - **`algorithm`** — a dictionary object that defines the type of key to generate
    and provides extra algorithm-specific parameters:
    
    - for
      `RSASSA-PKCS1-v1_5`,
      `RSA-PSS`, or
      `RSA-OAEP`,
      pass the object with the following keys:
      
      - `name` is a string, should be set to
        `RSASSA-PKCS1-v1_5`,
        `RSA-PSS`, or
        `RSA-OAEP`, depending on the used algorithm
      - `hash` is a string that represents the name of the `digest` function to use, can be
        `SHA-256`,
        `SHA-384`, or
        `SHA-512`
    - for
      `ECDSA`,
      pass the object with the following keys:
      
      - `name` is a string, should be set to `ECDSA`
      - `namedCurve` is a string that represents the name of the elliptic curve to use, may be
        `P-256`,
        `P-384`, or
        `P-521`
    - for
      `HMAC`,
      pass the object with the following keys:
      
      - `name` is a string, should be set to `HMAC`
      - `hash` is a string that represents the name of the `digest` function to use, can be
        `SHA-256`,
        `SHA-384`, or
        `SHA-512`
      - `length` (optional) is a number that represents the length in bits of the key. If omitted, the length of the key is equal to the length of the digest generated by the chosen digest function.
    - for
      `AES-CTR`,
      `AES-CBC`,
      `AES-GCM`, or
      `AES-KW` (since 0.9.7), pass the string identifying the algorithm or an object of the form `{ "name": "ALGORITHM" }`, where `ALGORITHM` is the name of the algorithm
    - for
      `ECDH`,
      pass the object with the following keys
      (since 0.9.1):
      
      - `name` is a string, should be set to `ECDH`
      - `namedCurve` is a string that represents the name of the elliptic curve to use, may be
        `P-256`,
        `P-384`, or
        `P-521`
    - for `Ed25519`, pass the `Ed25519` string or an object of the form `{ "name": "Ed25519" }` (since 0.9.7)
    - for `X25519`, pass the `X25519` string or an object of the form `{ "name": "X25519" }` (since 0.9.7)
  - **`extractable`** — boolean value that indicates if it is possible to export the key
  - **`usage`** — an `array` that indicates possible actions with the key:
    - **`encrypt`** — key for encrypting messages
    - **`decrypt`** — key for decrypting messages
    - **`sign`** — key for signing messages
    - **`verify`** — key for verifying signatures
    - **`deriveKey`** — key for deriving a new key
    - **`deriveBits`** — key for deriving bits
    - **`wrapKey`** — key for wrapping a key
    - **`unwrapKey`** — key for unwrapping a key
- **`сrypto.subtle.importKey`(`format`,
`keyData`,
`algorithm`,
`extractable`,
`keyUsages`)** — Imports a key: takes as input a key in an external, portable format
  and gives a `CryptoKey` object.
  Returns a `Promise` that fulfills with the imported key
  as a `CryptoKey` object.
  Possible values:
  - **`format`** — a string that describes the data format of the key to import,
    can be the following:
    - **`raw`** — the raw data format
    - **`pkcs8`** — the [PKCS #8](https://datatracker.ietf.org/doc/html/rfc5208) format
    - **`spki`** — the [SubjectPublicKeyInfo](https://datatracker.ietf.org/doc/html/rfc5280#section-4.1) format
    - **`jwk`** — the [JSON Web Key](https://datatracker.ietf.org/doc/html/rfc7517) (JWK) format (since 0.7.10)
  - **`keyData`** — the
    `ArrayBuffer`,
    `TypedArray`, or
    `DataView` object that contains the key in the given format
  - **`algorithm`** — a dictionary object that defines the type of key to import
    and provides extra algorithm-specific parameters:
    
    - for
      `RSASSA-PKCS1-v1_5`,
      `RSA-PSS`, or
      `RSA-OAEP`,
      pass the object with the following keys:
      
      - `name` is a string, should be set to
        `RSASSA-PKCS1-v1_5`,
        `RSA-PSS`, or
        `RSA-OAEP`, depending on the used algorithm
      - `hash` is a string that represents the name of the `digest` function to use, can be
        `SHA-1`,
        `SHA-256`,
        `SHA-384`, or
        `SHA-512`
    - for
      `ECDSA`,
      pass the object with the following keys:
      
      - `name` is a string, should be set to `ECDSA`
      - `namedCurve` is a string that represents the name of the elliptic curve to use, may be
        `P-256`,
        `P-384`, or
        `P-521`
    - for
      `HMAC`,
      pass the object with the following keys:
      
      - `name` is a string, should be set to `HMAC`
      - `hash` is a string that represents the name of the `digest` function to use, can be
        `SHA-256`,
        `SHA-384`, or
        `SHA-512`
      - `length` (optional) is a number that represents the length in bits of the key. If omitted, the length of the key is equal to the length of the digest generated by the chosen digest function.
    - for
      `AES-CTR`,
      `AES-CBC`,
      `AES-GCM`, or
      `AES-KW` (since 0.9.7), pass the string identifying the algorithm or an object of the form `{ "name": "ALGORITHM" }`, where `ALGORITHM` is the name of the algorithm
    - for
      `PBKDF2`, pass the `PBKDF2` string
    - for
      `HKDF`, pass the `HKDF` string
    - for
      `ECDH`,
      pass the object with the following keys
      (since 0.9.1):
      
      - `name` is a string, should be set to `ECDH`
      - `namedCurve` is a string that represents the name of the elliptic curve to use, may be
        `P-256`,
        `P-384`, or
        `P-521`
    - for `Ed25519`, pass the `Ed25519` string or an object of the form `{ "name": "Ed25519" }` (since 0.9.7)
    - for `X25519`, pass the `X25519` string or an object of the form `{ "name": "X25519" }` (since 0.9.7)
  - **`extractable`** — boolean value that indicates if it is possible to export the key
  - **`keyUsages`** — an `array` that indicates possible actions with the key:
    - **`encrypt`** — key for encrypting messages
    - **`decrypt`** — key for decrypting messages
    - **`sign`** — key for signing messages
    - **`verify`** — key for verifying signatures
    - **`deriveKey`** — key for deriving a new key
    - **`deriveBits`** — key for deriving bits
    - **`wrapKey`** — key for wrapping a key
    - **`unwrapKey`** — key for unwrapping a key
- **`сrypto.subtle.sign`(`algorithm`,
`key`,
`data`)** — Returns `signature` as a `Promise`
  that fulfills with an `ArrayBuffer` containing the signature.
  Possible values:
  
  - **`algorithm`** — is a string or object that specifies the signature algorithm to use
    and its parameters:
    
    - for `RSASSA-PKCS1-v1_5`, pass the string identifying the algorithm or an object of the form `{ "name": "ALGORITHM" }`
    - for `RSA-PSS`,
      pass the object with the following keys:
      - `name` is a string, should be set to
        `RSA-PSS`
      - `saltLength` is a long `integer` that represents the length of the random salt to use, in bytes
    - for `ECDSA`,
      pass the object with the following keys:
      - `name` is a string, should be set to
        `ECDSA`
      - `hash` is an identifier for the digest algorithm to use, can be
        `SHA-256`,
        `SHA-384`, or
        `SHA-512`
    - for  `HMAC`, pass the string identifying the algorithm or an object of the form `{ "name": "ALGORITHM" }`
    - for `Ed25519`, pass the `Ed25519` string or an object of the form `{ "name": "Ed25519" }` (since 0.9.7)
  - **`key`** — is a `CryptoKey` object that the key to be used for signing. If algorithm identifies a public-key cryptosystem, this is the private key.
  - **`data`** — is an
    `ArrayBuffer`,
    `TypedArray`, or
    `DataView` object that contains the data to be signed
- **`сrypto.subtle.verify`(`algorithm`,
`key`,
`signature`,
`data`)** — Verifies a digital signature,
  returns a `Promise` that fulfills with a boolean value:
  `true` if the signature is valid,
  otherwise `false`.
  Possible values:
  
  - **`algorithm`** — is a string or object that specifies the algorithm to use
    and its parameters:
    
    - for `RSASSA-PKCS1-v1_5`, pass the string identifying the algorithm or an object of the form `{ "name": "ALGORITHM" }`
    - for `RSA-PSS`,
      pass the object with the following keys:
      - `name` is a string, should be set to
        `RSA-PSS`
      - `saltLength` is a long `integer` that represents the length of the random salt to use, in bytes
    - for `ECDSA`,
      pass the object with the following keys:
      - `name` is a string, should be set to
        `ECDSA`
      - `hash` is an identifier for the digest algorithm to use, can be
        `SHA-256`,
        `SHA-384`, or
        `SHA-512`
    - for  `HMAC`, pass the string identifying the algorithm or an object of the form `{ "name": "ALGORITHM" }`
    - for `Ed25519`, pass the `Ed25519` string or an object of the form `{ "name": "Ed25519" }` (since 0.9.7)
  - **`key`** — is a `CryptoKey` object that the key to be used for verifying. It is the secret key for a symmetric algorithm and the public key for a public-key system.
  - **`signature`** — is an
    `ArrayBuffer`,
    `TypedArray`, or
    `DataView` that contains the signature to verify
  - **`data`** — is an
    `ArrayBuffer`,
    `TypedArray`, or
    `DataView` object that contains the data whose signature is to be verified
- **`сrypto.subtle.wrapKey`(`format`,
`key`,
`wrappingKey`,
`wrapAlgorithm`)** — Wraps a key: exports a key in an external, portable format,
  then encrypts the exported key
  (since 0.9.7).
  Returns a `Promise` that fulfills with
  an `ArrayBuffer` containing the encrypted exported key.
  Possible values:
  
  - **`format`** — a string that describes the data format of the key to export
    before it is encrypted,
    can be the following:
    - **`raw`** — the raw data format
    - **`pkcs8`** — the [PKCS #8](https://datatracker.ietf.org/doc/html/rfc5208) format
    - **`spki`** — the [SubjectPublicKeyInfo](https://datatracker.ietf.org/doc/html/rfc5280#section-4.1) format
    - **`jwk`** — the [JSON Web Key](https://datatracker.ietf.org/doc/html/rfc7517) (JWK) format
  - **`key`** — a `CryptoKey` that contains the key to be wrapped. The key must have
    `CryptoKey.extractable` set to `true`.
  - **`wrappingKey`** — a `CryptoKey` that contains the key used to encrypt the exported key. The key must have the `wrapKey` usage set.
  - **`wrapAlgorithm`** — an object that specifies the algorithm to be used
    to encrypt the exported key, and any extra parameters as required:
    
    - for `AES-CBC`,
      `AES-CTR`, or
      `AES-GCM`, pass the corresponding algorithm parameters as described in
      `сrypto.subtle.encrypt()`
    - for `AES-KW`, pass the `AES-KW` string or an object of the form `{ "name": "AES-KW" }`
    - for `RSA-OAEP`, pass the corresponding algorithm parameters as described in
      `сrypto.subtle.encrypt()`
- **`сrypto.subtle.unwrapKey`(`format`,
`wrappedKey`,
`unwrappingKey`,
`unwrapAlgorithm`,
`unwrappedKeyAlgorithm`,
`extractable`,
`keyUsages`)** — Unwraps a key: decrypts a wrapped key
  and creates a `CryptoKey` object
  from the result
  (since 0.9.7).
  Returns a `Promise` that fulfills with
  the unwrapped key as a `CryptoKey`.
  Possible values:
  
  - **`format`** — a string that describes the data format of the key
    that was wrapped,
    can be the following:
    - **`raw`** — the raw data format
    - **`pkcs8`** — the [PKCS #8](https://datatracker.ietf.org/doc/html/rfc5208) format
    - **`spki`** — the [SubjectPublicKeyInfo](https://datatracker.ietf.org/doc/html/rfc5280#section-4.1) format
    - **`jwk`** — the [JSON Web Key](https://datatracker.ietf.org/doc/html/rfc7517) (JWK) format
  - **`wrappedKey`** — an
    `ArrayBuffer`,
    `TypedArray`, or
    `DataView` that contains the wrapped key in the given format
  - **`unwrappingKey`** — a `CryptoKey` that contains the key used to decrypt the wrapped key. The key must have the `unwrapKey` usage set.
  - **`unwrapAlgorithm`** — an object that specifies the algorithm to be used
    to decrypt the wrapped key, and any extra parameters as required:
    
    - for `AES-CBC`,
      `AES-CTR`, or
      `AES-GCM`, pass the corresponding algorithm parameters as described in
      `сrypto.subtle.encrypt()`
    - for `AES-KW`, pass the `AES-KW` string or an object of the form `{ "name": "AES-KW" }`
    - for `RSA-OAEP`, pass the corresponding algorithm parameters as described in
      `сrypto.subtle.encrypt()`
  - **`unwrappedKeyAlgorithm`** — a dictionary object that defines the type of key to unwrap and provides extra algorithm-specific parameters. The same algorithm descriptions as in
    `сrypto.subtle.importKey()` apply.
  - **`extractable`** — boolean value that indicates if it is possible to export the key
  - **`keyUsages`** — an `array` that indicates possible actions with the key:
    - **`encrypt`** — key for encrypting messages
    - **`decrypt`** — key for decrypting messages
    - **`sign`** — key for signing messages
    - **`verify`** — key for verifying signatures
    - **`deriveKey`** — key for deriving a new key
    - **`deriveBits`** — key for deriving bits
    - **`wrapKey`** — key for wrapping a key
    - **`unwrapKey`** — key for unwrapping a key

### CryptoKey

| `CryptoKey.algorithm` |
|---|
| `CryptoKey.extractable` |
| `CryptoKey.type` |
| `CryptoKey.usages` |

 The `CryptoKey` object represents a cryptographic `key` obtained from one of the `SubtleCrypto` methods:
`сrypto.subtle.generateKey()`,
`сrypto.subtle.deriveKey()`,
`сrypto.subtle.importKey()`. 

- **`CryptoKey.algorithm`** — returns an object describing the algorithm for which this key can be used and any associated extra parameters (since 0.8.0), read-only
- **`CryptoKey.extractable`** — a boolean value, `true` if the key can be exported (since 0.8.0), read-only
- **`CryptoKey.type`** — a string value that indicates which kind of key is represented by the object,
  read-only.
  Possible values:
  - **`secret`** — This key is a secret key for use with a symmetric algorithm.
  - **`private`** — This key is the private half of an asymmetric algorithm's
    `CryptoKeyPair`
  - **`public`** — This key is the public half of an asymmetric algorithm's
    `CryptoKeyPair`.
- **`CryptoKey.usages`** — An array of strings indicating what this key can be used for
  (since 0.8.0),
  read-only.
  Possible array values:
  - **`encrypt`** — key for encrypting messages
  - **`decrypt`** — key for decrypting messages
  - **`sign`** — key for signing messages
  - **`verify`** — key for verifying signatures
  - **`deriveKey`** — key for deriving a new key
  - **`deriveBits`** — key for deriving bits

### CryptoKeyPair

| `CryptoKeyPair.privateKey` |
|---|
| `CryptoKeyPair.publicKey` |

 The `CryptoKeyPair` is a dictionary object of the WebCrypto API that represents an asymmetric key pair. 

- **`CryptoKeyPair.privateKey`** — A `CryptoKey` object representing the private key.
- **`CryptoKeyPair.publicKey`** — A `CryptoKey` object representing the public key.

### njs

| `njs.version` |
|---|
| `njs.version_number` |
| `njs.dump()` |
| `njs.memoryStats` |
| `njs.on()` |

 The `njs` object is a global object that represents the current VM instance (since 0.2.0). 

- **`njs.version`** — Returns a string with the current version of njs (for example, “0.7.4”).
- **`njs.version_number`** — Returns a number with the current version of njs. For example, “0.7.4” is returned as `0x000704` (since 0.7.4).
- **`njs.dump(*value*)`** — Returns the pretty-print string representation for a value.
- **`njs.memoryStats`** — Object containing memory statistics for current VM instance
  (since 0.7.8).
  - **`size`** — amount of memory in bytes njs memory pool claimed from the operating system.
- **`njs.on(*event*,
*callback*)`** — Registers a callback for the specified VM event
  (since 0.5.2).
  An event may be one of the following strings:
  - **`exit`** — is called before the VM is destroyed. The callback is called without arguments.

### process

| `process.argv` |
|---|
| `process.env` |
| `process.kill()` |
| `process.pid` |
| `process.ppid` |

 The `process` object is a global object that provides information about the current process (0.3.3). 

- **`process.argv`** — Returns an array that contains the command line arguments passed when the current process was launched.
- **`process.env`** — Returns an object containing the user environment. > **Note:** By default, nginx removes all environment variables inherited from its parent process except the TZ variable. Use the env directive to preserve some of the inherited variables.
- **`process.kill(*pid*,
*number* | *string*)`** — Sends the signal to the process identified by `pid`. Signal names are numbers or strings such as 'SIGINT' or 'SIGHUP'. See [kill(2)](https://man7.org/linux/man-pages/man2/kill.2.html) for more information.
- **`process.pid`** — Returns the PID of the current process.
- **`process.ppid`** — Returns the PID of the current parent process.

### String

 By default all strings in njs are Unicode strings. They correspond to ECMAScript strings that contain Unicode characters. Before 0.8.0, byte strings were also supported. 

#### Byte strings

 > **Note:** Since 0.8.0, the support for byte strings and byte string methods were removed. When working with byte sequence, the Buffer object and `Buffer` properties, such as > `r.requestBuffer`, > `r.rawVariables`, should be used.   

Byte strings contain a sequence of bytes
and are used to serialize Unicode strings
to external data and deserialize from external sources.
For example, the toUTF8() method serializes
a Unicode string to a byte string using UTF-8 encoding:

```
>> '£'.toUTF8().toString('hex')
'c2a3'  /* C2 A3 is the UTF-8 representation of 00A3 ('£') code point */
```

The toBytes() method serializes
a Unicode string with code points up to 255 into a byte string,
otherwise, `null` is returned:

```
>> '£'.toBytes().toString('hex')
'a3'  /* a3 is a byte equal to 00A3 ('£') code point  */
```

- **`String.bytesFrom(*array*
| *string*, *encoding*)`** — The method was made obsolete in
  0.4.4
  and was removed in 0.8.0.
  The `Buffer.from` method should be used instead:
  
  ```
  >> Buffer.from([0x62, 0x75, 0x66, 0x66, 0x65, 0x72]).toString()
  'buffer'
  
  >> Buffer.from('YnVmZmVy', 'base64').toString()
  'buffer'
  ```
  
  Before 0.4.4,
  created a byte string either from an array that contained octets,
  or from an encoded string
  (0.2.3),
  the encoding could be
  `hex`,
  `base64`, and
  `base64url`.
- **`String.prototype.fromBytes(*start*[,
*end*])`** — the property was made obsolete in 0.7.7 and was removed in 0.8.0. Before 0.7.7, returned a new Unicode string from a byte string where each byte was replaced with a corresponding Unicode code point.
- **`String.prototype.fromUTF8(*start*[,
*end*])`** — the property was made obsolete in 0.7.7 and was removed in 0.8.0. The `TextDecoder` method should be used instead. Before 0.7.7, converted a byte string containing a valid UTF-8 string into a Unicode string, otherwise `null` was returned.
- **`String.prototype.toBytes(*start*[,
*end*])`** — the property was made obsolete in 0.7.7 and was removed in 0.8.0. Before 0.7.7, serialized a Unicode string to a byte string, returned `null` if a character larger than 255 was found in the string.
- **`String.prototype.toString(*encoding*)`** — the property was made obsolete in
  0.7.7
  and was removed in 0.8.0.
  Before 0.7.7,
  encoded a string to
  `hex`,
  `base64`, or
  `base64url`:
  
  ```
  >>  'αβγδ'.toString('base64url')
  'zrHOss6zzrQ'
  ```
  
  Before version 0.4.3,
  only a byte string could be encoded:
  
  ```
  >>  'αβγδ'.toUTF8().toString('base64url')
  'zrHOss6zzrQ'
  ```
- **`String.prototype.toUTF8(*start*[,
*end*])`** — the property was made obsolete in
  0.7.7
  and was removed in 0.8.0.
  The `TextEncoder` method
  should be used instead.
  Before 0.7.7,
  serialized a Unicode string
  to a byte string using UTF-8 encoding:
  
  ```
  >> 'αβγδ'.toUTF8().length
  8
  >> 'αβγδ'.length
  4
  ```

## web API

### Text Decoder

| `TextDecoder()` |
|---|
| `TextDecoder.prototype.encoding` |
| `TextDecoder.prototype.fatal` |
| `TextDecoder.prototype.ignoreBOM` |
| `TextDecoder.prototype.decode()` |

 The `TextDecoder` produces a stream of code points from a stream of bytes (0.4.3). 

- **`TextDecoder([[*encoding*],
*options*])`** — Creates a new `TextDecoder` object
  for specified `encoding`,
  currently, only UTF-8 is supported.
  The `options` is
  `TextDecoderOptions` dictionary with the property:
  
  - **`fatal`** — boolean flag indicating if
    `TextDecoder.decode()` must throw the *TypeError* exception when a coding error is found, by default is `false`.
- **`TextDecoder.prototype.encoding`** — Returns a string with the name of the encoding used by
  `TextDecoder()`, read-only.
- **`TextDecoder.prototype.fatal`** — boolean flag, `true` if the error mode is fatal, read-only.
- **`TextDecoder.prototype.ignoreBOM`** — boolean flag, `true` if the byte order marker is ignored, read-only.
- **`TextDecoder.prototype.decode(*buffer*,
[*options*])`** — Returns a string with the text
  decoded from the `buffer` by
  `TextDecoder()`.
  The buffer can be `ArrayBuffer`.
  The `options` is
  `TextDecodeOptions` dictionary with the property:
  
  - **`stream`** — boolean flag indicating if additional data will follow in subsequent calls to `decode()`:
    `true` if processing the data in chunks, and
    `false` for the final chunk or if the data is not chunked. By default is `false`.
  
  
  
  ```
  >> (new TextDecoder()).decode(new Uint8Array([206,177,206,178]))
  αβ
  ```

### Text Encoder

| `TextEncoder()` |
|---|
| `TextEncoder.prototype.encode()` |
| `TextEncoder.prototype.encodeInto()` |

 The `TextEncoder` object produces a byte stream with UTF-8 encoding from a stream of code points (0.4.3). 

- **`TextEncoder()`** — Returns a newly constructed `TextEncoder` that will generate a byte stream with UTF-8 encoding.
- **`TextEncoder.prototype.encode(*string*)`** — Encodes `string` into a `Uint8Array` with UTF-8 encoded text.
- **`TextEncoder.prototype.encodeInto(*string*,
*uint8Array*)`** — Encodes a `string` to UTF-8,
  puts the result into destination `Uint8Array`, and
  returns a dictionary object that shows the progress of the encoding.
  The dictionary object contains two members:
  
  - **`read`** — the number of UTF-16 units of code from the source `string` converted to UTF-8
  - **`written`** — the number of bytes modified in the destination `Uint8Array`

## timers

| `clearTimeout()` |
|---|
| `setTimeout()` |

- **`clearTimeout(*timeout*)`** — Cancels a `timeout` object created by `setTimeout()`.
- **`setTimeout(*function*,
*milliseconds*[,
*argument1*,
*argumentN*])`** — Calls a `function`
  after a specified number of `milliseconds`.
  One or more optional `arguments`
  can be passed to the specified function.
  Returns a `timeout` object.
  
  ```
  function handler(v)
  {
      // ...
  }
  
  t = setTimeout(handler, 12);
  
  // ...
  
  clearTimeout(t);
  ```

### Global functions

| `atob()` |
|---|
| `btoa()` |

- **`atob(*encodedData*)`** — Decodes a string of data which has been encoded
  using `Base64` encoding.
  The `encodedData` parameter is a binary string
  that contains Base64-encoded data.
  Returns a string that contains decoded data from `encodedData`.
  
  The similar `btoa()` method
  can be used to encode and transmit data
  which may otherwise cause communication problems,
  then transmit it and use the `atob()` method
  to decode the data again.
  For example, you can encode, transmit, and decode control characters
  such as ASCII values `0` through `31`.
  
  ```
  const encodedData = btoa("text to encode"); // encode a string
  const decodedData = atob(encodedData); // decode the string
  ```
- **`btoa(*stringToEncode*)`** — Creates a Base64-encoded ASCII string from a binary string.
  The `stringToEncode` parameter is a binary string to encode.
  Returns an ASCII string containing the Base64 representation of
  `stringToEncode`.
  
  The method can be used to encode data
  which may otherwise cause communication problems, transmit it,
  then use the `atob()` method
  to decode the data again.
  For example, you can encode control characters
  such as ASCII values `0` through `31`.
  
  ```
  const encodedData = btoa("text to encode"); // encode a string
  const decodedData = atob(encodedData); // decode the string
  ```

## built-in modules

### Buffer

| `Buffer.alloc()` |
|---|
| `Buffer.allocUnsafe()` |
| `Buffer.byteLength()` |
| `Buffer.compare()` |
| `Buffer.concat()` |
| `Buffer.from(array)` |
| `Buffer.from(arrayBuffer)` |
| `Buffer.from(buffer)` |
| `Buffer.from(object)` |
| `Buffer.from(string)` |
| `Buffer.isBuffer()` |
| `Buffer.isEncoding()` |
| `buffer[]` |
| `buf.buffer` |
| `buf.byteOffset` |
| `buf.compare()` |
| `buf.copy()` |
| `buf.equals()` |
| `buf.fill()` |
| `buf.includes()` |
| `buf.indexOf()` |
| `buf.lastIndexOf()` |
| `buf.length` |
| `buf.readIntBE()` |
| `buf.readIntLE()` |
| `buf.readUIntBE()` |
| `buf.readUIntLE()` |
| `buf.readDoubleBE` |
| `buf.readDoubleLE()` |
| `buf.readFloatBE()` |
| `buf.readFloatLE()` |
| `buf.subarray()` |
| `buf.slice()` |
| `buf.swap16()` |
| `buf.swap32()` |
| `buf.swap64()` |
| `buf.toJSON()` |
| `buf.toString()` |
| `buf.write()` |
| `buf.writeIntBE()` |
| `buf.writeIntLE()` |
| `buf.writeUIntBE()` |
| `buf.writeUIntLE()` |
| `buf.writeDoubleBE()` |
| `buf.writeDoubleLE()` |
| `buf.writeFloatBE()` |
| `buf.writeFloatLE()` |

- **`Buffer.alloc(*size*[,
*fill*[,
*encoding*]]))`** — Allocates a new Buffer of a specified *size*. If *fill* is not specified, the Buffer will be zero-filled. If *fill* is specified, the allocated Buffer will be initialized by calling
  `buf.fill(fill)`. If *fill* and *encoding* are specified, the allocated Buffer will be initialized by calling
  `buf.fill(fill, encoding)`.    The *fill* parameter may be a *string*, *Buffer*, *Uint8Array*, or *integer*.
- **`Buffer.allocUnsafe(*size*)`** — The same as
  `Buffer.alloc()`, with the difference that the memory allocated for the buffer is not initialized, the contents of the new buffer is unknown and may contain sensitive data.
- **`Buffer.byteLength(*value*[,
*encoding*])`** — Returns the byte length of a specified value, when encoded using *encoding*. The value can be a
  `string`,
  `Buffer`,
  `TypedArray`,
  `DataView`, or
  `ArrayBuffer`. If the value is a *string*, the `encoding` parameter is its encoding, can be *utf8*, *hex*, *base64*, *base64url*; by default is *utf8*.
- **`Buffer.compare(*buffer1*,
*buffer2*)`** — Compares *buffer1* with *buffer2* when sorting arrays of Buffer instances. Returns
  `0` if *buffer1* is the same as *buffer2*,
  `1` if *buffer2* should come before *buffer1* when sorted, or
  `-1` if *buffer2* should come after *buffer1* when sorted.
- **`Buffer.concat(*list*[,
*totalLength*])`** — Returns a new Buffer which is the result of concatenating all the Buffer instances in the list. If there are no items in the list or the total length is 0, a new zero-length Buffer is returned. If *totalLength* is not specified, it is calculated from the Buffer instances in list by adding their lengths. If *totalLength* is specified, it is coerced to an unsigned integer. If the combined length of the Buffers in list exceeds *totalLength*, the result is truncated to *totalLength*.
- **`Buffer.from(*array*)`** — Allocates a new Buffer using an array of bytes in the range `0` – `255`. Array entries outside that range will be truncated.
- **`Buffer.from(*arrayBuffer*,
*byteOffset*[,
*length*]])`** — Creates a view of the *ArrayBuffer* without copying the underlying memory. The optional *byteOffset* and *length* arguments specify a memory range within the *arrayBuffer* that will be shared by the Buffer.
- **`Buffer.from(*buffer*)`** — Copies the passed buffer data onto a new Buffer instance.
- **`Buffer.from(*object*[,
*offsetOrEncoding*[,
*length*]])`** — For objects whose `valueOf()` function returns a value not strictly equal to object, returns
  `Buffer.from(object.valueOf()`,
  `offsetOrEncoding`,
  `length`).
- **`Buffer.from(*string*[,
*encoding*])`** — Creates a new Buffer with a *string*. The *encoding* parameter identifies the character encoding to be used when converting a string into bytes. The encoding can be
  `utf8`,
  `hex`,
  `base64`,
  `base64url`; by default is `utf8`.
- **`Buffer.isBuffer(*object*)`** — A boolean value, returns `true` if *object* is a Buffer.
- **`Buffer.isEncoding(*encoding*)`** — A boolean value, returns `true` if encoding is the name of a supported character encoding.
- **`buffer[*index*]`** — The index operator that can be used to get and set the octet at position `index` in `buffer`. The values refer to individual bytes, so the legal value range is between 0 and 255 (decimal).
- **`buf.buffer`** — The underlying `ArrayBuffer` object based on which this Buffer object is created.
- **`buf.byteOffset`** — An integer, specifying the `byteOffset` of the Buffers underlying `ArrayBuffer` object.
- **`buf.compare(*target*[,
*targetStart*[,
*targetEnd*[,
*sourceStart*[,
*sourceEnd*]]]])`** — Compares buffer with *target* and returns a number indicating whether buffer comes before, after, or is the same as *target* in sort order. Comparison is based on the actual sequence of bytes in each Buffer. The `targetStart` is an integer specifying the offset within *target* at which to begin comparison, by default is 0. The `targetEnd` is an integer specifying the offset within *target* at which to end comparison, by default is `target.length`. The `sourceStart` is an integer specifying the offset within buffer at which to begin comparison, by default is 0. The `sourceEnd` is an integer specifying the offset within buffer at which to end comparison (not inclusive), by default is `buf.length`.
- **`buf.copy(*target*[,
*targetStart*[,
*sourceStart*[,
*sourceEnd*]]])`** — Copies data from a region of buffer to a region in *target*, even if the target memory region overlaps with buffer. The `target` parameter is a *Buffer* or *Uint8Array* to copy into.  The `targetStart` is an integer specifying the offset within target at which to begin writing, by default is 0. The `sourceStart` is an integer specifying the offset within buffer from which to begin copying, by default is 0. The `sourceEnd` is an integer specifying the offset within buffer at which to stop copying (not inclusive) by default is *buf.length*.
- **`buf.equals(*otherBuffer*)`** — A boolean value, returns `true` if both Buffer and *otherBuffer* have exactly the same bytes.
- **`buf.fill(*value*[,
*offset*[,
*end*]][,
*encoding*])`** — Fills the Buffer with the specified *value*. If the *offset* and *end* are not specified, the entire Buffer will be filled. The *value* is coerced to *uint32* if it is not a
  `string`,
  `Buffer`, or
  `integer`. If the resulting integer is greater than 255, the Buffer will be filled with *value* and 255.
- **`buf.includes(*value*[,
*byteOffset*][,
*encoding*])`** — Equivalent to
  `buf.indexOf()`
  `!== -1`, returns `true` if the *value* was found in Buffer.
- **`buf.indexOf(*value*[,
*byteOffset*][,
*encoding*])`** — Returns an integer which is the index of the first occurrence of *value* in Buffer, or *-1* if Buffer does not contain value. The *value* can be a
  `string` with specified *encoding* (by default *utf8*),
  `Buffer`,
  `Unit8Array`, or a number between 0 and 255.
- **`buf.lastIndexOf(*value*[,
*byteOffset*][,
*encoding*])`** — The same as
  `buf.indexOf()`, except the last occurrence of the *value* is found instead of the first occurrence. The *value* can be a string, Buffer, or integer between 1 and 255. If the *value* is an empty string or empty Buffer,
  `byteOffset` will be returned.
- **`buf.length`** — Returns the number of bytes in Buffer.
- **`buf.readIntBE(*offset*,
*byteLength*)`** — Reads the *byteLength* from `buf` at the specified *offset* and interprets the result as a big-endian, two's complement signed value supporting up to 48 bits of accuracy. The *byteLength* parameter is an integer between 1 and 6 specifying the number of bytes to read. The similar methods are also supported:
  `buf.readInt8([offset])`,
  `buf.readInt16BE([offset])`,
  `buf.readInt32BE([offset])`.
- **`buf.readIntLE(*offset*,
*byteLength*)`** — Reads the *byteLength* from `buf` at the specified *offset* and interprets the result as a little-endian, two's complement signed value supporting up to 48 bits of accuracy. The *byteLength* parameter is an integer between 1 and 6 specifying the number of bytes to read. The similar methods are also supported:
  `buf.readInt8([offset])`,
  `buf.readInt16LE([offset])`,
  `buf.readInt32LE([offset])`.
- **`buf.readUIntBE(*offset*,
*byteLength*)`** — Reads the *byteLength* from `buf` at the specified *offset* and interprets the result as a big-endian integer supporting up to 48 bits of accuracy. The *byteLength* parameter is an integer between 1 and 6 specifying the number of bytes to read. The similar methods are also supported:
  `buf.readUInt8([offset])`,
  `buf.readUInt16BE([offset])`,
  `buf.readUInt32BE([offset])`.
- **`buf.readUIntLE(*offset*,
*byteLength*)`** — Reads the *byteLength* from `buf` at the specified *offset* and interprets the result as a little-endian integer supporting up to 48 bits of accuracy. The *byteLength* parameter is an integer between 1 and 6 specifying the number of bytes to read. The similar methods are also supported:
  `buf.readUInt8([offset])`,
  `buf.readUInt16LE([offset])`,
  `buf.readUInt32LE([offset])`.
- **`buf.readDoubleBE`([*offset*])** — Reads a 64-bit, big-endian double from `buf` at the specified *offset*.
- **`buf.readDoubleLE`([*offset*])** — Reads a 64-bit, little-endian double from `buf` at the specified *offset*.
- **`buf.readFloatBE`([*offset*])** — Reads a 32-bit, big-endian float from `buf` at the specified *offset*.
- **`buf.readFloatLE`([*offset*])** — Reads a 32-bit, little-endian float from `buf` at the specified *offset*.
- **`buf.subarray([*start*[,
*end*]])`** — Returns a new `buf` that references the same memory as the original, but offset and cropped by *start* and *end*. If *end* is greater than
  `buf.length`, the same result as that of end equal to
  `buf.length` is returned.
- **`buf.slice([*start*[,
*end*]])`** — Returns a new `buf` that references the same memory as the original, but offset and cropped by the *start* and *end* values. The method is not compatible with the
  `Uint8Array.prototype.slice()`, which is a superclass of Buffer. To copy the slice, use
  `Uint8Array.prototype.slice()`.
- **`buf.swap16`()** — Interprets `buf` as an array of unsigned 16-bit numbers and swaps the byte order in-place. Throws an error if
  `buf.length` is not a multiple of 2.
- **`buf.swap32`()** — Interprets `buf` as an array of unsigned 32-bit numbers and swaps the byte order in-place. Throws an error if
  `buf.length` is not a multiple of 4.
- **`buf.swap64`()** — Interprets `buf` as an array of 64-bit numbers and swaps byte order in-place. Throws an error if
  `buf.length` is not a multiple of 8.
- **`buf.toJSON`()** — Returns a JSON representation of `buf.`
  `JSON.stringify()` implicitly calls this function when stringifying a Buffer instance.
- **`buf.toString([*encoding*[,
*start*[,
*end*]]])`** — Decodes `buf` to a string according to the specified character *encoding* which can be *utf8*, *hex*, *base64*, *base64url*. The *start* and *end* parameters may be passed to decode only a subset of Buffer.
- **`buf.write(*string*[,
*offset*[,
*length*]][,
*encoding*])`** — Writes a *string* to `buf` at *offset* according to the character *encoding*. The *length* parameter is the number of bytes to write. If Buffer did not contain enough space to fit the entire string, only part of string will be written, however, partially encoded characters will not be written. The *encoding* can be *utf8*, *hex*, *base64*, *base64url*.
- **`buf.writeIntBE(*value*,
*offset*,
*byteLength*)`** — Writes *byteLength* bytes of *value* to `buf` at the specified *offset* as big-endian. Supports up to 48 bits of accuracy. The *byteLength* parameter is an integer between 1 and 6 specifying the number of bytes to read. The following similar methods are also supported:
  `buf.writeInt8`,
  `buf.writeInt16BE`,
  `buf.writeInt32BE`.
- **`buf.writeIntLE(*value*,
*offset*,
*byteLength*)`** — Writes *byteLength* bytes of *value* to `buf` at the specified *offset* as little-endian. Supports up to 48 bits of accuracy. The *byteLength* parameter is an integer between 1 and 6 specifying the number of bytes to read. The following similar methods are also supported:
  `buf.writeInt8`,
  `buf.writeInt16LE`,
  `buf.writeInt32LE`.
- **`buf.writeUIntBE(*value*,
*offset*,
*byteLength*)`** — Writes *byteLength* bytes of *value* to `buf` at the specified *offset* as big-endian. Supports up to 48 bits of accuracy. The *byteLength* parameter is an integer between 1 and 6 specifying the number of bytes to read. The following similar methods are also supported:
  `buf.writeUInt8`,
  `buf.writeUInt16BE`,
  `buf.writeUInt32BE`.
- **`buf.writeUIntLE(*value*,
*offset*,
*byteLength*)`** — Writes *byteLength* bytes of *value* to `buf` at the specified *offset* as little-endian. Supports up to 48 bits of accuracy. The *byteLength* parameter is an integer between 1 and 6 specifying the number of bytes to read. The following similar methods are also supported:
  `buf.writeUInt8`,
  `buf.writeUInt16LE`,
  `buf.writeUInt32LE`.
- **`buf.writeDoubleBE(*value*,
[*offset*])`** — Writes the *value* to `buf` at the specified *offset* as big-endian.
- **`buf.writeDoubleLE(*value*,
[*offset*])`** — Writes the *value* to `buf` at the specified *offset* as little-endian.
- **`buf.writeFloatBE(*value*,
[*offset*])`** — Writes the *value* to `buf` at the specified *offset* as big-endian.
- **`buf.writeFloatLE(*value*,
[*offset*])`** — Writes the *value* to `buf` at the specified *offset* as little-endian.

### Crypto

| `crypto.createHash()` |
|---|
| `crypto.createHmac()` |

 > **Note:** Since 0.7.0, extended crypto API is available as a global crypto object.   The Crypto module provides cryptographic functionality support. The Crypto module object is imported using `import crypto from 'crypto'`. > **Note:** Since 0.9.7, the Crypto module requires OpenSSL and uses OpenSSL EVP for hashing, making any digest algorithm supported by the linked OpenSSL library available to JavaScript code.   

- **`crypto.createHash(*algorithm*)`** — Creates and returns a Hash object that can be used to generate hash digests using the given *algorithm*. The algorithm can be
  `md5`,
  `sha1`,
  `sha256`,
  `sha384`,
  `sha512`, and any other digest supported by the linked OpenSSL library (since 0.9.7). Before version 0.9.7, only `md5`, `sha1`, and `sha256` were supported.
- **`crypto.createHmac(*algorithm*,
*secret key*)`** — Creates and returns an HMAC object that uses the given *algorithm* and *secret key*. The algorithm can be
  `md5`,
  `sha1`,
  `sha256`,
  `sha384`,
  `sha512`, and any other digest supported by the linked OpenSSL library (since 0.9.7). Before version 0.9.7, only `md5`, `sha1`, and `sha256` were supported.

#### Hash

| `hash.update()` |
|---|
| `hash.digest()` |

- **`hash.update(*data*)`** — Updates the hash content with the given *data*.
- **`hash.digest([*encoding*])`** — Calculates the digest of all of the data passed using
  `hash.update()`. The encoding can be
  `hex`,
  `base64`, and
  `base64url`. If encoding is not provided, a Buffer object (0.4.4) is returned. > **Note:** Before version (0.4.4), a byte string was returned instead of a Buffer object.
- **`hash.copy()`** — Makes a copy of the current state of the hash (since 0.7.12).

```
import crypto from 'crypto';

crypto.createHash('sha1').update('A').update('B').digest('base64url');
/* BtlFlCqiamG-GMPiK_GbvKjdK10 */
```

#### HMAC

| `hmac.update()` |
|---|
| `hmac.digest()` |

- **`hmac.update(*data*)`** — Updates the HMAC content with the given *data*.
- **`hmac.digest([*encoding*])`** — Calculates the HMAC digest of all of the data passed using
  `hmac.update()`. The encoding can be
  `hex`,
  `base64`, and
  `base64url`. If encoding is not provided, a Buffer object (0.4.4) is returned. > **Note:** Before version 0.4.4, a byte string was returned instead of a Buffer object.

```
import crypto from 'crypto';

crypto.createHmac('sha1', 'secret.key').update('AB').digest('base64url');
/* Oglm93xn23_MkiaEq_e9u8zk374 */
```

### File System

| `fs.accessSync()` |
|---|
| `fs.appendFileSync()` |
| `fs.closeSync()` |
| `fs.existsSync()` |
| `fs.fstatSync()` |
| `fs.lstatSync()` |
| `fs.mkdirSync()` |
| `fs.openSync()` |
| `fs.promises.open()` |
| `fs.readdirSync()` |
| `fs.readFileSync()` |
| `fs.readlinkSync()` |
| `fs.readSync()` |
| `fs.realpathSync()` |
| `fs.renameSync()` |
| `fs.rmdirSync()` |
| `fs.statSync()` |
| `fs.symlinkSync()` |
| `fs.unlinkSync()` |
| `fs.writeFileSync()` |
| `fs.writeSync()` |
| `fs.writeSync()` |

| `fs.Dirent` |
|---|
| `fs.FileHandle` |
| `fs.Stats` |
| `File Access Constants` |
| `File System Flags` |

 The File System module provides operations with files. 

The module object is imported using `import fs from 'fs'`.
Since 0.3.9,
promissified versions of file system methods are available through
`fs.promises` object after importing with `import fs from 'fs'`:

```
import fs from 'fs';

fs.promises.readFile("/file/path").then((data) => {
    /* <file data> */
});
```

- **`accessSync(*path*[,
*mode*])`** — Synchronously tests permissions for a file or directory
  specified in the `path`
  (0.3.9).
  If the check fails, an error will be returned,
  otherwise, the method will return undefined.
  - **`mode`** — an optional integer
    that specifies the accessibility checks to be performed,
    by default is `fs.constants.F_OK`
    
    ```
    try {
        fs.accessSync('/file/path', fs.constants.R_OK | fs.constants.W_OK);
        console.log('has access');
    } catch (e) {
        console.log('no access');)
    }
    ```
- **`appendFileSync(*filename*,
*data*[, *options*])`** — Synchronously appends specified `data`
  to a file with provided `filename`.
  The `data` is expected to be a string
  or a Buffer object (0.4.4).
  If the file does not exist, it will be created.
  The `options` parameter is expected to be
  an object with the following keys:
  - **`mode`** — mode option, by default is `0o666`
  - **`flag`** — file system flag, by default is `a`
- **`closeSync(*fd*)`** — Closes the `fd` file descriptor represented by an integer used by the method. Returns `undefined`.
- **`existsSync(*path*)`** — Boolean value, returns
  `true` if the specified *path* exists. (0.8.2)
- **`fstatSync(*fd*)`** — Retrieves the `fs.Stats` object for the file descriptor (0.7.7). The `fd` parameter is an integer representing the file descriptor used by the method.
- **`lstatSync(*path*[,
*options*])`** — Synchronously retrieves
  the `fs.Stats` object
  for the symbolic link referred to by `path`
  (0.7.1).
  The `options` parameter is expected to be
  an object with the following keys:
  - **`throwIfNoEntry`** — a boolean value which indicates whether an exception is thrown if no file system entry exists, rather than returning `undefined`, by default is `false`.
- **`mkdirSync(*path*[,
*options*])`** — Synchronously creates a directory at the specified `path`
  (0.4.2).
  The `options` parameter is expected to be an
  `integer` that specifies
  the mode,
  or an object with the following keys:
  - **`mode`** — mode option, by default is `0o777`.
- **`openSync(*path*[,
*flags*[, *mode*]])`** — Returns an integer
  representing the file descriptor for the opened file `path`
  (0.7.7).
  - **`flags`** — file system flag, by default is `r`
  - **`mode`** — mode option, by default is `0o666`
- **`promises.open(*path*[,
*flags*[, *mode*]])`** — Returns a `FileHandle` object
  representing the opened file `path`
  (0.7.7).
  - **`flags`** — file system flag, by default is `r`
  - **`mode`** — mode option, by default is `0o666`
- **`readdirSync(*path*[,
*options*])`** — Synchronously reads the contents of a directory
  at the specified `path`
  (0.4.2).
  The `options` parameter is expected to be
  a string that specifies encoding
  or an object with the following keys:
  - **`encoding`** — encoding, by default is `utf8`. The encoding can be `utf8` and `buffer` (0.4.4).
  - **`withFileTypes`** — if set to `true`, the files array will contain
    `fs.Dirent` objects, by default is `false`.
- **`readFileSync(*filename*[,
*options*])`** — Synchronously returns the contents of the file
  with provided `filename`.
  The `options` parameter holds
  `string` that specifies encoding.
  If an encoding is specified, a string is returned,
  otherwise, a Buffer object
  (0.4.4) is returned.
  > **Note:** Before version 0.4.4, a byte string was returned if encoding was not specified.
  
  
  Otherwise, `options` is expected to be
  an object with the following keys:
  - **`encoding`** — encoding, by default is not specified. The encoding can be `utf8`,
    `hex` (0.4.4),
    `base64` (0.4.4),
    `base64url` (0.4.4).
  - **`flag`** — file system flag, by default is `r`
  
  
  
  ```
  import fs from 'fs';
  
  var file = fs.readFileSync('/file/path.tar.gz');
  console.log(file.slice(0,2).toString('hex')) /* '1f8b' */
  ```
- **`readlinkSync(*path*[,
*options*])`** — Synchronously gets the contents of the symbolic link `path` using [readlink(2)](https://man7.org/linux/man-pages/man2/readlink.2.html) (0.8.7). The `options` argument can be a string specifying an encoding, or an object with `encoding` property specifying the character encoding to use. If the `encoding` is *buffer*, the result is returned as a `Buffer` object, otherwise as a string.
- **`readSync(*fd*,
*buffer*, *offset*[,
*length*[, *position*]])`** — Reads the content of a file path using file descriptor `fd`,
  returns the number of bytes read
  (0.7.7).
  
  - **`buffer`** — the `buffer` value can be a
    `Buffer`,
    `TypedArray`, or
    `DataView`
  - **`offset`** — is an `integer` representing the position in buffer to write the data to
  - **`length`** — is an `integer` representing the number of bytes to read
  - **`position`** — specifies where to begin reading from in the file, the value can be
    `integer` or
    `null`, by default is `null`. If `position` is `null`, data will be read from the current file position, and the file position will be updated. If position is an `integer`, the file position will be unchanged
- **`realpathSync(*path*[,
*options*])`** — Synchronously computes the canonical pathname by resolving
  `.`, `..` and symbolic links using [realpath(3)](http://man7.org/linux/man-pages/man3/realpath.3.html). The `options` argument can be a string specifying an encoding, or an object with an encoding property specifying the character encoding to use for the path passed to the callback (0.3.9).
- **`renameSync(*oldPath*,
*newPath*)`** — Synchronously changes the name or location of a file from
  `oldPath` to `newPath`
  (0.3.4).
  
  ```
  import fs from 'fs';
  
  fs.renameSync('hello.txt', 'HelloWorld.txt');
  ```
- **`rmdirSync(*path*)`** — Synchronously removes a directory at the specified `path` (0.4.2).
- **`statSync(*path*,[
*options*])`** — Synchronously retrieves
  the `fs.Stats` object
  for the specified `path`
  (0.7.1).
  The `path` can be a
  `string` or
  `buffer`.
  The `options` parameter is expected to be
  an object with the following keys:
  - **`throwIfNoEntry`** — a boolean value which indicates whether an exception is thrown if no file system entry exists rather than returning `undefined`, by default is `true`.
- **`symlinkSync(*target*,
*path*)`** — Synchronously creates the link called `path` pointing to `target` using [symlink(2)](http://man7.org/linux/man-pages/man2/symlink.2.html) (0.3.9). Relative targets are relative to the link’s parent directory.
- **`unlinkSync(*path*)`** — Synchronously unlinks a file by `path` (0.3.9).
- **`writeFileSync(*filename*,
*data*[,
*options*])`** — Synchronously writes `data` to a file
  with provided `filename`.
  The `data` is expected to be a string
  or a Buffer object (0.4.4).
  If the file does not exist, it will be created,
  if the file exists, it will be replaced.
  The `options` parameter is expected to be
  an object with the following keys:
  - **`mode`** — mode option, by default is `0o666`
  - **`flag`** — file system flag, by default is `w`
  
  
  
  ```
  import fs from 'fs';
  
  fs.writeFileSync('hello.txt', 'Hello world');
  ```
- **`writeSync(*fd*,
*buffer*, *offset*[,
*length*[, *position*]])`** — Writes a buffer to a file using file descriptor,
  returns the `number` of bytes written
  (0.7.7).
  
  - **`fd`** — an `integer` representing the file descriptor
  - **`buffer`** — the `buffer` value can be a
    `Buffer`,
    `TypedArray`, or
    `DataView`
  - **`offset`** — is an `integer` that determines the part of the buffer to be written, by default `0`
  - **`length`** — is an `integer` specifying the number of bytes to write, by default is an offset of Buffer.byteLength
  - **`position`** — refers to the offset from the beginning of the file where this data should be written, can be an
    `integer` or
    `null`, by default is `null`. See also [pwrite(2)](https://man7.org/linux/man-pages/man2/write.2.html).
- **`writeSync(*fd*,
*string*[,
*position*[,
*encoding*]])`** — Writes a `string` to a file
  using file descriptor `fd`,
  returns the `number` of bytes written
  (0.7.7).
  
  - **`fd`** — is an `integer` representing a file descriptor
  - **`position`** — refers to the offset from the beginning of the file where this data should be written, can be an
    `integer` or
    `null`, by default is `null`. See also [pwrite(2)](https://man7.org/linux/man-pages/man2/write.2.html)
  - **`encoding`** — is a `string`, by default is `utf8`

#### fs.Dirent

`fs.Dirent` is a representation of a directory entry — 
a file or a subdirectory.
When
`readdirSync()`
is called with the
`withFileTypes`
option,
the resulting array contains `fs.Dirent` objects.

- `dirent.isBlockDevice()` — returns
  `true` if the `fs.Dirent` object describes a block device.
- `dirent.isCharacterDevice()` — returns
  `true` if the `fs.Dirent` object describes a character device.
- `dirent.isDirectory()` — returns
  `true` if the `fs.Dirent` object describes a file system directory.
- `dirent.isFIFO()` — returns
  `true` if the `fs.Dirent` object describes a first-in-first-out (FIFO) pipe.
- `dirent.isFile()` — returns
  `true` if the `fs.Dirent` object describes a regular file.
- `dirent.isSocket()` — returns
  `true` if the `fs.Dirent` object describes a socket.
- `dirent.isSymbolicLink()` — returns
  `true` if the `fs.Dirent` object describes a symbolic link.
- `dirent.name` — the name of the file `fs.Dirent` object refers to.

#### fs.FileHandle

| `filehandle.close()` |
|---|
| `filehandle.fd` |
| `filehandle.read()` |
| `filehandle.stat()` |
| `filehandle.write(*buf*)` |
| `filehandle.write(*str*)` |

 The `FileHandle` object is an object wrapper for a numeric file descriptor (0.7.7). Instances of the `FileHandle` object are created by the
`fs.promises.open()` method. If a `FileHandle` is not closed using the
`filehandle.close()` method, it will try to automatically close the file descriptor, helping to prevent memory leaks. Please do not rely on this behavior because it can be unreliable. Instead, always explicitly close a `FileHandle`. 

- **`filehandle.close()`** — Closes the file handle after waiting for any pending operation on the handle to complete. Returns a `promise`, fulfills with undefined upon success.
- **`filehandle.fd`** — The numeric file descriptor managed by the `FileHandle` object.
- **`filehandle.read(*buffer*,
*offset*[,
*length*[,
*position*]])`** — Reads data from the file and stores that in the given buffer.
  
  - **`buffer`** — a buffer that will be filled with the file data read, the value can be a
    `Buffer`,
    `TypedArray`, or
    `DataView`
  - **`offset`** — is an `integer` representing the location in the buffer at which to start filling
  - **`length`** — is an `integer` representing the number of bytes to read
  - **`position`** — the location where to begin reading data from the file, the value can be
    `integer`,
    `null`. If `null`, data will be read from the current file position and the position will be updated. If position is an `integer`, the current file position will remain unchanged.
  
  
  
  Returns a `Promise` which fulfills upon success
  with an object with two properties:
  - **`bytesRead`** — is an `integer` representing the number of bytes read
  - **`buffer`** — is a reference to the passed argument in buffer, can be
    `Buffer`,
    `TypedArray`, or
    `DataView`
- **`filehandle.stat()`** — Fulfills with an fs.Stats for the file, returns a `promise`.
- **`filehandle.write(*buffer*,
*offset*[,
*length*[,
*position*]])`** — Writes a buffer to the file.
  
  - **`buffer`** — the `buffer` value can be a
    `Buffer`,
    `TypedArray`, or
    `DataView`
  - **`offset`** — is an `integer` representing the start position from within buffer where the data to write begins
  - **`length`** — is an `integer` representing the number of bytes from buffer to write, by default is an offset of Buffer.byteLength
  - **`position`** — the offset from the beginning of the file where the data from buffer should be written, can be an
    `integer` or
    `null`, by default is `null`. If `position` is not a `number`, the data will be written at the current position. See the POSIX [pwrite(2)](https://man7.org/linux/man-pages/man2/write.2.html) documentation for details.
  
  
  Returns a `Promise` which is resolved with an object
  containing two properties:
  - **`bytesWritten`** — is an `integer` representing the number of bytes written
  - **`buffer`** — a reference to the buffer written, can be a
    `Buffer`,
    `TypedArray`, or
    `DataView`
  
  
   > **Note:** It is unsafe to use `filehandle.write()` multiple times on the same file without waiting for the promise to be resolved or rejected.
- **`filehandle.write(*string*[,
*position*[,
*encoding*]])`** — Writes a `string` to the file.
  
  - **`position`** — the offset from the beginning of the file where the data from buffer should be written, can be an
    `integer` or
    `null`, by default is `null`. If `position` is not a `number`, the data will be written at the current position. See the POSIX [pwrite(2)](https://man7.org/linux/man-pages/man2/write.2.html) documentation for details.
  - **`encoding`** — the expected encoding of the string, by default `utf8`
  
  
  Returns a `Promise` which is resolved with an object
  containing two properties:
  - **`bytesWritten`** — is an `integer` representing the number of bytes written
  - **`buffer`** — a reference to the buffer written, can be a
    `Buffer`,
    `TypedArray`, or
    `DataView`
  
  
   > **Note:** It is unsafe to use `filehandle.write()` multiple times on the same file without waiting for the promise to be resolved or rejected.

#### fs.Stats

The `fs.Stats` object provides information about a file.
The object is returned from
fs.statSync() and
fs.lstatSync().

- `stats.isBlockDevice()` — returns
  `true` if the `fs.Stats` object describes a block device.
- `stats.isDirectory()` — returns
  `true` if the `fs.Stats` object describes a file system directory.
- `stats.isFIFO()` — returns
  `true` if the `fs.Stats` object describes a first-in-first-out (FIFO) pipe.
- `stats.isFile()` — returns
  `true` if the `fs.Stats` object describes a regular file.
- `stats.isSocket()` — returns
  `true` if the `fs.Stats` object describes a socket.
- `stats.isSymbolicLink()` — returns
  `true` if the `fs.Stats` object describes a symbolic link.
- `stats.dev` — the numeric identifier of the device containing the file.
- `stats.ino` — the file system specific `Inode` number for the file.
- `stats.mode` — a bit-field describing the file type and mode.
- `stats.nlink` — the number of hard-links that exist for the file.
- `stats.uid` — the numeric user identifier of the user that owns the file (POSIX).
- `stats.gid` — the numeric group identifier of the group that owns the file (POSIX).
- `stats.rdev` — the numeric device identifier if the file represents a device.
- `stats.size` — the size of the file in bytes.
- `stats.blksize` — the file system block size for i/o operations.
- `stats.blocks` — the number of blocks allocated for this file.
- `stats.atimeMs` — the timestamp indicating the last time this file was accessed expressed in milliseconds since the POSIX Epoch.
- `stats.mtimeMs` — the timestamp indicating the last time this file was modified expressed in milliseconds since the POSIX Epoch.
- `stats.ctimeMs` — the timestamp indicating the last time this file was changed expressed in milliseconds since the POSIX Epoch.
- `stats.birthtimeMs` — the timestamp indicating the creation time of this file expressed in milliseconds since the POSIX Epoch.
- `stats.atime` — the timestamp indicating the last time this file was accessed.
- `stats.mtime` — the timestamp indicating the last time this file was modified.
- `stats.ctime` — the timestamp indicating the last time this file was changed.
- `stats.birthtime` — the timestamp indicating the creation time of this file.

#### File Access Constants

The `access()` method
can accept the following flags.
These flags are exported by `fs.constants`:

- `F_OK` — indicates that the file is visible to the calling process, used by default if no mode is specified
- `R_OK` — indicates that the file can be read by the calling process
- `W_OK` — indicates that the file can be written by the calling process
- `X_OK` — indicates that the file can be executed by the calling process

#### File System Flags

The `flag` option can accept the following values:

- `a` — open a file for appending. The file is created if it does not exist
- `ax` — the same as `a` but fails if the file already exists
- `a+` — open a file for reading and appending. If the file does not exist, it will be created
- `ax+` — the same as `a+` but fails if the file already exists
- `as` — open a file for appending in synchronous mode. If the file does not exist, it will be created
- `as+` — open a file for reading and appending in synchronous mode. If the file does not exist, it will be created
- `r` — open a file for reading. An exception occurs if the file does not exist
- `r+` — open a file for reading and writing. An exception occurs if the file does not exist
- `rs+` — open a file for reading and writing in synchronous mode. Instructs the operating system to bypass the local file system cache
- `w` — open a file for writing. If the file does not exist, it will be created. If the file exists, it will be replaced
- `wx` — the same as `w` but fails if the file already exists
- `w+` — open a file for reading and writing. If the file does not exist, it will be created. If the file exists, it will be replaced
- `wx+` — the same as `w+` but fails if the file already exists

### Query String

| `querystring.decode()` |
|---|
| `querystring.encode()` |
| `querystring.escape()` |
| `querystring.parse()` |
| `querystring.stringify()` |
| `querystring.unescape()` |

 The Query String module provides support for parsing and formatting URL query strings (0.4.3). The Query String module object is imported using
`import qs from 'querystring'`. 

- **`querystring.decode()`** — is an alias for
  `querystring.parse()`.
- **`querystring.encode()`** — is an alias for
  `querystring.stringify()`.
- **`querystring.escape(*string*)`** — Performs URL encoding of the given `string`, returns an escaped query string. The method is used by
  `querystring.stringify()` and should not be used directly.
- **`querystring.parse(*string*[,
*separator*[,
*equal*[,
*options*]]])`** — Parses the query string URL and returns an object. 
  
  
  
   The `separator` parameter is a substring for delimiting key and value pairs in the query string, by default is “`&`”. 
  
  
  
   The `equal` parameter is a substring for delimiting keys and values in the query string, by default is “`=`”. 
  
  
  
  
  The `options` parameter is expected to be
  an object with the following keys:
  - **`decodeURIComponent`
  *function*** — Function used to decode percent-encoded characters in the query string, by default is
    `querystring.unescape()`
  - **`maxKeys`
  *number*** — the maximum number of keys to parse, by default is `1000`. The `0` value removes limitations for counting keys.
  
  
  By default, percent-encoded characters within the query string are assumed
  to use the UTF-8 encoding,
  invalid UTF-8 sequences will be replaced with
  the `U+FFFD` replacement character.
  
  
  
  
  
  For example, for the following query string
  
  ```
  'foo=bar&abc=xyz&abc=123'
  ```
  
  the output will be:
  
  ```
  {
    foo: 'bar',
    abc: ['xyz', '123']
  }
  ```
- **`querystring.stringify(*object*[,
*separator*[,
*equal*[,
*options*]]])`** — Serializes an object and returns a URL query string. 
  
  
  
   The `separator` parameter is a substring for delimiting key and value pairs in the query string, by default is “`&`”. 
  
  
  
   The `equal` parameter is a substring for delimiting keys and values in the query string, by default is “`=`”. 
  
  
  
  
  The `options` parameter is expected to be
  an object with the following keys:
  - **`encodeURIComponent`
  *function*** — The function to use when converting URL-unsafe characters to percent-encoding in the query string, by default is
    `querystring.escape()`.
  
  
  
  
  
  
   By default, characters that require percent-encoding within the query string are encoded as UTF-8. If other encoding is required, then
  `encodeURIComponent` option should be specified. 
  
  
  
  
  For example, for the following command
  
  ```
  querystring.stringify({ foo: 'bar', baz: ['qux', 'quux'], 123: '' });
  ```
  
  the query string will be:
  
  ```
  'foo=bar&baz=qux&baz=quux&123='
  ```
- **`querystring.unescape(*string*)`** — Performs decoding of URL percent-encoded characters of the `string`, returns an unescaped query string. The method is used by
  `querystring.parse()` and should not be used directly.

### XML

| `xml.parse()` |
|---|
| `xml.c14n()` |
| `xml.exclusiveC14n()` |
| `xml.serialize()` |
| `xml.serializeToString()` |
| `XMLDoc` |
| `XMLNode` |
| `XMLAttr` |

 The XML module allows working with XML documents (since 0.7.10). The XML module object is imported using
`import xml from 'xml'`. 

Example:

```
import xml from 'xml';

let data = `<note><to b="bar" a= "foo" >Tove</to><from>Jani</from></note>`;
let doc = xml.parse(data);

console.log(doc.note.to.$text) /* 'Tove' */
console.log(doc.note.to.$attr$b) /* 'bar' */
console.log(doc.note.$tags[1].$text) /* 'Jani' */

let dec = new TextDecoder();
let c14n = dec.decode(xml.exclusiveC14n(doc.note));
console.log(c14n) /* '<note><to a="foo" b="bar">Tove</to><from>Jani</from></note>' */

c14n = dec.decode(xml.exclusiveC14n(doc.note.to));
console.log(c14n) /* '<to a="foo" b="bar">Tove</to>' */

c14n = dec.decode(xml.exclusiveC14n(doc.note, doc.note.to /* excluding 'to' */));
console.log(c14n) /* '<note><from>Jani</from></note>' */
```

- **`parse(*string* |
*Buffer*)`** — Parses a string or Buffer for an XML document, returns an
  `XMLDoc` wrapper object representing the parsed XML document.
- **`c14n(*root_node*[,
*excluding_node*])`** — Canonicalizes `root_node` and its children according to
  [Canonical XML Version 1.1](https://www.w3.org/TR/xml-c14n).
  The `root_node` can be
  `XMLNode` or
  `XMLDoc` wrapper object
  around XML structure.
  Returns Buffer object that contains canonicalized output.
  
  
  - **`excluding_node`** — allows omitting from the output a part of the document
- **`exclusiveC14n(*root_node*[,
*excluding_node*[,
*withComments*
[,*prefix_list*]]])`** — Canonicalizes `root_node` and its children according to
  [Exclusive XML
  Canonicalization Version 1.0](https://www.w3.org/TR/xml-exc-c14n/).
  
  
  - **`root_node`** — is
    `XMLNode` or
    `XMLDoc` wrapper object around XML structure
  - **`excluding_node`** — allows omitting from the output a part of the document corresponding to the node and its children
  - **`withComments`** — a boolean value, `false` by default. If `true`, canonicalization corresponds to [Exclusive XML Canonicalization Version 1.0](http://www.w3.org/2001/10/xml-exc-c14n#WithComments). Returns Buffer object that contains canonicalized output.
  - **`prefix_list`** — an optional string with a space separated namespace prefixes for namespaces that should also be included into the output
- **`serialize()`** — The same as
  `xml.c14n()` (since 0.7.11).
- **`serializeToString()`** — The same as
  `xml.c14n()` except it returns the result as a `string` (since 0.7.11).
- **`XMLDoc`** — An XMLDoc wrapper object around XML structure,
  the root node of the document.
  
  
  - **`doc.$root`** — the document's root by its name or undefined
  - **`doc.*abc*`** — the first root tag named *abc* as
    `XMLNode` wrapper object
- **`XMLNode`** — An XMLNode wrapper object around XML tag node.
  Since 1.0.2, existing wrappers
  for a node continue to refer to it after mutation. Removed nodes remain
  readable, but cannot be mutated.
  
  - **`node.*abc*`** — the same as
    `node.$tag$*abc*`, unless *abc* is the name of an XMLNode method
  - **`node.$attr$*abc*`** — the node's attribute value of *abc*, writable since 0.7.11
  - **`node.$attr$*abc*`=*xyz*** — the same as
    `node.setAttribute('*abc*', *xyz*)` (since 0.7.11)
  - **`node.$attrs`** — an `XMLAttr` wrapper object for all attributes of the node
  - **`node.$name`** — the name of the node
  - **`node.$ns`** — the namespace of the node
  - **`node.$parent`** — the parent node of the current node, or `undefined` for a document root. Since 1.0.2, the value is also
    `undefined` for a removed node
  - **`node.$tag$*abc*`** — the first child tag of the node named *abc*. This form is required if *abc* is also the name of an XMLNode method. Assignment is not supported. Deleting the property removes matching child tags
  - **`node.$tags`** — an array of all children tags
  - **`node.$tags = [node1, node2, ...]`** — the same as
    `node.removeChildren`();
    `node.addChild(*node1*)`;
    `node.addChild(*node2*)` (since 0.7.11). Since 1.0.2, XMLDoc sources are supported and source nodes must not have namespaces
  - **`node.$tags$*abc*`** — all children tags named *abc* of the node. Assignment and deletion are not supported
  - **`node.$text`** — the content of the node, writable since 0.7.11 Since 1.0.2, assigning a string replaces all child nodes, while assigning `null` or
    `undefined` removes them
  - **`node.$text = 'abc'`** — the same as
    `node.setText('abc')` (since 0.7.11)
  - **`node.addChild(*nd*)`** — adds XMLNode as a child to node (since 0.7.11).
    `nd` is recursively copied before adding to the node. Since 1.0.2, XMLDoc sources are supported and source nodes must not have namespaces
  - **`node.getAttributeNS(*namespaceURI*,
  *localName*)`** — returns the value of the first attribute matching `namespaceURI` and `localName`, or `undefined` if there is no matching attribute. The `namespaceURI` is a string or `null`; an empty string and `null` match attributes without a namespace. An unprefixed attribute has no namespace, even if a default namespace is declared. Since 1.0.2
  - **`node.getChildNS(*namespaceURI*,
  *localName*)`** — returns the first child tag matching `namespaceURI` and
    `localName`, or `undefined` if there is no matching child tag. The `namespaceURI` is a string or `null`; an empty string and `null` match tags without a namespace. Since 1.0.2
  - **`node.removeAllAttributes()`** — removes all attributes of the node (since 0.7.11)
  - **`node.removeAttribute(*attr_name*)`** — removes the attribute named `attr_name` (since 0.7.11)
  - **`node.removeChildren(*tag_name*)`** — removes all the children tags named `tag_name` (since 0.7.11). If `tag_name` is absent, all child nodes are removed
  - **`node.removeText()`** — removes all child nodes (0.7.11)
  - **`node.setAttribute(*attr_name*,
  *value*)`** — sets a value for an `attr_name` (since 0.7.11). Since 1.0.2, a string value is assigned to the attribute, while `null` or
    `undefined` deletes it
  - **`node.setText(*value*)`** — sets a text value for the node (since 0.7.11). Since 1.0.2, a string value replaces all child nodes, while `null` or
    `undefined` deletes all child nodes
- **`XMLAttr`** — An XMLAttrs wrapper object around XML node attributes.
  
  
  - **`attr.*abc*`** — the attribute value of *abc*

### zlib

| `zlib.deflateRawSync()` |
|---|
| `zlib.deflateSync()` |
| `zlib.inflateRawSync()` |
| `zlib.inflateSync()` |

 The zlib module provides compression functionality using the “deflate” and “inflate” algorithms (since 0.7.12). The zlib module object is imported using
`import zlib from 'zlib'`. 

- **`deflateRawSync(*string* |
*Buffer*[,
*options*])`** — Compresses data using the “deflate” algorithm provided as a string or Buffer and does not append a zlib header. The buffer value can be a
  `Buffer`,
  `TypedArray`, or
  `DataView`.
  `Options` is an optional object that contains zlib_options. Returns Buffer instance that contains the compressed data.
- **`deflateSync(*string* |
*Buffer*[,
*options*])`** — Compresses data using the “deflate” algorithm provided as a string or Buffer. The Buffer value can be a
  `Buffer`,
  `TypedArray`, or
  `DataView`.
  `Options` is an optional object that contains zlib_options. Returns Buffer instance that contains the compressed data.
- **`inflateRawSync(*string* |
*Buffer*)`** — Decompresses a raw stream by using the “deflate” algorithm. Returns Buffer instance that contains the decompressed data.
- **`inflateSync(*string* |
*Buffer*)`** — Decompresses a stream by using the “deflate” algorithm. Returns Buffer instance that contains the decompressed data.

#### zlib options

- `chunkSize` — is an integer, by default is `1024`
- `dictionary` — is a
  `Buffer`,
  `TypedArray`, or
  `DataView`. by default is empty
- `level` — is an integer, compression only, see zlib_compression_levels
- `memLevel` — is an integer from `1` to `9`, compression only
- `strategy` — is an integer, compression only, see zlib_compression_strategy
- `windowBits` — is an integer from `-15` to `-9` for raw data, from `9` to `15` for an ordinary stream

#### zlib compression levels

| Name | Description |
|---|---|
| `zlib.constants.Z_NO_COMPRESSION` | no compression |
| `zlib.constants.Z_BEST_SPEED` | fastest, produces the least compression |
| `zlib.constants.Z_DEFAULT_COMPRESSION` | trade-off between speed and compression |
| `zlib.constants.Z_BEST_COMPRESSION` | slowest, produces the most compression |

#### zlib compression strategy

| Name | Description |
|---|---|
| `zlib.constants.Z_FILTERED` | Filtered strategy: for the data produced by a filter or predictor |
| `zlib.constants.Z_HUFFMAN_ONLY` | Huffman-only strategy: only Huffman encoding, no string matching |
| `zlib.constants.Z_RLE` | Run Length Encoding strategy: limit match distances to one, better compression of PNG image data |
| `zlib.constants.Z_FIXED` | Fixed table strategy: prevents the use of dynamic Huffman codes, a simpler decoder for special applications |
| `zlib.constants.Z_DEFAULT_STRATEGY` | Default strategy, suitable for general purpose compression |
