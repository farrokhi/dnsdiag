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
server             avg(ms)     min(ms)     max(ms)     stddev(ms)  lost(%)
--------------------------------------------------------------------------
4.2.2.1            151.067     131.270     221.742     28.643      %10
4.2.2.2            142.175     132.921     178.133     13.348      %0
64.6.64.6          133.047     109.145     162.938     20.609      %0
64.6.65.6          377.270     97.669      661.471     172.717     %0
8.8.4.4            389.048     294.581     511.134     67.953      %0
8.8.8.8            0.000       0.000       0.000       0.000       %100
208.67.222.222     179.068     135.975     258.582     50.681      %0
208.67.220.220     137.817     135.822     140.113     1.504       %0
```
# todo
- input sanitization
- new tool: DNS traceroute
 
