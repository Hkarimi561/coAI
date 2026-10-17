# Module ngx_otel_module

 The `ngx_otel_module` module provides [OpenTelemetry](https://opentelemetry.io) distributed tracing support. The module supports [W3C](https://w3c.github.io/trace-context) context propagation and OTLP/gRPC export protocol. 

 The source code of the module is available [here](https://github.com/nginx/nginx-otel). Download and install instructions are available [here](https://github.com/nginx/nginx-otel/blob/main/README.md). 

 The module is also available in a prebuilt
`nginx-module-otel` package since 1.25.3 and in `nginx-plus-module-otel` package as part of our *(commercial subscription)* commercial subscription since 1.23.4. 

## Example Configuration

```
load_module modules/ngx_otel_module.so;

events {
}

http {

    otel_exporter {
        endpoint localhost:4317;
    }

    server {
        listen 127.0.0.1:8080;

        location / {
            otel_trace         on;
            otel_trace_context inject;

            proxy_pass http://backend;
        }
    }
}
```

## Directives

### otel_exporter

**Syntax:** `otel_exporter ;`  
**Default:** —  
**Context:** http  

Specifies OTel data export parameters:

- **`endpoint [(http|https)://]host:port;`** — OTLP/gRPC endpoint that will accept telemetry data. TLS is supported since 0.1.2.
- **`trusted_certificate path;`** — the CA certificates file in PEM format used to verify TLS endpoint (since 0.1.2). Defaults to OS provided CA bundle.
- **`header name value;`** — a custom HTTP header to add to telemetry export request (since 0.1.2).
- **`interval time;`** — the maximum interval between two exports, by default is `5` seconds.
- **`batch_size number;`** — the maximum number of spans to be sent in one batch per worker, by default is `512`.
- **`batch_count number;`** — the number of pending batches per worker, spans exceeding the limit are dropped, by default is `4`.

Example:

```
otel_exporter {
    endpoint https://otel-example.nginx.com:4317;

    header X-API-Token "my-token-value";
}
```

### otel_service_name

**Syntax:** `otel_service_name name;`  
**Default:** `otel_service_name unknown_service:nginx;`  
**Context:** http  

 Sets the “[`service.name`](https://opentelemetry.io/docs/reference/specification/resource/semantic_conventions/#service)” attribute of the OTel resource. 

### otel_resource_attr

**Syntax:** `otel_resource_attr name value;`  
**Default:** —  
**Context:** http  
**Appeared in:** 0.1.2

 Sets a custom OTel resource attribute. 

### otel_trace

**Syntax:** `otel_trace on | off | $variable;`  
**Default:** `otel_trace off;`  
**Context:** http, server, location  

Enables or disables OpenTelemetry tracing.
The directive can also be enabled by specifying a variable:

```
split_clients "$otel_trace_id" $ratio_sampler {
              10%              on;
              *                off;
}

server {
    location / {
        otel_trace         $ratio_sampler;
        otel_trace_context inject;
        proxy_pass         http://backend;
    }
}
```

### otel_trace_context

**Syntax:** `otel_trace_context extract | inject | propagate | ignore;`  
**Default:** `otel_trace_context ignore;`  
**Context:** http, server, location  

Specifies how to propagate
[traceparent/tracestate](https://www.w3.org/TR/trace-context/#design-overview) headers:

- **`extract`** — uses an existing trace context from the request, so that the identifiers of a trace and the parent span are inherited from the incoming request.
- **`inject`** — adds a new context to the request, overwriting existing headers, if any.
- **`propagate`** — updates the existing context (combines extract and inject).
- **`ignore`** — skips context headers processing.

### otel_span_name

**Syntax:** `otel_span_name name;`  
**Default:** —  
**Context:** http, server, location  

 Defines the name of the OTel [span](https://opentelemetry.io/docs/concepts/observability-primer/#spans). By default, it is a name of the location for a request. The name can contain variables. 

### otel_span_attr

**Syntax:** `otel_span_attr name value;`  
**Default:** —  
**Context:** http, server, location  

 Adds a custom OTel span attribute. The value can contain variables. 

## Default span attributes

The following
[span
attributes](https://opentelemetry.io/docs/specs/semconv/registry/attributes/http/)
are added automatically:

- `http.method`
- `http.target`
- `http.route`
- `http.scheme`
- `http.flavor`
- `http.user_agent`
- `http.request_content_length`
- `http.response_content_length`
- `http.status_code`
- `net.host.name`
- `net.host.port`
- `net.sock.peer.addr`
- `net.sock.peer.port`

## Embedded Variables

- **`$otel_trace_id`** — the identifier of the trace the current span belongs to, for example, `56552bc4daa3bf39c08362527e1dd6c4`
- **`$otel_span_id`** — the identifier of the current span, for example, `4c0b8531ec38ca59`
- **`$otel_parent_id`** — the identifier of the parent span, for example, `dc94d281b0f884ea`
- **`$otel_parent_sampled`** — the “`sampled`” flag of the parent span, can be “`1`” or “`0`”
