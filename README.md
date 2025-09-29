[![PyPI](https://img.shields.io/pypi/v/dnsdiag.svg?maxAge=8600)](https://pypi.python.org/pypi/dnsdiag/) [![PyPI](https://img.shields.io/pypi/l/dnsdiag.svg?maxAge=8600)]() [![Downloads](https://static.pepy.tech/personalized-badge/dnsdiag?period=total&units=international_system&left_color=grey&right_color=blue&left_text=PyPi%20Downloads)](https://pepy.tech/project/dnsdiag) [![Downloads](https://static.pepy.tech/badge/dnsdiag/month)](https://pepy.tech/project/dnsdiag) [![PyPI](https://img.shields.io/pypi/pyversions/dnsdiag.svg?maxAge=8600)]() [![Docker Pulls](https://img.shields.io/docker/pulls/farrokhi/dnsdiag)](https://hub.docker.com/r/farrokhi/dnsdiag) [![GitHub stars](https://img.shields.io/github/stars/farrokhi/dnsdiag.svg?style=social&label=Star&maxAge=8600)](https://github.com/farrokhi/dnsdiag/stargazers) 

DNS Measurement, Troubleshooting and Security Auditing Toolset
===============================================================

Have you ever wondered if your ISP is [intercepting your DNS
traffic](https://medium.com/decentralize-today/is-your-isp-hijacking-your-dns-traffic-f3eb7ccb0ee7))?
Have you noticed any unusual behavior in your DNS responses, or been redirected to
the wrong address and suspected something might be off with your DNS? We offer a
suite of tools to perform basic audits on your DNS requests and responses, helping
you ensure your DNS is functioning as expected.

With `dnsping`, you can measure the response time of any DNS server for arbitrary
queries. Similar to the regular ping utility, dnsping offers comparable
functionality for DNS requests, helping you monitor server responsiveness.

You can also trace the route of your DNS request to its destination using
`dnstraceroute`, verifying that it isn't being redirected or intercepted. By
comparing DNS queries sent to the same server, `dnstraceroute` allows you to
observe any differences in the paths taken, alerting you to possible issues.


`dnseval` assesses multiple DNS resolvers to help you choose the best DNS resolver
for your network. While using your own DNS resolver is recommended to avoid
reliance on third-party DNS resolvers, `dnseval` can assist in selecting the
optimal DNS resolver when needed. It lets you compare DNS servers based on
performance (latency) and reliability (packet loss), giving you a comprehensive
view for informed decision-making.


# Installation

There are several ways to use this toolset, though we recommend running it
directly from the source code for optimal flexibility and control.

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

## Using uv (Recommended)

[uv](https://docs.astral.sh/uv/) is a fast Python package manager that can run tools directly without installation. This is the easiest way to try dnsdiag tools:

```bash
# Run dnsping directly without installation
uv run --from dnsdiag dnsping google.com

# Run with specific options
uv run --from dnsdiag dnsping -c 5 --tls -s 8.8.8.8 example.com

# Run dnstraceroute
uv run --from dnsdiag dnstraceroute cloudflare.com

# Run dnseval
uv run --from dnsdiag dnseval -f public-servers.txt github.com
```

This approach automatically manages dependencies and ensures you're always using the latest version from PyPI.

## Binary Package

From time to time, binary packages will be released for Windows, Mac OS X and Linux. You can grab the latest release from [releases page](https://github.com/farrokhi/dnsdiag/releases).

## Docker

If you prefer not to install `dnsdiag` on your local machine, you can use the
Docker image to run the tools in a containerized environment. For example:

```
docker run --network host -it --rm farrokhi/dnsdiag dnsping.py
```

# dnsping

`dnsping` allows you to "ping" a DNS resolver by sending an arbitrary DNS query multiple times. For a full list of supported command-line options, use `--help`. Here are a few key flags:

- Use `--tcp`, `--tls`, `--doh`, `--quic` or `--http3` to select the transport protocol (default is UDP).
- Use `--flags` to display response flags, including EDNS flags, for each response.
- Use `--dnssec` to request DNSSEC validation, if available.
- Use `--ede` to display Extended DNS Error messages ([RFC 8914](https://www.rfc-editor.org/rfc/rfc8914)).
- Use `--nsid` to display the Name Server Identifier (NSID) if available ([RFC 5001](https://www.rfc-editor.org/rfc/rfc5001)).
- Use `--ecs` to include EDNS Client Subnet information for geographic routing optimization.

```shell
./dnsping.py -c 5 --dnssec --flags --tls --ede -t AAAA -s 8.8.8.8 brokendnssec.net
```

```
dnsping.py DNS: 8.8.8.8:853, hostname: brokendnssec.net, proto: TLS, class: IN, type: AAAA, flags: [RD]
75  bytes from 8.8.8.8: seq=1   time=73.703 ms  SERVFAIL [QR RD RA -- DO] [EDE:10("For brokendnssec.net/soa")]
75  bytes from 8.8.8.8: seq=2   time=69.523 ms  SERVFAIL [QR RD RA -- DO] [EDE:10("For brokendnssec.net/soa")]
75  bytes from 8.8.8.8: seq=3   time=58.058 ms  SERVFAIL [QR RD RA -- DO] [EDE:10("For brokendnssec.net/soa")]
75  bytes from 8.8.8.8: seq=4   time=54.235 ms  SERVFAIL [QR RD RA -- DO] [EDE:10("For brokendnssec.net/soa")]
75  bytes from 8.8.8.8: seq=5   time=57.806 ms  SERVFAIL [QR RD RA -- DO] [EDE:10("For brokendnssec.net/soa")]

--- 8.8.8.8 dnsping statistics ---
5 requests transmitted, 5 responses received, 0% lost
min=54.235 ms, avg=22.665 ms, max=69.523 ms, stddev=38.202 ms
```

`dnsping` also provides statistics such as minimum, maximum, and average
response times, along with jitter (standard deviation) and packet loss.

Here are a few interesting use cases for `dnsping`:

- Comparing response times across different transport protocols (e.g., UDP vs. DoH).
- Evaluating the reliability of your DNS server by measuring jitter and packet loss.
- Measuring response times with DNSSEC enabled using the `--dnssec` flag.
- Testing EDNS Client Subnet behavior for geolocation-aware responses:

```shell
./dnsping.py -c 3 --ecs 203.0.113.0/24 -s 94.140.14.14 google.com
```

```
dnsping.py DNS: 94.140.14.14:53, hostname: google.com, proto: UDP, class: IN, type: A, flags: [RD]
66  bytes from 94.140.14.14: seq=1   time=31.407 ms  NOERROR [ECS:203.0.113.0/24]
66  bytes from 94.140.14.14: seq=2   time=29.156 ms  NOERROR [ECS:203.0.113.0/24]
66  bytes from 94.140.14.14: seq=3   time=30.892 ms  NOERROR [ECS:203.0.113.0/24]

--- 94.140.14.14 dnsping statistics ---
3 requests transmitted, 3 responses received, 0% lost
min=29.156 ms, avg=30.485 ms, max=31.407 ms, stddev=1.176 ms
```

- Identifying DNS servers using the NSID option:

```shell
./dnsping.py -c 2 --nsid -s 8.8.8.8 google.com
```

```
dnsping.py DNS: 8.8.8.8:53, hostname: google.com, proto: UDP, class: IN, type: A, flags: [RD]
68  bytes from 8.8.8.8: seq=1   time=36.399 ms  NOERROR [NSID:gpdns-ams]
68  bytes from 8.8.8.8: seq=2   time=32.156 ms  NOERROR [NSID:gpdns-ams]

--- 8.8.8.8 dnsping statistics ---
2 requests transmitted, 2 responses received, 0% lost
min=32.156 ms, avg=34.278 ms, max=36.399 ms, stddev=2.122 ms
```


# dnstraceroute

`dnstraceroute` is a utility that traces the path of your DNS requests to their
destination. You may want to compare this with your actual network traceroute to
ensure that your DNS traffic is not being routed through any unwanted paths.

`dnstraceroute` supports multiple transport protocols:
- UDP (default) - Traditional DNS queries
- TCP (`--tcp`) - DNS over TCP
- DoQ (`--quic`) - DNS over QUIC (supported by AdGuard DNS)
- DoH3 (`--http3`) - DNS over HTTP/3 (supported by Google DNS and Cloudflare)

```shell
./dnstraceroute.py --expert --asn -C -t A -s 8.8.4.4 facebook.com
```

You can also test modern DNS protocols:

```shell
# Test DNS over QUIC with AdGuard DNS
./dnstraceroute.py --quic -s 94.140.14.14 -c 3 google.com

# Test DNS over HTTP/3 with Google DNS
./dnstraceroute.py --http3 -s 8.8.8.8 -c 3 google.com
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

Using the `--expert` flag with `dnstraceroute` will enable the display of expert
hints, including warnings about potential DNS traffic hijacking.

# dnseval
`dnseval` is a bulk ping utility that sends arbitrary DNS queries to a specified
list of DNS servers, allowing you to compare their response times
simultaneously.

You can use `dnseval` to evaluate response times across different transport
protocols, including UDP (default), TCP, DoT (DNS over TLS), and DoH (DNS over
HTTPS) by using the `--tcp`, `--tls`, and `--doh` flags, respectively.

## Protocol Support Summary

| Tool | UDP | TCP | TLS (DoT) | DoH | DoQ | DoH3 |
|------|-----|-----|-----------|-----|-----|------|
| `dnsping` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `dnstraceroute` | ✓ | ✓ | - | - | ✓ | ✓ |
| `dnseval` | ✓ | ✓ | ✓ | ✓ | - | - |

*DoQ: DNS over QUIC, DoH3: DNS over HTTP/3*

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

- github: [github.com/farrokhi](https://github.com/farrokhi/)
- website: [farrokhi.net](https://farrokhi.net/)
- mastodon: [@farrokhi@unix.family](https://unix.family/@farrokhi)
- twitter: [@farrokhi](https://twitter.com/farrokhi)


### License

dnsdiag is released under a 2 clause BSD license.
