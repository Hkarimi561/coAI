# Contributing Changes

## Getting Sources

[GitHub](https://github.com) is used
to store source code.
The [repository](https://github.com/nginx/nginx) can be cloned
with the following command:

```
git clone https://github.com/nginx/nginx.git
```

## Formatting Changes

 Changes should be formatted according to the code style used by nginx. Sometimes, there is no clear rule; in such cases examine how existing nginx sources are formatted and mimic this style. Changes will more likely be accepted if style corresponds to the surrounding code. 

 [Commit](https://docs.github.com/en/pull-requests/committing-changes-to-your-project/creating-and-editing-commits/about-commits) the changes in your nginx GitHub fork. Please ensure that the specified [e-mail](https://docs.github.com/en/get-started/getting-started-with-git/setting-your-username-in-git) address and real name of the author are correct. 

The commit message should have a single-line synopsis followed by verbose
description after an empty line.
Limit the subject and commit message body lines to 72 characters.
The resulting commit can be obtained using the
`git show` command:

```
commit 067d766f210ee914b750d79d9284cbf8801058f3
Author: Zoey <username@example.com>
Date:   Sun Apr 5 11:31:15 2026 +0200

    Fix $request_port and $is_request_port in subrequests

    Closes #1247.

diff --git a/src/http/ngx_http_core_module.c b/src/http/ngx_http_core_module.c
index 0c46106db..53ddf39bb 100644
--- a/src/http/ngx_http_core_module.c
+++ b/src/http/ngx_http_core_module.c
@@ -2453,6 +2453,8 @@ ngx_http_subrequest(ngx_http_request_t *r,
     sr->method = NGX_HTTP_GET;
     sr->http_version = r->http_version;

+    sr->port = r->port;
+
     sr->request_line = r->request_line;
     sr->uri = *uri;
```

## Before Submitting

Several points are worth to consider before submitting changes:
- The proposed changes should work properly on a wide range of supported platforms.
- Try to make it clear why the suggested change is needed, and provide a use case, if possible.
- Passing your changes through the test suite is a good way to ensure
  that they do not cause a regression.
  The [repository](https://github.com/nginx/nginx-tests) with
  tests can be cloned with the following command:
  
  ```
  git clone https://github.com/nginx/nginx-tests.git
  ```

## Submitting Changes

 The proposed changes should be submitted from your fork to [nginx repository](https://github.com/nginx/nginx) as a [pull request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork). 

## Website

GitHub is used to store the sources for this website.
The [repository](https://www.github.com/nginx/nginx.org)
can be cloned with the following command:

```
git clone https://github.com/nginx/nginx.org.git
```

Documentation changes should be submitted from your fork
as a pull request.

## License

 Submitting changes implies granting project a permission to use it under an appropriate [license](../../LICENSE).
