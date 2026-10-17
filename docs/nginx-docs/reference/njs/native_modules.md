# Native modules

## Overview

 Native modules allow loading C-based shared libraries (.so files) into NGINX JavaScript for performance-critical operations or system-level integrations. This feature is available only with the QuickJS engine and is not supported by the njs native engine. Native module support has been available since 0.9.5. 

## When to use native modules

Native modules are useful in the following scenarios:

- Performance-critical operations that exceed JavaScript capabilities
- System-level integrations requiring C libraries
- Leveraging existing C/C++ codebases

 Native modules should be used for low-level primitives rather than for complex business logic, for example, for cryptographic operations (hashing, encryption), data compression/decompression, binary protocol parsing, high-performance string operations, or mathematical computations. Complex application logic should remain in JavaScript where it's easier to maintain, debug, and modify. 

Limitations:

- Native modules must be compiled for the same architecture as NGINX
- Native modules run with full process privileges and require careful security review

## Loading native modules in NGINX

Native modules are loaded using these directives
specified in the `main` context:

- js_load_http_native_module for HTTP context
- js_load_stream_native_module for Stream context

Example configuration:

```
js_load_http_native_module /path/to/mylib.so;
js_load_http_native_module /path/to/other.so as myalias;

http {
    js_import main.js;

    server {
        listen 8000;
        location / {
            js_content main.handler;
        }
    }
}
```

Once loaded, the module can be imported in JavaScript code:

```
// Import by filename
import * as mylib from 'mylib.so';

// Import by alias
import * as myalias from 'myalias';

function handler(r) {
    let result = mylib.add(5, 10);
    r.return(200, `Result: ${result}\n`);
}

export default { handler };
```

## Building native modules

 Native modules must implement the `js_init_module` function as the entry point. This function is called by QuickJS when the module is loaded. 

A complete example of a simple native module
that exports two functions:

```
#include <quickjs.h>

#define countof(x) (sizeof(x) / sizeof((x)[0]))

/* Add two numbers */
static JSValue
js_add(JSContext *ctx, JSValueConst this_val, int argc, JSValueConst *argv)
{
    int a, b;

    if (argc < 2) {
        return JS_ThrowTypeError(ctx, "expected 2 arguments");
    }

    if (JS_ToInt32(ctx, &a, argv[0]) < 0) {
        return JS_EXCEPTION;
    }

    if (JS_ToInt32(ctx, &b, argv[1]) < 0) {
        return JS_EXCEPTION;
    }

    return JS_NewInt32(ctx, a + b);
}

/* Reverse a string */
static JSValue
js_reverse_string(JSContext *ctx, JSValueConst this_val, int argc,
    JSValueConst *argv)
{
    char        *reversed;
    size_t       i, len;
    JSValue      result;
    const char  *str;

    if (argc < 1) {
        return JS_ThrowTypeError(ctx, "expected 1 argument");
    }

    str = JS_ToCStringLen(ctx, &len, argv[0]);
    if (!str) {
        return JS_EXCEPTION;
    }

    reversed = js_malloc(ctx, len + 1);
    if (!reversed) {
        JS_FreeCString(ctx, str);
        return JS_EXCEPTION;
    }

    for (i = 0; i < len; i++) {
        reversed[i] = str[len - 1 - i];
    }
    reversed[len] = '\0';

    result = JS_NewString(ctx, reversed);

    js_free(ctx, reversed);
    JS_FreeCString(ctx, str);

    return result;
}

/* Module function list */
static const JSCFunctionListEntry js_module_funcs[] = {
    JS_CFUNC_DEF("add", 2, js_add),
    JS_CFUNC_DEF("reverseString", 1, js_reverse_string),
};

/* Module initialization */
static int
js_module_init(JSContext *ctx, JSModuleDef *m)
{
    return JS_SetModuleExportList(ctx, m, js_module_funcs,
                                  countof(js_module_funcs));
}

/* Required entry point */
JSModuleDef *
js_init_module(JSContext *ctx, const char *module_name)
{
    JSModuleDef  *m;

    m = JS_NewCModule(ctx, module_name, js_module_init);
    if (!m) {
        return NULL;
    }

    JS_AddModuleExportList(ctx, m, js_module_funcs,
                           countof(js_module_funcs));

    return m;
}
```

To compile the native module:

```
gcc -fPIC -shared -I/path/to/quickjs -o mymodule.so mymodule.c
```

where `/path/to/quickjs` is the directory
containing the QuickJS header files.

 > **Note:** For proper memory tracking, always use QuickJS memory allocation functions (`js_malloc`, `js_free`) instead of standard library functions (`malloc`, `free`).   

## Additional resources

For more information about the QuickJS C API:

- [QuickJS official website](https://bellard.org/quickjs/)
- QuickJS header file (`quickjs.h`) contains comprehensive API documentation
