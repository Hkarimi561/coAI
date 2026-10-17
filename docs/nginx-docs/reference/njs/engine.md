# JavaScript Engine

 Starting from version 0.8.6, multiple JavaScript engines are supported. To specify a particular engine, use the `js_engine` directive available for both the http and stream. By default, the njs engine is used. 

## njs engine

 > **Note:** The njs engine is deprecated since 1.0.0; new code should use the QuickJS engine instead.   

 njs is an embeddable JavaScript engine developed as a part of the njs module. See the Compatibility section for details. 

## QuickJS engine

 [QuickJS](https://bellard.org/quickjs/) is a lightweight, embeddable JavaScript engine that supports the [ES2023](https://tc39.es/ecma262/2023/) specification, including features as modules, asynchronous generators, proxies and BigInt. 

Since version 0.8.6,
a drop-in replacement for
njs/nginx objects
has been introduced
to ensure compatibility with the njs engine, with the following exceptions:

- njs-specific API:
  `njs.dump()`,
  `console.dump()`.
- deprecated API:
  `require()`, use the `import` statement instead.
- `js_preload_object` directive for http and stream.

njs built-in modules status:

- `buffer`: since 0.8.6.
- `crypto`: since 0.8.10.
- `fs`: since 0.8.9.
- `querystring`: since 0.8.10.
- `WebCrypto`: since 0.8.10.
- `xml`: since 0.8.10.
- `zlib`: since 0.8.5.

njs built-in objects status:

- `process`: since 0.8.8.
- `TextDecoder`: since 0.8.10.
- `TextEncoder`: since 0.8.10.

nginx built-in objects status:

- `ngx.fetch`: since 0.9.1.
- `shared dictionary`: since 0.8.8.
