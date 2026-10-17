# Compatibility

This page describes the JavaScript surface provided by njs:
- the njs and nginx objects, built-in modules, and the
  `Buffer` object, available with both the QuickJS and njs engines;
- the ECMAScript language features implemented by the njs engine.

 Definitions of njs specific properties and methods not compliant with ECMAScript can be found in Reference. Definitions of standard ECMAScript objects and methods can be found in the [ECMAScript specification](http://www.ecma-international.org/ecma-262/). 

## njs and nginx objects, modules, and Buffer

 The objects, modules, and methods listed below are available with both the QuickJS and njs engines, unless noted otherwise. 

- `Buffer` methods
  (0.4.4):
  - `alloc`,
    `allocUnsafe`,
    `byteLength`,
    `compare`,
    `concat`,
    `from`,
    `isBuffer`,
    `isEncoding`
- `Buffer` prototype methods
  (0.4.4):
  - `compare`,
    `copy`,
    `equals`,
    `fill`,
    `includes`,
    `indexOf`,
    `lastIndexOf`,
    `readIntBE`,
    `readInt8`,
    `readInt16BE`,
    `readInt32BE`,
    `readIntLE`,
    `readInt16LE`,
    `readInt32LE`,
    `readUIntBE`,
    `readUInt8`,
    `readUInt16BE`,
    `readUInt32BE`,
    `readUIntLE`,
    `readUInt16LE`,
    `readUInt32LE`,
    `readDoubleBE`,
    `readDoubleLE`,
    `readFloatBE`,
    `readFloatLE`,
    `subarray`,
    `slice`,
    `swap16`,
    `swap32`,
    `swap64`,
    `toJSON`,
    `toString`,
    `write`,
    `writeIntBE`,
    `writeInt8`,
    `writeInt16BE`,
    `writeInt32BE`,
    `writeIntLE`,
    `writeInt16LE`,
    `writeInt32LE`,
    `writeUIntBE`,
    `writeUInt8`,
    `writeUInt16BE`,
    `writeUInt32BE`,
    `writeUIntLE`,
    `writeUInt16LE`,
    `writeUInt32LE`,
    `writeDoubleBE`,
    `writeDoubleLE`,
    `writeFloatBE`,
    `writeFloatLE`
- `Crypto` methods (0.2.0):
  `crypto.createHash`,
  `crypto.createHmac`
- `Query String` methods (0.4.3):
  `querystring.decode`,
  `querystring.encode`,
  `querystring.escape`,
  `querystring.parse`,
  `querystring.stringify`,
  `querystring.unescape`
- `TextDecoder` methods (0.4.3):
  `encoding`,
  `fatal`,
  `ignoreBOM`,
  `decode`
- `TextEncoder` methods (0.4.3):
  `encode`,
  `encodeInto`
- `XML` methods (0.7.10):
  `parse`,
  `xml.c14n`,
  `xml.exclusiveC14n`
- `zlib` methods (0.7.12):
  `deflateRawSync`,
  `deflateSync`,
  `inflateRawSync`,
  `inflateSync`
- `File system` methods:
  `fs.accessSync` (0.3.9),
  `fs.appendFileSync`,
  `fs.closeSync`,
  `fs.existsSync` (0.8.2),
  `fs.FileHandle` (0.7.7),
  `fs.fstatSync` (0.7.7),
  `fs.lstatSync` (0.7.1),
  `fs.mkdirSync` (0.4.2),
  `fs.openSync` (0.7.7),
  `fs.promises.open` (0.7.7),
  `fs.readdirSync` (0.4.2),
  `fs.readFileSync`,
  `fs.readSync` (0.7.7),
  `fs.realpathSync` (0.3.9),
  `fs.renameSync` (0.3.4),
  `fs.rmdirSync` (0.4.2),
  `fs.symlinkSync` (0.3.9),
  `fs.unlinkSync` (0.3.9),
  `fs.writeFileSync`,
  `fs.writeSync` (0.7.7)
- `fs.promises` API (0.3.9), asynchronous version of file system methods.
- Global functions:
  `atob`,
  `btoa` (available with the njs engine since 0.7.6 and with the QuickJS engine since 1.0.1)
- `clearTimeout` and
  `setTimeout` functions (0.2.0)
- Global objects
  (0.3.3):
  - `console` (0.8.2):
    `error`,
    `info`,
    `log`,
    `time`,
    `timeEnd`,
    `warn`
  - `crypto` (0.7.0):
    `getRandomValues`,
    `randomUUID` (0.9.7),
    `subtle.encrypt`,
    `subtle.decrypt`,
    `subtle.deriveBits`,
    `subtle.deriveKey`,
    `subtle.digest`,
    `subtle.exportKey` (0.7.10),
    `subtle.generateKey` (0.7.10),
    `subtle.importKey`,
    `subtle.sign`,
    `subtle.verify`,
    `subtle.wrapKey` (0.9.7),
    `subtle.unwrapKey` (0.9.7)
  - `globalThis` alias (0.3.8)
  - `njs`:
    `version`,
    `version_number` (0.7.4),
    `dump` (njs engine only),
    `memoryStats` (0.7.8, njs engine only),
    `on` (0.5.2)
  - `process`:
    `argv`,
    `env`,
    `pid`,
    `ppid`
- nginx object methods:
  - `HTTP Request`:
    `r.done` (0.5.2),
    `r.error`,
    `r.finish`,
    `r.internalRedirect`,
    `r.log`,
    `r.return` (0.5.0),
    `r.send` (0.5.0),
    `r.sendBuffer` (0.5.2),
    `r.sendHeader`,
    `r.setReturnValue` (0.7.0),
    `r.subrequest`,
    `r.warn`
  - `Stream Session`:
    `s.allow` (0.2.4),
    `s.decline` (0.2.4),
    `s.deny` (0.2.4),
    `s.done` (0.2.4),
    `s.error`,
    `s.log`,
    `s.off` (0.2.4),
    `s.on` (0.2.4),
    `s.send` (0.2.4),
    `s.sendDownstream` (0.7.8),
    `s.sendUpstream` (0.7.8),
    `s.setReturnValue` (0.7.0),
    `s.warn`
  - `Headers` (0.5.1):
    `append`,
    `delete`,
    `get`,
    `getAll`,
    `forEach`,
    `has`,
    `set`
  - `Request` (0.7.10):
    `arrayBuffer`,
    `headers`,
    `json`,
    `text`
  - `Response` (0.5.1):
    `arrayBuffer`,
    `headers`,
    `json`,
    `text`
  - `ngx` (0.5.0):
    `fetch` (0.5.1),
    `log`
  - `ngx.shared` (0.8.0):
    `add`,
    `clear`,
    `delete`,
    `freeSpace`,
    `get`,
    `has`,
    `incr`,
    `items`,
    `keys`,
    `pop`,
    `replace`,
    `set`,
    `size`,
    `ttl` (0.9.7)
- nginx object properties:
  - `HTTP Request`:
    `r.args`,
    `r.headersIn`,
    `r.headersOut`,
    `r.httpVersion`,
    `r.internal`,
    `r.jsVarNames` (0.9.9),
    `r.method`,
    `r.parent`,
    `r.readRequestArrayBuffer` (0.9.9),
    `r.readRequestForm` (0.9.9),
    `r.readRequestJSON` (0.9.9),
    `r.readRequestText` (0.9.9),
    `r.rawHeadersIn` (0.4.1),
    `r.rawHeadersOut` (0.4.1),
    `r.rawVariables` (0.5.0),
    `r.remoteAddress`,
    `r.requestBuffer` (0.5.0),
    `r.requestText`,
    `r.responseBuffer` (0.5.0),
    `r.responseText` (0.5.0),
    `r.status`,
    `r.uri`,
    `r.variables` (0.2.8)
  - `Stream Session`:
    `s.jsVarNames` (0.9.9),
    `s.remoteAddress`,
    `s.rawVariables` (0.5.0),
    `s.status` (0.5.2),
    `s.variables` (0.2.8)
  - `Periodic Session` (0.8.1):
    `PeriodicSession.rawVariables`,
    `PeriodicSession.variables`
  - `Request` (0.7.10):
    `bodyUsed`,
    `cache`,
    `credentials`,
    `method`,
    `mode`,
    `url`
  - `Response` (0.5.1):
    `bodyUsed`,
    `ok`,
    `redirected`,
    `status`,
    `statusText`,
    `type`,
    `url`
  - `ngx` (0.5.0):
    `build` (0.8.0),
    `conf_file_path` (0.8.0),
    `conf_prefix` (0.7.8),
    `error_log_path` (0.8.0),
    `prefix` (0.8.0),
    `version` (0.8.0),
    `version_number` (0.8.0),
    `worker_id` (0.8.0)
  - `ngx.shared` (0.8.0):
    `capacity`,
    `name`,
    `type`

## ECMAScript compliance (njs engine)

 > **Note:** The ECMAScript language features listed below describe the njs engine, which is deprecated since 1.0.0. The QuickJS engine supports ES2023; new code should use the QuickJS engine instead.   

 The njs engine is implemented in compliance with [ECMAScript 5.1](http://www.ecma-international.org/ecma-262/5.1/) (strict mode) with some [ECMAScript 6](http://www.ecma-international.org/ecma-262/6.0/) and later extensions. The compliance is still evolving. 

- Boolean values, numbers, strings, objects, arrays, functions, function constructors (0.3.6), and regular expressions
- ES5.1 operators, ES7 exponentiation operators, ES2020 optional chaining (0.9.6), ES2021 logical assignment operators
  `||=`, `&&=`,
  `??=` (0.9.6)
- ES5.1 statements:
  `break`,
  `catch`,
  `continue`,
  `do while`,
  `else`,
  `finally`,
  `for`,
  `for in`,
  `if`,
  `return`,
  `switch`,
  `throw`,
  `try`,
  `var`,
  `while`, labeled statements (0.2.8)
- ES6 statements:
  `let` (0.6.0),
  `const` (0.6.0),
  `async` (0.7.0),
  `await` (0.7.0)
- `Math` properties:
  - ES6:
    `E`,
    `LN10`,
    `LN2`,
    `LOG10E`,
    `LOG2E`,
    `PI`,
    `SQRT1_2`,
    `SQRT2`
- `Math` methods:
  - ES6:
    `abs`,
    `acos`,
    `acosh`,
    `asin`,
    `asinh`,
    `atan`,
    `atan2`,
    `atanh`,
    `cbrt`,
    `ceil`,
    `clz32`,
    `cos`,
    `cosh`,
    `exp`,
    `expm1`,
    `floor`,
    `fround`,
    `hypot`,
    `imul`,
    `log`,
    `log10`,
    `log1p`,
    `log2`,
    `max`,
    `min`,
    `pow`,
    `random`,
    `round`,
    `sign`,
    `sin`,
    `sinh`,
    `sqrt`,
    `tan`,
    `tanh`,
    `trunc`
- `Number` properties:
  - ES6:
    `EPSILON`,
    `MAX_SAFE_INTEGER`,
    `MAX_VALUE`,
    `MIN_SAFE_INTEGER`,
    `MIN_VALUE`,
    `NEGATIVE_INFINITY`,
    `NaN`,
    `POSITIVE_INFINITY`
- `Number` methods:
  - ES6:
    `isFinite`,
    `isInteger`,
    `isNaN`,
    `isSafeInteger`,
    `parseFloat`,
    `parseInt`
- `Number` prototype methods:
  - ES6:
    `toExponential` (0.3.6),
    `toFixed` (0.3.6),
    `toPrecision` (0.3.6)
- `String` methods:
  - ES5.1:
    `fromCharCode`
  - ES6:
    `fromCodePoint`
- `String` prototype methods:
  - ES5.1:
    `charAt`,
    `concat`,
    `indexOf`,
    `lastIndexOf`,
    `match`,
    `replace`,
    `search`,
    `slice`,
    `split`,
    `substr`,
    `substring`,
    `toLowerCase`,
    `trim`,
    `toUpperCase`
  - ES6:
    `codePointAt`,
    `endsWith`,
    `includes`,
    `repeat`,
    `startsWith`
  - ES8:
    `padEnd`,
    `padStart`
  - ES9:
    `trimEnd` (0.3.4),
    `trimStart` (0.3.4)
  - ES12:
    `replaceAll` (0.7.10)
- `Object` methods:
  - ES5.1:
    `create` (support without properties list),
    `defineProperties` (accessor descriptors support since 0.3.3),
    `defineProperty` (accessor descriptors support since 0.3.3),
    `freeze`,
    `getOwnPropertyDescriptor`,
    `getOwnPropertyDescriptors` (0.3.1),
    `getOwnPropertyNames` (0.3.1),
    `getPrototypeOf`,
    `isExtensible`,
    `isFrozen`,
    `isSealed`,
    `keys`,
    `preventExtensions`,
    `seal`
  - ES6:
    `assign` (0.3.7),
    `is` (0.3.8),
    `setPrototypeOf` (0.3.8)
  - ES8:
    `entries` (0.2.7),
    `values` (0.2.7)
- `Object` prototype methods:
  - ES5.1:
    `hasOwnProperty`,
    `isPrototypeOf` (0.3.0),
    `propertyIsEnumerable`,
    `toString`,
    `valueOf`
- `Array` methods:
  - ES5.1:
    `isArray`
  - ES6:
    `of`,
    `from` (0.8.0)
- `Array` prototype methods:
  - ES5.1:
    `concat`,
    `every`,
    `filter`,
    `forEach`,
    `indexOf`,
    `join`,
    `lastIndexOf`,
    `map`,
    `pop`,
    `push`,
    `reduce`,
    `reduceRight`,
    `reverse`,
    `shift`,
    `slice`,
    `some`,
    `sort`,
    `splice`,
    `unshift`
  - ES6:
    `copyWithin` (0.3.7),
    `fill`,
    `find`,
    `findIndex`
  - ES7: `includes`
  - ES2023:
    `toReversed` (0.8.0),
    `toSorted` (0.8.0),
    `toSpliced` (0.8.0)
- `ArrayBuffer` methods
  (0.3.8):
  - ES6:
    `isView`
- `ArrayBuffer` prototype methods
  (0.3.8):
  - ES6:
    `slice`
- `Typed-array` constructors
  (0.3.8):
  - ES6:
    `Int8Array`,
    `Uint8Array`,
    `Uint8ClampedArray`,
    `Int16Array`,
    `Uint16Array`,
    `Int32Array`,
    `Uint32Array`,
    `Float32Array`,
    `Float64Array`
- `Typed-array` prototype methods
  (0.3.8):
  - ES6:
    `copyWithin`,
    `every` (0.4.4),
    `fill`,
    `filter` (0.4.4),
    `find` (0.4.4),
    `findIndex` (0.4.4),
    `forEach` (0.4.4),
    `includes` (0.4.4),
    `indexOf` (0.4.4),
    `join`,
    `lastIndexOf` (0.4.4),
    `map` (0.4.4),
    `reduce` (0.4.4),
    `reduceRight` (0.4.4),
    `reverse` (0.4.4),
    `set`,
    `slice`,
    `some` (0.4.4),
    `sort` (0.4.2),
    `subarray`,
    `toString`
  - ES2023:
    `toReversed` (0.8.0),
    `toSorted` (0.8.0)
- `Promise` methods
  (0.3.8):
  - ES6:
    `all` (0.6.2),
    `race` (0.6.2),
    `reject`,
    `resolve`
  - ES2020:
    `allSettled` (0.6.2)
  - ES2021:
    `any` (0.6.2)
- `Promise` prototype methods
  (0.3.8):
  - ES6:
    `catch`,
    `finally`,
    `then`
- `Function` prototype methods:
  - ES5.1:
    `apply`,
    `bind`,
    `call`
- `RegExp` prototype accessor properties:
  - `flags` (0.6.0),
    `global`,
    `ignoreCase`,
    `multiline`,
    `source`,
    `sticky` (0.6.0)
- `RegExp` prototype methods:
  - `[@@replace]` (0.4.2),
    `[@@split]` (0.6.0)
  - ES5.1:
    `exec`,
    `test`,
    `toString`
- `RegExp` instance properties:
  - `lastIndex`
- `RegExp` ES9 named capture groups (0.3.2)
- `DataView` prototype methods
  (0.4.4):
  - ES6:
    `getFloat32`,
    `getFloat64`,
    `getInt16`,
    `getInt32`,
    `getInt8`,
    `getUint16`,
    `getUint32`,
    `getUint8`,
    `setFloat32`,
    `setFloat64`,
    `setInt16`,
    `setInt32`,
    `setInt8`,
    `setUint16`,
    `setUint32`,
    `setUint8`
- `Date` methods:
  - ES5.1:
    `now`,
    `parse`,
    `UTC`
- `Date` prototype methods:
  - ES5.1:
    `getDate`,
    `getDay`,
    `getFullYear`,
    `getHours`,
    `getMilliseconds`,
    `getMinutes`,
    `getMonth`,
    `getSeconds`,
    `getTime`,
    `getTimezoneOffset`,
    `getUTCDate`,
    `getUTCDay`,
    `getUTCFullYear`,
    `getUTCHours`,
    `getUTCMilliseconds`,
    `getUTCMinutes`,
    `getUTCMonth`,
    `getUTCSeconds`,
    `toDateString`,
    `toISOString`,
    `toLocaleDateString`,
    `toLocaleString`,
    `toLocaleTimeString`,
    `toTimeString`,
    `toUTCString`,
    `setDate`,
    `setFullYear`,
    `setHours`,
    `setMinutes`,
    `setMilliseconds`,
    `setMonth`,
    `setSeconds`,
    `setTime`,
    `setUTCDate`,
    `setUTCFullYear`,
    `setUTCHours`,
    `setUTCMilliseconds`,
    `setUTCMinutes`,
    `setUTCMonth`,
    `setUTCSeconds`
- `JSON` methods:
  - ES5.1:
    `parse`,
    `stringify`
- `Symbol` methods
  (0.7.6):
  - `for`,
    `keyFor`
- ES5.1 `arguments` object (0.2.5)
- ES6 rest parameters syntax (without destructuring support) (0.2.7)
- ES5.1 global functions:
  `decodeURI`,
  `decodeURIComponent`,
  `encodeURI`,
  `encodeURIComponent`,
  `isFinite`,
  `isNaN`,
  `parseFloat`,
  `parseInt`
- `Error` objects:
  `Error`,
  `EvalError`,
  `InternalError`,
  `RangeError`,
  `ReferenceError`,
  `SyntaxError`,
  `TypeError`,
  `URIError`
- ES6 modules support: default `export` and default `import` statements (0.3.0)
- ES6 arrow functions (0.3.1)
- Template literals: multiline strings, expression interpolation, nesting templates (0.3.2)
