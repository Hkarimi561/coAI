# Command-line interface

njs scripts development and debugging can be performed
from the command-line.
The command-line utility is available after the installation of
the Linux package
or after building from the
sources.
Compared to njs running inside nginx,
nginx objects
(HTTP and
Stream)
are not available in the utility.

```
$ echo "2**3" | njs -q
8

$ njs
>> globalThis
global {
 njs: njs {
  version: '0.3.9'
 },
 global: [Circular],
 process: process {
  argv: [
   '/usr/bin/njs'
  ],
  env: {
   PATH: '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
   HOSTNAME: 'f777c149d4f8',
   TERM: 'xterm',
   NGINX_VERSION: '1.17.9',
   NJS_VERSION: '0.3.9',
   PKG_RELEASE: '1~buster',
   HOME: '/root'
  }
 },
 console: {
  log: [Function: native],
  dump: [Function: native],
  time: [Function: native],
  timeEnd: [Function: native]
 },
 print: [Function: native]
}
>>
```
