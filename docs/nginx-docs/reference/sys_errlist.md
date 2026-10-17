# A message “ ‘sys_errlist’                 is deprecated;                 use ‘strerror’ or ‘strerror_r’                 instead ”

Q:
While building nginx version 0.7.66, 0.8.35 or higher on Linux
the following warning messages are issued:

```
warning: `sys_errlist' is deprecated;
    use `strerror' or `strerror_r' instead
warning: `sys_nerr' is deprecated;
    use `strerror' or `strerror_r' instead
```

 A: This is normal: nginx has to use the deprecated sys_errlist[] and sys_nerr in signal handlers because strerror() and strerror_r() functions are not Async-Signal-Safe.
