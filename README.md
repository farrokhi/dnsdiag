# dnstools
DNS Diagnostics and Performance Measurement Tools

# prerequisites
This script requires python3 as well as latest [dnspython](http://www.dnspython.org/)

# dnsping
dnsping pings a DNS resolver by sending an arbitrary DNS query for given number of times:
```
% ./dnsping.py -c 3 -s 8.8.8.8 -t MX wikipedia.org

DNSPING 8.8.8.8: hostname=wikipedia.org rdatatype=MX
101 bytes from 8.8.8.8: seq=0   time=161.607 ms
101 bytes from 8.8.8.8: seq=1   time=156.355 ms
101 bytes from 8.8.8.8: seq=2   time=145.201 ms

--- 8.8.8.8 dnsping statistics ---
3 requests transmitted, 3 responses received,   0% lost
min=145.201 ms, avg=154.388 ms, max=161.607 ms, stddev=8.378 ms
```
This script calculates minimum, maximum and average response time as well as jitter

# dnsperf
dnsperf is a bulk ping utility that sends an arbitrary DNS query to a give list of DNS servers. This script is meant for comparing response time of multiple DNS servers at once:
```
% ./dnsperf.py wikipedia.org
server             avg(ms)     min(ms)     max(ms)     stddev(ms) lost(%)
-------------------------------------------------------------------------
4.2.2.1            152.938     142.640     166.988     8.546       %10
4.2.2.2            147.496     136.643     160.676     8.903       %30
64.6.64.6          146.446     112.044     162.620     17.441      %0
8.8.4.4            307.992     303.591     315.377     3.418       %0
8.8.8.8            150.635     110.882     172.863     20.908      %0

```
# todo
- input sanitization
 
