# Why nginx doesn’t handle chunked encoding                responses from my backend properly?

Q:
My backend server appears to send HTTP/1.0 responses using
chunked encoding but nginx doesn’t handle it correctly.
For instance, I’m using nginx as a frontend to my node.js
application and instead of pure JSON from backend, nginx
returns something framed in decimal numbers like

```
47
{"error":"query error","message":"Parameter(s) missing: user,password"}
0
```

   

 A: Your backend violates HTTP specification (see [RFC 2616, "3.6 Transfer Codings"](https://datatracker.ietf.org/doc/html/rfc2616#section-3.6)). The "chunked" transfer-codings must not be used with HTTP/1.0. You’d need to either fix your backend application or upgrade to nginx version 1.1.4 and newer, where an additional code was introduced to handle such erratic backend behavior.
