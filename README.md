DNS Diagnostics and Performance Measurement Tools
==================================================

Ever been wondering if your ISP is hijacking your DNS traffic? Ever observed any
misbehavior with your DNS responses? Ever been redirected to wrong address and
suspected something is wrong with your DNS? Here we have a set of tools to
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
server for your network. While it is highly recommended to use your own DNS
resolver and never trust any third-party DNS server, but in case you need to
choose the best DNS forwarder for your network, `dnseval` lets you compare
different DNS servers from performance (latency) and reliability (loss) point
of view.

# prerequisites
This script requires python3 as well as latest
[dnspython](http://www.dnspython.org/) and
[cymruwhois](https://pythonhosted.org/cymruwhois/). Please note that
"dnstraceroute" requires a modified version of dnspython module. All required
third-party modules are included as GIT submodules. You just need to run `git
submodule update --init` and project directory to pull the required code.

# dnsping
dnsping pings a DNS resolver by sending an arbitrary DNS query for given number
of times:
```
% ./dnsping.py -c 3 -s 8.8.8.8 -t MX wikipedia.org
dnsping.py DNS: 8.8.8.8:53, hostname: wikipedia.org, rdatatype: MX
101 bytes from 8.8.8.8: seq=0   time=262.896 ms
101 bytes from 8.8.8.8: seq=1   time=305.608 ms
101 bytes from 8.8.8.8: seq=2   time=307.221 ms

--- 8.8.8.8 dnsping statistics ---
3 requests transmitted, 3 responses received,   0% lost
min=262.896 ms, avg=291.908 ms, max=307.221 ms, stddev=25.138 ms
```
This script calculates minimum, maximum and average response time as well as
jitter (stddev)

# dnstraceroute
dnstraceroute is a traceroute utility to figure out the path that your DNS
request is passing through to get to its destination. You may want to compare
it to your actual network traceroute and make sure your DNS traffic is not
routed to any unwanted path.

```
% ./dnstraceroute.py -s 4.2.2.1 yahoo.com
 dnstraceroute.py 4.2.2.1: hostname=yahoo.com rdatatype=A
 1       192.168.199.57 (192.168.199.57)  47 ms
 2       192.168.198.21 (192.168.198.21)  21 ms
 3       192.168.169.169 (192.168.169.169)  27 ms
 4       192.168.168.137 (192.168.168.137)  28 ms
 5       so-5-0-0.franco71.fra.seabone.net (89.221.34.6)  23 ms
 6       xe-5-3-1.fra44.ip4.gtt.net (89.149.129.185)  62 ms
 7       *  1126 ms
 8       ae-1-60.edge5.Frankfurt1.Level3.net (4.69.154.9)  62 ms
 9       ae-1-60.edge5.Frankfurt1.Level3.net (4.69.154.9)  12 ms
 10      a.resolvers.level3.net (4.2.2.1)  171 ms
```

# dnseval
dnseval is a bulk ping utility that sends an arbitrary DNS query to a give list
of DNS servers. This script is meant for comparing response time of multiple
DNS servers at once:
```
% ./dnseval.py wikipedia.org
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

### Credits

- [@rthalley](https://github.com/rthalley) for invaluable [dnspython](https://github.com/rthalley/dnspython) library
- [@JustinAzoff](https://github.com/JustinAzoff) for [python-cymruwhois](https://github.com/JustinAzoff/python-cymruwhois) library
- [@bortzmeyer](https://github.com/bortzmeyer) for his feedback and patches
