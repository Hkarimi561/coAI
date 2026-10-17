# Module ngx_http_xslt_module

 The `ngx_http_xslt_module` (0.7.8+) is a filter that transforms XML responses using one or more XSLT stylesheets. 

 This module is not built by default, it should be enabled with the
`--with-http_xslt_module` configuration parameter. > **Note:** This module requires the [libxml2](http://xmlsoft.org) and [libxslt](http://xmlsoft.org/XSLT/) libraries.   

## Example Configuration

```
location / {
    xml_entities    /site/dtd/entities.dtd;
    xslt_stylesheet /site/xslt/one.xslt param=value;
    xslt_stylesheet /site/xslt/two.xslt;
}
```

## Directives

### xml_entities

**Syntax:** `xml_entities path;`  
**Default:** —  
**Context:** http, server, location  

Specifies the DTD file that declares character entities.
This file is compiled at the configuration stage.
For technical reasons, the module is unable to use the
external subset declared in the processed XML, so it is
ignored and a specially defined file is used instead.
This file should not describe the XML structure.
It is enough to declare just the required character entities, for example:

```
<!ENTITY nbsp "&#xa0;">
```

### xml_external_entities

**Syntax:** `xml_external_entities on | off;`  
**Default:** `xml_external_entities off;`  
**Context:** http, server, location  
**Appeared in:** 1.31.3

 Enables or disables loading of external entities declared in the internal DTD subset of the processed XML. Only loading of file-based external entities is supported. > **Note:** To prevent reading arbitrary local files accessible to the worker process, it is recommended to enable external entities only when the processed XML is trusted.   

### xslt_last_modified

**Syntax:** `xslt_last_modified on | off;`  
**Default:** `xslt_last_modified off;`  
**Context:** http, server, location  
**Appeared in:** 1.5.1

 Allows preserving the `Last-Modified` header field from the original response during XSLT transformations to facilitate response caching. 

 By default, the header field is removed as contents of the response are modified during transformations and may contain dynamically generated elements or parts that are changed independently of the original response. 

### xslt_param

**Syntax:** `xslt_param parameter value;`  
**Default:** —  
**Context:** http, server, location  
**Appeared in:** 1.1.18

 Defines the parameters for XSLT stylesheets. The *value* is treated as an XPath expression. The *value* can contain variables. To pass a string value to a stylesheet, the xslt_string_param directive can be used. 

 There could be several `xslt_param` directives. These directives are inherited from the previous configuration level if and only if there are no `xslt_param` and xslt_string_param directives defined on the current level. 

### xslt_string_param

**Syntax:** `xslt_string_param parameter value;`  
**Default:** —  
**Context:** http, server, location  
**Appeared in:** 1.1.18

 Defines the string parameters for XSLT stylesheets. XPath expressions in the *value* are not interpreted. The *value* can contain variables. 

 There could be several `xslt_string_param` directives. These directives are inherited from the previous configuration level if and only if there are no xslt_param and
`xslt_string_param` directives defined on the current level. 

### xslt_stylesheet

**Syntax:** `xslt_stylesheet stylesheet [parameter=value ...];`  
**Default:** —  
**Context:** location  

 Defines the XSLT stylesheet and its optional parameters. A stylesheet is compiled at the configuration stage. 

Parameters can either be specified separately, or grouped in a
single line using the “`:`” delimiter.
If a parameter includes the “`:`” character,
it should be escaped as “`%3A`”.
Also, `libxslt` requires to enclose parameters
that contain non-alphanumeric characters into single or double quotes,
for example:

```
param1='http%3A//www.example.com':param2=value2
```

The parameters description can contain variables, for example,
the whole line of parameters can be taken from a single variable:

```
location / {
    xslt_stylesheet /site/xslt/one.xslt
                    $arg_xslt_params
                    param1='$value1':param2=value2
                    param3=value3;
}
```

 It is possible to specify several stylesheets. They will be applied sequentially in the specified order. 

### xslt_types

**Syntax:** `xslt_types mime-type ...;`  
**Default:** `xslt_types text/xml;`  
**Context:** http, server, location  

 Enables transformations in responses with the specified MIME types in addition to “`text/xml`”. The special value “`*`” matches any MIME type (0.8.29). If the transformation result is an HTML response, its MIME type is changed to “`text/html`”.
