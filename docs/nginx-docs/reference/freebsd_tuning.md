# Tuning FreeBSD for the highload

## Listen queues

After the connection has been established it is placed in the listen queue
of the listen socket.
To see the current listen queues state, you may run the command
“`netstat -Lan`”:

```
Current listen queue sizes (qlen/incqlen/maxqlen)
Proto Listen         Local Address
tcp4  10/0/128       *.80
tcp4  0/0/128        *.22
```

This is a normal case: the listen queue of the port *:80 contains
just 10 unaccepted connections.
If the web server is not able to handle the load, you may see
something like this:

```
Current listen queue sizes (qlen/incqlen/maxqlen)
Proto Listen         Local Address
tcp4  192/0/128      *.80
tcp4  0/0/128        *.22
```

Here are 192 unaccepted connections and most likely new coming connections
are discarding. Although the limit is 128 connections, FreeBSD allows
receiving 1.5 times connections than the limit before it starts to discard
the new connections. You may increase the limit using

```
sysctl kern.ipc.soacceptqueue=4096
```

However, note that the queue is only a damper to quench bursts.
If it is always overflowed, this means that you need to improve the web server,
but not to continue to increase the limit.
You may also change the listen queue maximum size in nginx configuration:

```
listen  80  backlog=1024;
```

However, you may not set it more than the current
`kern.ipc.soacceptqueue` value.
By default nginx uses the maximum value of FreeBSD kernel.

## Socket buffers

 When a client sends a data, the data first is received by the kernel which places the data in the socket receiving buffer. Then an application such as the web server may call `recv` or `read` system calls to get the data from the buffer. When the application wants to send a data, it calls
`send` or `write` system calls to place the data in the socket sending buffer. Then the kernel manages to send the data from the buffer to the client. In modern FreeBSD versions the default sizes of the socket receiving and sending buffers are respectively 64K and 32K. You may change them on the fly using the sysctls
`net.inet.tcp.recvspace` and
`net.inet.tcp.sendspace`. Of course the bigger buffer sizes may increase throughput, because connections may use bigger TCP sliding windows sizes. And on the Internet you may see recommendations to increase the buffer sizes to one or even several megabytes. However, such large buffer sizes are suitable for local networks or for networks under your control. Since on the Internet a slow network client may ask a large file and then it will download the file during several minutes if not hours. All this time the megabyte buffer will be bound to the slow client, although we may devote just several kilobytes to it. 

 There is one more advantage of the large sending buffers for the web servers such as Apache which use the blocking I/O system calls. The server may place a whole large response in the sending buffer, then may close the connection, and let the kernel to send the response to a slow client, while the server is ready to serve other requests. You should decide what is it better to bind to a client in your case: a tens megabytes Apache/mod_perl process or the hundreds kilobytes socket sending buffer. Note that nginx uses non-blocking I/O system calls and devotes just tens kilobytes to connections, therefore it does not require the large buffer sizes. 

## mbufs, mbuf clusters, etc.

Inside the kernel the buffers are stored in the form of chains of
memory chunks linked using the *mbuf* structures.
The mbuf size is 256 bytes and it can be used to store a small amount
of data, for example, TCP/IP header. However, the mbufs point mostly
to other data stored in the *mbuf clusters* or *jumbo clusters*,
and in this kind they are used as the chain links only.
The mbuf cluster size is 2K.
The jumbo cluster size can be equal to a CPU page size (4K for amd64),
9K, or 16K.
The 9K and 16K jumbo clusters are used mainly in local networks with Ethernet
frames larger than usual 1500 bytes, and they are beyond the scope of
this article.
The page size jumbo clusters are usually used for sending only,
while the mbuf clusters are used for both sending and receiving.

To see the current usage of the mbufs and clusters and their limits,
you may run the command “`netstat -m`”.
Here is a sample from FreeBSD 7.2/amd64 with the default settings:

```
1477/3773/5250 mbufs in use (current/cache/total)
771/2203/2974/25600 mbuf clusters in use (current/cache/total/max)
771/1969 mbuf+clusters out of packet secondary zone in use
   (current/cache)
296/863/1159/12800 4k (page size) jumbo clusters in use
   (current/cache/total/max)
0/0/0/6400 9k jumbo clusters in use (current/cache/total/max)
0/0/0/3200 16k jumbo clusters in use (current/cache/total/max)
3095K/8801K/11896K bytes allocated to network(current/cache/total)
0/0/0 requests for mbufs denied (mbufs/clusters/mbuf+clusters)
0/0/0 requests for jumbo clusters denied (4k/9k/16k)
0/0/0 sfbufs in use (current/peak/max)
0 requests for sfbufs denied
0 requests for sfbufs delayed
523590 requests for I/O initiated by sendfile
0 calls to protocol drain routines
```

There are 12800 page size jumbo clusters,
therefore they can store only 50M of data.
If you set the `net.inet.tcp.sendspace` to 1M,
then merely 50 slow clients will take all jumbo clusters
requesting large files.

You may increase the clusters limits on the fly using:

```
sysctl kern.ipc.nmbclusters=200000
sysctl kern.ipc.nmbjumbop=100000
```

The former command increases the mbuf clusters limit
and the latter increases page size jumbo clusters limit.
Note that all allocated mbufs clusters will take about 440M physical memory:
(200000 × (2048 + 256)) because each mbuf cluster requires also the mbuf.
All allocated page size jumbo clusters will take yet about 415M physical memory:
(100000 × (4096 + 256)).
And together they may take 845M.

 There is way not to use the jumbo clusters while serving static files: the *sendfile()* system call. The sendfile allows sending a file or its part to a socket directly without reading the parts in an application buffer. It creates the mbufs chain where the mbufs point to the file pages that are already present in FreeBSD cache memory, and passes the chain to the TCP/IP stack. Thus, sendfile decreases both CPU usage by omitting two memory copy operations, and memory usage by using the cached file pages. 

## Outgoing connections

```
net.inet.ip.portrange.randomized=0
net.inet.ip.portrange.first=1024
net.inet.ip.portrange.last=65535
```

## Finalizing connection

```
net.inet.tcp.fast_finwait2_recycle=1
```
