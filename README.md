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

[uv](https://docs.astral.sh/uv/) is a fast Python package manager that can run tools directly without installation:

```bash
# Run dnsping directly without installation
uvx --from dnsdiag dnsping google.com

# Run with specific options
uvx --from dnsdiag dnsping -c 5 --tls -s 8.8.8.8 example.com

# Run dnstraceroute
uvx --from dnsdiag dnstraceroute cloudflare.com

# Run dnseval
uvx --from dnsdiag dnseval -f public-servers.txt github.com
```

To install dnsdiag persistently:

```bash
# Install dnsdiag tools
uv tool install dnsdiag

# Upgrade to the latest version
uv tool upgrade dnsdiag
```

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
- Extended DNS Error messages ([RFC 8914](https://www.rfc-editor.org/rfc/rfc8914)) are automatically displayed when present.
- Use `--nsid` to display the Name Server Identifier (NSID) if available ([RFC 5001](https://www.rfc-editor.org/rfc/rfc5001)).
- Use `--ecs` to include EDNS Client Subnet information for geographic routing optimization.
- Use `--cookie` to display DNS cookies ([RFC 7873](https://www.rfc-editor.org/rfc/rfc7873)) when present in responses.

```shell
./dnsping.py -c 5 --dnssec --flags --tls -t AAAA -s 8.8.8.8 brokendnssec.net
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
66  bytes from 94.140.14.14: seq=1   time=31.407 ms  NOERROR [ECS:203.0.113.0/24/24]
66  bytes from 94.140.14.14: seq=2   time=29.156 ms  NOERROR [ECS:203.0.113.0/24/24]
66  bytes from 94.140.14.14: seq=3   time=30.892 ms  NOERROR [ECS:203.0.113.0/24/24]

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

- Testing DNS cookies for enhanced security and cache optimization:

```shell
./dnsping.py -c 2 --cookie -s anyns.pch.net quad9.net
```

```
dnsping.py DNS: anyns.pch.net:53, hostname: quad9.net, proto: UDP, class: IN, type: A, flags: [RD]
82  bytes from anyns.pch.net: seq=1   time=30.552  ms  NOERROR [COOKIE:27f609c017bb2ec4ea70de5c68eec3fc39f6a53ee49c55f8]
82  bytes from anyns.pch.net: seq=2   time=24.794  ms  NOERROR [COOKIE:719631dd9fcce722d3ac859b68eec3fd2e5430b5c8a7f8cf]

--- anyns.pch.net dnsping statistics ---
2 requests transmitted, 2 responses received, 0% lost
min=24.794 ms, avg=27.673 ms, max=30.552 ms, stddev=4.072 ms
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
protocols, including UDP (default), TCP, DoT (DNS over TLS), DoH (DNS over
HTTPS), DoQ (DNS over QUIC), and DoH3 (DNS over HTTP/3) by using the `--tcp`,
`--tls`, `--doh`, `--quic`, and `--http3` flags, respectively.

## Protocol Support Summary

| Tool | UDP | TCP | TLS (DoT) | DoH | DoQ | DoH3 |
|------|-----|-----|-----------|-----|-----|------|
| `dnsping` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `dnstraceroute` | ✓ | ✓ | - | - | ✓ | ✓ |
| `dnseval` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

*DoQ: DNS over QUIC, DoH3: DNS over HTTP/3*

```shell
./dnseval.py --skip-warmup --dnssec -c10 -f public-servers.txt ripe.net
```

```
server                   avg(ms)  min(ms)  max(ms)  stddev(ms)  lost(%)  ttl      flags                      response
---------------------------------------------------------------------------------------------------------------------
1.0.0.1                  29.01    14.15    45.36    8.60        %0       300      QR -- -- RD RA AD -- DO     NOERROR
1.1.1.1                  23.90    18.14    42.07    7.83        %0       300      QR -- -- RD RA AD -- DO     NOERROR
1.0.0.2                  25.90    21.36    31.58    4.26        %0       300      QR -- -- RD RA AD -- DO     NOERROR
1.1.1.2                  22.68    18.36    32.15    3.96        %0       300      QR -- -- RD RA AD -- DO     NOERROR
1.0.0.3                  22.53    18.98    32.52    3.94        %0       300      QR -- -- RD RA AD -- DO     NOERROR
1.1.1.3                  21.70    20.25    22.97    0.77        %0       299      QR -- -- RD RA AD -- DO     NOERROR
2606:4700:4700::1001     21.70    19.13    27.50    2.28        %0       299      QR -- -- RD RA AD -- DO     NOERROR
2606:4700:4700::1111     22.63    20.42    30.18    3.13        %0       299      QR -- -- RD RA AD -- DO     NOERROR
2606:4700:4700::1002     24.97    20.89    44.63    7.16        %0       299      QR -- -- RD RA AD -- DO     NOERROR
2606:4700:4700::1112     23.24    21.37    25.87    1.48        %0       298      QR -- -- RD RA AD -- DO     NOERROR
2606:4700:4700::1003     21.68    19.28    24.88    1.65        %0       298      QR -- -- RD RA AD -- DO     NOERROR
2606:4700:4700::1113     22.61    19.86    26.09    1.73        %0       299      QR -- -- RD RA AD -- DO     NOERROR
195.46.39.39             25.56    16.42    55.37    15.37       %0       300      QR -- -- RD RA -- -- --     NOERROR
195.46.39.40             19.08    16.51    23.86    2.24        %0       300      QR -- -- RD RA -- -- --     NOERROR
2a05:d014:939:3300::39   0.00     0.00     0.00     0.00        %100     N/A      -- -- -- -- -- -- -- --     No Response
2a05:d014:939:3300::40   0.00     0.00     0.00     0.00        %100     N/A      -- -- -- -- -- -- -- --     No Response
208.67.220.220           30.60    14.54    120.64   31.88       %0       300      QR -- -- RD RA AD -- DO     NOERROR
208.67.222.222           21.78    17.42    36.45    6.06        %0       50       QR -- -- RD RA AD -- DO     NOERROR
2620:0:ccc::2            29.48    19.23    98.29    24.22       %0       299      QR -- -- RD RA AD -- DO     NOERROR
2620:0:ccd::2            22.36    17.90    30.18    3.98        %0       299      QR -- -- RD RA AD -- DO     NOERROR
216.146.35.35            172.53   114.46   360.87   71.47       %0       299      QR -- -- RD RA AD -- DO     NOERROR
216.146.36.36            187.36   118.21   324.32   59.08       %0       110      QR -- -- RD RA AD -- DO     NOERROR
209.244.0.3              46.49    25.23    115.86   28.19       %0       300      QR -- -- RD RA -- -- DO     NOERROR
209.244.0.4              58.33    28.09    109.18   29.20       %0       299      QR -- -- RD RA -- -- DO     NOERROR
4.2.2.1                  64.58    30.21    86.79    30.19       %25      299      QR -- -- RD RA -- -- DO     NOERROR
4.2.2.2                  40.54    22.69    74.80    20.76       %0       70       QR -- -- RD RA -- -- DO     NOERROR
4.2.2.3                  90.62    90.62    90.62    0.00        %50      70       QR -- -- RD RA -- -- DO     NOERROR
4.2.2.4                  31.53    23.80    70.93    14.51       %0       294      QR -- -- RD RA -- -- DO     NOERROR
4.2.2.5                  24.11    24.05    24.18    0.09        %33      294      QR -- -- RD RA -- -- DO     NOERROR
80.80.80.80              0.00     0.00     0.00     0.00        %100     N/A      -- -- -- -- -- -- -- --     No Response
80.80.81.81              0.00     0.00     0.00     0.00        %100     N/A      -- -- -- -- -- -- -- --     No Response
8.8.4.4                  28.35    20.85    39.14    7.24        %0       300      QR -- -- RD RA AD -- DO     NOERROR
8.8.8.8                  21.22    16.22    24.93    2.39        %0       299      QR -- -- RD RA AD -- DO     NOERROR
```

You can also save results in JSONL format for further processing. Each line in the output file is a valid JSON object containing the full measurement results for one DNS server.

```shell
./dnseval.py -c 5 -j results.jsonl -f public-servers.txt example.com
```

The output can be parsed line by line with standard JSON tools like `jq`.

```shell
cat results.jsonl | jq -r 'select(.data.r_lost_percent == 0) | .data.resolver'
```

### Author

Babak Farrokhi 

- github: [github.com/farrokhi](https://github.com/farrokhi/)
- website: [farrokhi.net](https://farrokhi.net/)
- mastodon: [@farrokhi@unix.family](https://unix.family/@farrokhi)
- twitter: [@farrokhi](https://twitter.com/farrokhi)


### License

dnsdiag is released under a 2 clause BSD license.
