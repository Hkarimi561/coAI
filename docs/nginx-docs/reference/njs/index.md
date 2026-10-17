# nginx JavaScript module

 njs is an nginx module that extends the server's functionality through JavaScript scripting, enabling the creation of custom server-side logic and more. 

 nginx calls JavaScript handlers at a fixed set of integration points: HTTP request and response processing phases, stream session phases, variable evaluation, and periodic timers. njs is not a standalone application runtime: it has no start-up script and no event loop of its own, JavaScript code runs only when nginx invokes a configured handler, and control returns to nginx once the handler completes. 

 > **Note:** The built-in njs JavaScript engine is deprecated since 1.0.0; new configurations should use the QuickJS engine.   

## Getting started

- install.xml
- integration.xml
- [Examples](https://github.com/nginx/njs-examples/)
- cli.xml

## Reference

- reference.xml
- ngx_http_js_module
- ngx_stream_js_module
- engine.xml
- compatibility.xml
- native_modules.xml
- node_modules.xml
- typescript.xml
- preload_objects.xml

## Project

- changes.xml
- security.xml
- Tested OS and platforms

## Use cases

- Complex access control and security checks in njs before a request reaches an upstream server
- Manipulating response headers
- Writing flexible asynchronous content handlers and filters

See [examples](https://github.com/nginx/njs-examples/)
for more njs use cases.

## Basic HTTP Example

To use njs in nginx:
- install njs
- create an njs script file, for example, `http.js`.
  See Reference
  for the list of njs properties and methods.
  
  ```
  function hello(r) {
      r.return(200, "Hello world!");
  }
  
  export default {hello};
  ```
- in the `nginx.conf` file, enable
  ngx_http_js_module module
  and specify the
  js_import
  directive
  with the `http.js` script file:
  
  ```
  load_module modules/ngx_http_js_module.so;
  
  events {}
  
  http {
      # since 0.9.1
      js_engine qjs;
  
      js_import http.js;
  
      server {
          listen 8000;
  
          location / {
              js_content http.hello;
          }
      }
  }
  ```

There is also a standalone command line utility
that can be used independently of nginx for njs development and debugging.

## Tested OS and platforms

- FreeBSD / amd64;
- Linux / x86, amd64, arm64, ppc64el;
- Solaris 11 / amd64;
- macOS / x86_64;

## Presentation at nginx.conf 2018
