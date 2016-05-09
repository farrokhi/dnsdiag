#!/usr/bin/env python3
#
# Copyright (c) 2016, Babak Farrokhi
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import getopt
import ipaddress
import os
import signal
import socket
import sys
import time
from statistics import stdev

import dns.rdatatype
import dns.resolver

__VERSION__ = 1.1
__PROGNAME__ = os.path.basename(sys.argv[0])
shutdown = False


def usage():
    print("""%s version %1.1f
usage: %s [-h] [-q] [-v] [-s server] [-p port] [-P port] [-S address] [-c count] [-t type] [-w wait] hostname
  -h  --help      Show this help
  -q  --quiet     Quiet
  -v  --verbose   Print actual dns response
  -s  --server    DNS server to use (default: first entry from /etc/resolv.conf)
  -p  --port      DNS server port number (default: 53)
  -T  --tcp       Use TCP instead of UDP
  -4  --ipv4      Use IPv4 as default network protocol
  -6  --ipv6      Use IPv6 as default network protocol
  -P  --srcport   Query source port number (default: 0)
  -S  --srcip     Query source IP address (default: default interface address)
  -c  --count     Number of requests to send (default: 10)
  -w  --wait      Maximum wait time for a reply (default: 5)
  -t  --type      DNS request record type (default: A)
""" % (__PROGNAME__, __VERSION__, __PROGNAME__))
    sys.exit(0)


def signal_handler(sig, frame):
    global shutdown
    if shutdown:  # pressed twice, so exit immediately
        sys.exit(0)
    shutdown = True  # pressed once, exit gracefully


def main():
    try:
        signal.signal(signal.SIGTSTP, signal.SIG_IGN)  # ignore CTRL+Z
        signal.signal(signal.SIGINT, signal_handler)  # custom CTRL+C handler
    except AttributeError:  # OS Does not support some signals, probably windows
        pass

    if len(sys.argv) == 1:
        usage()

    # defaults
    dnsrecord = 'A'
    count = 10
    timeout = 5
    quiet = False
    verbose = False
    dnsserver = dns.resolver.get_default_resolver().nameservers[0]
    dst_port = 53
    src_port = 0
    src_ip = None
    use_tcp = False
    af = None
    hostname = 'wikipedia.org'

    try:
        opts, args = getopt.getopt(sys.argv[1:], "qhc:s:t:w:vp:P:S:T46",
                                   ["help", "output=", "count=", "server=", "quiet", "type=", "wait=", "verbose",
                                    "port", "dstport=", "srcip=", "tcp", "ipv4", "ipv6"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err)  # will print something like "option -a not recognized"
        usage()

    if args and len(args) == 1:
        hostname = args[0]
    else:
        usage()

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-c", "--count"):
            count = int(a)
        elif o in ("-v", "--verbose"):
            verbose = True
        elif o in ("-s", "--server"):
            dnsserver = a
        elif o in ("-p", "--port"):
            dst_port = int(a)
        elif o in ("-q", "--quiet"):
            quiet = True
            verbose = False
        elif o in ("-w", "--wait"):
            timeout = int(a)
        elif o in ("-t", "--type"):
            dnsrecord = a
        elif o in ("-T", "--tcp"):
            use_tcp = True
        elif o in ("-4", "--ipv4"):
            af = socket.AF_INET
        elif o in ("-6", "--ipv6"):
            af = socket.AF_INET6
        elif o in ("-P", "--srcport"):
            src_port = int(a)
            if src_port < 1024:
                print("WARNING: Source ports below 1024 are only available to superuser")
        elif o in ("-S", "--srcip"):
            src_ip = a
        else:
            usage()

    # check if we have a valid dns server address
    try:
        ipaddress.ip_address(dnsserver)
    except ValueError:  # so it is not a valid IPv4 or IPv6 address, so try to resolve host name
        try:
            dnsserver = socket.getaddrinfo(dnsserver, port=None, family=af)[1][4][0]
        except OSError:
            print('Error: cannot resolve hostname:', dnsserver)
            sys.exit(1)

    resolver = dns.resolver.Resolver()
    resolver.nameservers = [dnsserver]
    resolver.timeout = timeout
    resolver.lifetime = timeout
    resolver.port = dst_port
    resolver.retry_servfail = 0

    response_time = []
    i = 0

    print("%s DNS: %s:%d, hostname: %s, rdatatype: %s" % (__PROGNAME__, dnsserver, dst_port, hostname, dnsrecord))

    for i in range(count):
        if shutdown:
            break
        try:
            stime = time.time()
            answers = resolver.query(hostname, dnsrecord, source_port=src_port, source=src_ip, tcp=use_tcp, af=af)
            etime = time.time()
        except dns.resolver.NoNameservers as e:
            if not quiet:
                print("No response to dns request")
                if verbose:
                    print("error:", e)
            sys.exit(1)
        except dns.resolver.NXDOMAIN as e:
            if not quiet:
                print("Hostname does not exist")
            if verbose:
                print("Error:", e)
            sys.exit(1)
        except dns.resolver.Timeout:
            if not quiet:
                print("Request timeout")
            pass
        except dns.resolver.NoAnswer:
            if not quiet:
                print("No answer")
            pass
        else:
            elapsed = (etime - stime) * 1000  # convert to milliseconds
            response_time.append(elapsed)
            if not quiet:
                print(
                    "%d bytes from %s: seq=%-3d time=%3.3f ms" % (
                        len(str(answers.rrset)), dnsserver, i, elapsed))
            if verbose:
                print(answers.rrset)

    r_sent = i + 1
    r_received = len(response_time)
    r_lost = r_sent - r_received
    r_lost_percent = (100 * r_lost) / r_sent
    if response_time:
        r_min = min(response_time)
        r_max = max(response_time)
        r_avg = sum(response_time) / r_received
        if len(response_time) > 1:
            r_stddev = stdev(response_time)
        else:
            r_stddev = 0
    else:
        r_min = 0
        r_max = 0
        r_avg = 0
        r_stddev = 0

    print('\n--- %s dnsping statistics ---' % dnsserver)
    print('%d requests transmitted, %d responses received, %3.0f%% lost' % (r_sent, r_received, r_lost_percent))
    print('min=%3.3f ms, avg=%3.3f ms, max=%3.3f ms, stddev=%3.3f ms' % (r_min, r_avg, r_max, r_stddev))


if __name__ == '__main__':
    main()
