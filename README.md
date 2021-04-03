[![Build Status](https://travis-ci.org/farrokhi/dnsdiag.svg)](https://travis-ci.org/farrokhi/dnsdiag) [![PyPI](https://img.shields.io/pypi/v/dnsdiag.svg?maxAge=8600)](https://pypi.python.org/pypi/dnsdiag/) [![PyPI](https://img.shields.io/pypi/l/dnsdiag.svg?maxAge=8600)]() [![PyPI](https://img.shields.io/pypi/pyversions/dnsdiag.svg?maxAge=8600)]() [![Docker Pulls](https://img.shields.io/docker/pulls/farrokhi/dnsdiag)](https://hub.docker.com/r/farrokhi/dnsdiag) [![GitHub stars](https://img.shields.io/github/stars/farrokhi/dnsdiag.svg?style=social&label=Star&maxAge=8600)](https://github.com/farrokhi/dnsdiag/stargazers) 

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
docker run -it --rm farrokhi/dnsdiag ./dnsping.py
```

# dnsping
dnsping pings a DNS resolver by sending an arbitrary DNS query for given number of times.
In addition to UDP, you can ping using TCP, DoT (DNS over TLS) and DoH (DNS over HTTPS) using `--tcp`, `--tls` and `--doh` respectively.

```
./dnsping.py -c 3 --tls -t AAAA -s 8.8.8.8 dnsdiag.org                                                                                                                      (eliminate-stub-resolver *!)
dnsping.py DNS: 8.8.8.8:853, hostname: dnsdiag.org, proto: TLS, rdatatype: AAAA, flags: RD
110 bytes from 8.8.8.8: seq=1   time=396.299 ms
110 bytes from 8.8.8.8: seq=2   time=314.991 ms
110 bytes from 8.8.8.8: seq=3   time=106.758 ms

--- 8.8.8.8 dnsping statistics ---
3 requests transmitted, 3 responses received, 0% lost
min=106.758 ms, avg=272.683 ms, max=396.299 ms, stddev=149.335 ms
```
It also displays statistics such as minimum, maximum and average response time as well as
jitter (stddev) and lost packets

# dnstraceroute
dnstraceroute is a traceroute utility to figure out the path that your DNS
request is passing through to get to its destination. You may want to compare
it to your actual network traceroute and make sure your DNS traffic is not
routed to any unwanted path.

```
% ./dnstraceroute.py --expert -C -t A -s 8.8.4.4 facebook.com
dnstraceroute.py DNS: 8.8.4.4:53, hostname: facebook.com, rdatatype: A
1	192.168.0.1 (192.168.0.1) 1 ms
2	192.168.28.177 (192.168.28.177) 4 ms
3	192.168.0.1 (192.168.0.1) 693 ms
4	172.19.4.17 (172.19.4.17) 3 ms
5	dns.google (8.8.4.4) 8 ms

=== Expert Hints ===
 [*] public DNS server is next to a private IP address (possible hijacking)
```

Using `--expert` will instruct dnstraceroute to print expert hints (such as warnings of possible DNS traffic hijacking).

# dnseval
dnseval is a bulk ping utility that sends an arbitrary DNS query to a give list
of DNS servers. This script is meant for comparing response time of multiple
DNS servers at once:
```
% ./dnseval.py -t AAAA -f public-servers.txt -c10 yahoo.com
server                   avg(ms)     min(ms)     max(ms)     stddev(ms)  lost(%)  ttl        flags                  response
----------------------------------------------------------------------------------------------------------------------------
1.0.0.1                  7.228       7.047       7.527       0.150       %0       520        QR -- -- RD RA -- --   NOERROR
1.1.1.1                  7.078       6.957       7.235       0.089       %0       533        QR -- -- RD RA -- --   NOERROR
2606:4700:4700::1001     7.275       7.060       7.752       0.200       %0       1477       QR -- -- RD RA -- --   NOERROR
2606:4700:4700::1111     7.253       7.051       7.434       0.123       %0       520        QR -- -- RD RA -- --   NOERROR
195.46.39.39             7.200       7.036       7.410       0.124       %0       484        QR -- -- RD RA -- --   NOERROR
195.46.39.40             7.243       7.074       7.930       0.254       %0       483        QR -- -- RD RA -- --   NOERROR
208.67.220.220           6.699       6.656       6.773       0.033       %0       1019       QR -- -- RD RA -- --   NOERROR
208.67.222.222           6.761       6.671       7.208       0.160       %0       1018       QR -- -- RD RA -- --   NOERROR
2620:0:ccc::2            6.859       6.742       7.245       0.187       %0       1017       QR -- -- RD RA -- --   NOERROR
2620:0:ccd::2            6.779       6.699       7.200       0.151       %0       1019       QR -- -- RD RA -- --   NOERROR
216.146.35.35            6.827       6.675       7.066       0.130       %0       228        QR -- -- RD RA -- --   NOERROR
216.146.36.36            77.712      72.345      80.162      3.339       %10      57         QR -- -- RD RA -- --   NOERROR
209.244.0.3              7.062       6.965       7.254       0.083       %0       200        QR -- -- RD RA -- --   NOERROR
209.244.0.4              7.036       6.922       7.183       0.072       %0       369        QR -- -- RD RA -- --   NOERROR
4.2.2.1                  7.100       7.005       7.318       0.092       %0       475        QR -- -- RD RA -- --   NOERROR
4.2.2.2                  7.063       7.027       7.127       0.031       %0       1231       QR -- -- RD RA -- --   NOERROR
4.2.2.3                  7.068       6.996       7.116       0.035       %0       979        QR -- -- RD RA -- --   NOERROR
4.2.2.4                  7.096       6.981       7.228       0.077       %0       979        QR -- -- RD RA -- --   NOERROR
4.2.2.5                  7.097       6.999       7.241       0.083       %0       368        QR -- -- RD RA -- --   NOERROR
80.80.80.80              149.838     53.340      348.011     111.651     %0       1798       QR -- -- RD RA -- --   NOERROR
80.80.81.81              241.220     53.368      508.663     131.759     %0       1799       QR -- -- RD RA -- --   NOERROR
8.8.4.4                  6.981       6.766       7.329       0.206       %0       440        QR -- -- RD RA -- --   NOERROR
8.8.8.8                  7.029       6.773       7.331       0.212       %0       1317       QR -- -- RD RA -- --   NOERROR
2001:4860:4860::8844     7.513       7.154       7.958       0.304       %0       710        QR -- -- RD RA -- --   NOERROR
2001:4860:4860::8888     7.444       6.938       7.905       0.350       %0       1545       QR -- -- RD RA -- --   NOERROR
9.9.9.9                  7.564       6.902       8.915       0.764       %0       1800       QR -- -- RD RA -- --   NOERROR
2620:fe::fe              7.188       6.811       8.069       0.375       %0       1800       QR -- -- RD RA -- --   NOERROR
```

### Author

Babak Farrokhi 

- twitter: [@farrokhi](https://twitter.com/farrokhi)
- github: [github.com/farrokhi](https://github.com/farrokhi/)
- website: [farrokhi.net](https://farrokhi.net/)


### License

dnsdiag is released under a 2 clause BSD license.
