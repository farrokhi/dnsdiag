[![Build Status](https://travis-ci.org/farrokhi/dnsdiag.svg)](https://travis-ci.org/farrokhi/dnsdiag) [![PyPI](https://img.shields.io/pypi/v/dnsdiag.svg?maxAge=8600)](https://pypi.python.org/pypi/dnsdiag/) [![PyPI](https://img.shields.io/pypi/l/dnsdiag.svg?maxAge=8600)]() [![Downloads](https://static.pepy.tech/personalized-badge/dnsdiag?period=total&units=international_system&left_color=grey&right_color=blue&left_text=PyPi%20Downloads)](https://pepy.tech/project/dnsdiag) [![PyPI](https://img.shields.io/pypi/pyversions/dnsdiag.svg?maxAge=8600)]() [![Docker Pulls](https://img.shields.io/docker/pulls/farrokhi/dnsdiag)](https://hub.docker.com/r/farrokhi/dnsdiag) [![GitHub stars](https://img.shields.io/github/stars/farrokhi/dnsdiag.svg?style=social&label=Star&maxAge=8600)](https://github.com/farrokhi/dnsdiag/stargazers) 

DNS Measurement, Troubleshooting and Security Auditing Toolset
===============================================================

Ever been wondering if your ISP is [hijacking your DNS traffic](https://medium.com/decentralize-today/is-your-isp-hijacking-your-dns-traffic-f3eb7ccb0ee7)? Ever observed any
misbehavior with your DNS responses? Ever been redirected to wrong address and
suspected something is wrong with your DNS? Here we have a [set of tools](http://github.com/farrokhi/dnsdiag) to
perform basic audits on your DNS requests and responses to make sure your DNS is
working as you expect.

You can measure the response time of any given DNS server for arbitrary requests
using `dnsping`. Just like traditional ping utility, it gives you similar
functionality for DNS requests.

You can also trace the path your DNS request takes to destination to make sure
it is not being redirected or hijacked. This can be done by comparing different
DNS queries being sent to the same DNS server using `dnstraceroute` and observe
if there is any difference between the path.

`dnseval` evaluates multiple DNS resolvers and helps you choose the best DNS
server for your network. While it is highly recommended using your own DNS
resolver and never trust any third-party DNS server, but in case you need to
choose the best DNS forwarder for your network, `dnseval` lets you compare
different DNS servers from performance (latency) and reliability (loss) point
of view.

# Installation

There are several ways that you can use this toolset. However, using the source code is always recommended.

## Source Code

1. Check out the git repository and install dependencies:

```
git clone https://github.com/farrokhi/dnsdiag.git
cd dnsdiag
pip3 install -r requirements.txt
```

2. You can alternatively install the package using pip:

```
pip3 install dnsdiag
```

## Binary Package

From time to time, binary packages will be released for Windows, Mac OS X and Linux. You can grab the latest release from [releases page](https://github.com/farrokhi/dnsdiag/releases).

## Docker

If you don't want to install dnsdiags on your local machine, you may use the docker image and run programs in a container. For example:

```
docker run --network host -it --rm farrokhi/dnsdiag dnsping.py
```

# dnsping
dnsping pings a DNS resolver by sending an arbitrary DNS query for given number of times.
A complete explanation of supported command line flags is shown by using `--help`. Here are a few useful flags:

- Using `--tcp`, `--tls` and `--doh` to select transport protocol. Default is UDP.
- Using `--flags` to display response flags for each response
- Using `--dnssec` to request DNSSEC if available

In addition to UDP, you can ping using TCP, DoT (DNS over TLS) and DoH (DNS over HTTPS) using `--tcp`, `--tls` and `--doh` respectively.

```shell
./dnsping.py -c 5 --dnssec --flags --tls -t AAAA -s 9.9.9.9 ripe.net
```

```
dnsping.py DNS: 9.9.9.9:853, hostname: ripe.net, proto: TLS, rdatatype: AAAA, flags: RD
169 bytes from 9.9.9.9: seq=1   time=279.805 ms [QR RD RA AD]  NOERROR
169 bytes from 9.9.9.9: seq=2   time=107.237 ms [QR RD RA AD]  NOERROR
169 bytes from 9.9.9.9: seq=3   time=96.747  ms [QR RD RA AD]  NOERROR
169 bytes from 9.9.9.9: seq=4   time=107.782 ms [QR RD RA AD]  NOERROR
169 bytes from 9.9.9.9: seq=5   time=94.713  ms [QR RD RA AD]  NOERROR

--- 9.9.9.9 dnsping statistics ---
5 requests transmitted, 5 responses received, 0% lost
min=94.713 ms, avg=137.257 ms, max=279.805 ms, stddev=79.908 ms
```

It also displays statistics such as minimum, maximum and average response time as well as
jitter (stddev) and lost packets.

There are several interesting use cases for dnsping, including:

- Comparing response times using different transport protocols (e.g. UDP vs DoH)
- Measuring how reliable your DNS server is, by measuring Jitter and packet loss
- Measuring responses times when DNSSEC is enabled using `--dnssec`

# dnstraceroute
dnstraceroute is a traceroute utility to figure out the path that your DNS
request is passing through to get to its destination. You may want to compare
it to your actual network traceroute and make sure your DNS traffic is not
routed to any unwanted path.

In addition to UDP, it also supports TCP as transport protocol, using `--tcp` flag.

```shell
./dnstraceroute.py --expert --asn -C -t A -s 8.8.4.4 facebook.com
```

```
dnstraceroute.py DNS: 8.8.4.4:53, hostname: facebook.com, rdatatype: A
1	192.168.0.1 (192.168.0.1) 1 ms
2	192.168.28.177 (192.168.28.177) 4 ms
3	192.168.0.1 (192.168.0.1) 693 ms
4	172.19.4.17 (172.19.4.17) 3 ms
5	dns.google (8.8.4.4) [AS15169 GOOGLE, US] 8 ms

=== Expert Hints ===
 [*] public DNS server is next to a private IP address (possible hijacking)
```

Using `--expert` will instruct dnstraceroute to print expert hints (such as 
warnings of possible DNS traffic hijacking).

# dnseval
dnseval is a bulk ping utility that sends an arbitrary DNS query to a give list
of DNS servers. This script is meant for comparing response time of multiple
DNS servers at once.

You can use `dnseval` to compare response times using different transport 
protocols such as UDP (default), TCP, DoT and DoH using `--tcp`, `--tls` and
`--doh` respectively.

```shell
./dnseval.py --dnssec -t AAAA -f public-servers.txt -c10 ripe.net
```

```
server                   avg(ms)     min(ms)     max(ms)     stddev(ms)  lost(%)  ttl        flags                  response
----------------------------------------------------------------------------------------------------------------------------
1.0.0.1                  36.906      7.612       152.866     50.672      %0       300        QR -- -- RD RA AD --   NOERROR
1.1.1.1                  7.752       7.512       8.132       0.183       %0       298        QR -- -- RD RA AD --   NOERROR
2606:4700:4700::1001     7.661       7.169       8.102       0.240       %0       297        QR -- -- RD RA AD --   NOERROR
2606:4700:4700::1111     7.802       7.000       8.128       0.312       %0       296        QR -- -- RD RA AD --   NOERROR
195.46.39.39             14.723      7.024       78.239      22.362      %0       300        QR -- -- RD RA -- --   NOERROR
195.46.39.40             7.524       6.972       10.897      1.191       %0       300        QR -- -- RD RA -- --   NOERROR
208.67.220.220           70.519      6.694       180.229     66.516      %0       300        QR -- -- RD RA AD --   NOERROR
208.67.222.222           37.868      6.663       107.601     41.178      %0       300        QR -- -- RD RA AD --   NOERROR
2620:0:ccc::2            31.471      6.768       178.647     56.546      %0       299        QR -- -- RD RA AD --   NOERROR
2620:0:ccd::2            20.651      6.699       145.029     43.702      %0       300        QR -- -- RD RA AD --   NOERROR
216.146.35.35            19.338      6.713       131.198     39.306      %0       300        QR -- -- RD RA AD --   NOERROR
216.146.36.36            107.741     73.421      266.969     58.003      %0       299        QR -- -- RD RA AD --   NOERROR
209.244.0.3              14.717      7.015       80.329      23.058      %0       300        QR -- -- RD RA -- --   NOERROR
209.244.0.4              7.184       7.003       8.197       0.361       %0       300        QR -- -- RD RA -- --   NOERROR
4.2.2.1                  7.040       6.994       7.171       0.052       %0       299        QR -- -- RD RA -- --   NOERROR
4.2.2.2                  14.358      6.968       79.964      23.052      %0       300        QR -- -- RD RA -- --   NOERROR
4.2.2.3                  7.083       6.945       7.265       0.091       %0       299        QR -- -- RD RA -- --   NOERROR
4.2.2.4                  7.103       6.990       7.238       0.086       %0       299        QR -- -- RD RA -- --   NOERROR
4.2.2.5                  7.100       7.025       7.267       0.074       %0       299        QR -- -- RD RA -- --   NOERROR
80.80.80.80              149.924     53.310      247.395     97.311      %0       299        QR -- -- RD RA AD --   NOERROR
80.80.81.81              144.262     53.360      252.564     97.759      %0       298        QR -- -- RD RA AD --   NOERROR
8.8.4.4                  9.196       7.160       10.974      1.484       %0       299        QR -- -- RD RA AD --   NOERROR
8.8.8.8                  7.847       7.056       9.866       0.836       %0       299        QR -- -- RD RA AD --   NOERROR
2001:4860:4860::8844     31.819      7.194       155.761     50.671      %0       299        QR -- -- RD RA AD --   NOERROR
2001:4860:4860::8888     7.773       7.200       9.814       0.777       %0       298        QR -- -- RD RA AD --   NOERROR
9.9.9.9                  21.894      6.670       81.434      30.299      %0       300        QR -- -- RD RA AD --   NOERROR
2620:fe::fe              21.177      6.723       80.046      30.062      %0       300        QR -- -- RD RA AD --   NOERROR
```

### Author

Babak Farrokhi 

- twitter: [@farrokhi](https://twitter.com/farrokhi)
- github: [github.com/farrokhi](https://github.com/farrokhi/)
- website: [farrokhi.net](https://farrokhi.net/)


### License

dnsdiag is released under a 2 clause BSD license.
