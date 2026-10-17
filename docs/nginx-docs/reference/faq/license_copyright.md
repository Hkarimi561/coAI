# How can nginx copyright be acknowledged                when using nginx as part of a proprietary                software distribution?

 Q: I’d like to use nginx distribution as part of my proprietary software package. How can nginx copyright be acknowledged when using nginx as part of a proprietary software distribution? 

   

A:
The text below should be added to your license conditions,
followed by the text of the applicable 2-clause BSD license described
[here](http://nginx.org/LICENSE).

```
This product contains software provided by Nginx, Inc. and its contributors.
```

 Also, if your build of nginx includes any of the following 3rd party products: zlib, PCRE, OpenSSL — it’s worth including their copyright acknowledgements and disclaimers as well.
