#!/usr/bin/env python3
#
# Copyright (c) 2016-2021, Babak Farrokhi
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


import datetime
import getopt
import ipaddress
import os
import requests
import signal
import socket
import sys
import time
from statistics import stdev

import dns.flags
import dns.resolver

from util.dns import PROTO_UDP, PROTO_TCP, PROTO_TLS, PROTO_HTTPS, proto_to_text, unsupported_feature

__author__ = 'Babak Farrokhi (babak@farrokhi.net)'
__license__ = 'BSD'
__version__ = '2.0.2'
__progname__ = os.path.basename(sys.argv[0])
shutdown = False


def usage():
    print("""%s version %s
usage: %s [-46DeFhqTvX] [-i interval] [-s server] [-p port] [-P port] [-S address] [-c count] [-t type] [-w wait] hostname

  -h  --help      Show this help
  -q  --quiet     Quiet
  -v  --verbose   Print actual dns response
  -s  --server    DNS server to use (default: first entry from /etc/resolv.conf)
  -p  --port      DNS server port number (default: 53 for TCP/UDP and 853 for TLS)
  -T  --tcp       Use TCP as transport protocol
  -X  --tls       Use TLS as transport protocol
  -H  --doh       Use HTTPS as transport protols (DoH)
  -4  --ipv4      Use IPv4 as default network protocol
  -6  --ipv6      Use IPv6 as default network protocol
  -P  --srcport   Query source port number (default: 0)
  -S  --srcip     Query source IP address (default: default interface address)
  -c  --count     Number of requests to send (default: 10, 0 for infinity)
  -w  --wait      Maximum wait time for a reply (default: 2 seconds)
  -i  --interval  Time between each request (default: 1 seconds)
  -t  --type      DNS request record type (default: A)
  -e  --edns      Disable EDNS0 (default: Enabled)
  -D  --dnssec    Enable 'DNSSEC desired' flag in requests. Implies EDNS.
  -F  --flags     Display response flags
""" % (__progname__, __version__, __progname__))
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
    rdatatype = 'A'
    count = 10
    timeout = 2
    interval = 1
    quiet = False
    verbose = False
    show_flags = False
    dnsserver = None  # do not try to use system resolver by default
    dst_port = 53  # default for UDP and TCP
    src_port = 0
    src_ip = None
    proto = PROTO_UDP
    use_edns = True
    want_dnssec = False
    af = socket.AF_INET
    qname = 'wikipedia.org'

    try:
        opts, args = getopt.getopt(sys.argv[1:], "qhc:s:t:w:i:vp:P:S:T46eDFXH",
                                   ["help", "count=", "server=", "quiet", "type=", "wait=", "interval=", "verbose",
                                    "port=", "srcip=", "tcp", "ipv4", "ipv6", "srcport=", "edns", "dnssec", "flags",
                                    "tls", "doh"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err, file=sys.stderr)  # will print something like "option -a not recognized"
        usage()

    if args and len(args) == 1:
        qname = args[0]
    else:
        usage()

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-c", "--count"):
            count = abs(int(a))
        elif o in ("-v", "--verbose"):
            verbose = True
        elif o in ("-s", "--server"):
            dnsserver = a
        elif o in ("-q", "--quiet"):
            quiet = True
            verbose = False
        elif o in ("-w", "--wait"):
            timeout = int(a)
        elif o in ("-i", "--interval"):
            interval = int(a)
        elif o in ("-t", "--type"):
            rdatatype = a
        elif o in ("-T", "--tcp"):
            proto = PROTO_TCP
        elif o in ("-X", "--tls"):
            proto = PROTO_TLS
            dst_port = 853  # default for DoT, unless overriden using -p
        elif o in ("-H", "--doh"):
            proto = PROTO_HTTPS
            dst_port = 443  # default for DoH, unless overriden using -p
        elif o in ("-4", "--ipv4"):
            af = socket.AF_INET
        elif o in ("-6", "--ipv6"):
            af = socket.AF_INET6
        elif o in ("-e", "--edns"):
            use_edns = False
        elif o in ("-D", "--dnssec"):
            want_dnssec = True
        elif o in ("-F", "--flags"):
            show_flags = True
        elif o in ("-p", "--port"):
            dst_port = int(a)
        elif o in ("-P", "--srcport"):
            src_port = int(a)
            if src_port < 1024:
                print("WARNING: Source ports below 1024 are only available to superuser", flush=True)
        elif o in ("-S", "--srcip"):
            src_ip = a
        else:
            usage()

    # Use system DNS server if parameter is not specified
    # remember not all systems have /etc/resolv.conf (i.e. Android)
    if dnsserver is None:
        dnsserver = dns.resolver.get_default_resolver().nameservers[0]

    # check if we have a valid dns server address
    try:
        ipaddress.ip_address(dnsserver)
    except ValueError:  # so it is not a valid IPv4 or IPv6 address, so try to resolve host name
        try:
            dnsserver = socket.getaddrinfo(dnsserver, port=None, family=af)[1][4][0]
        except OSError:
            print('Error: cannot resolve hostname:', dnsserver, file=sys.stderr, flush=True)
            sys.exit(1)

    if use_edns:
        query = dns.message.make_query(qname, rdatatype, dns.rdataclass.IN,
                                       use_edns=True, want_dnssec=want_dnssec,
                                       ednsflags=dns.flags.edns_from_text('DO'), payload=8192)
    else:
        query = dns.message.make_query(qname, rdatatype, dns.rdataclass.IN,
                                       use_edns=False, want_dnssec=want_dnssec)

    response_time = []
    i = 0

    print("%s DNS: %s:%d, hostname: %s, proto: %s, rdatatype: %s, flags: %s" %
          (__progname__, dnsserver, dst_port, qname, proto_to_text(proto), rdatatype,
           dns.flags.to_text(query.flags)), flush=True)

    while not shutdown:

        if 0 < count <= i:
            break
        else:
            i += 1

        try:
            stime = time.perf_counter()
            if proto is PROTO_UDP:
                answers = dns.query.udp(query, dnsserver, timeout=timeout, port=dst_port,
                                        source=src_ip, source_port=src_port, ignore_unexpected=True)
            elif proto is PROTO_TCP:
                answers = dns.query.tcp(query, dnsserver, timeout=timeout, port=dst_port,
                                        source=src_ip, source_port=src_port)
            elif proto is PROTO_TLS:
                if hasattr(dns.query, 'tls'):
                    answers = dns.query.tls(query, dnsserver, timeout, dst_port,
                                            src_ip, src_port)
                else:
                    unsupported_feature()

            elif proto is PROTO_HTTPS:
                if hasattr(dns.query, 'https'):
                    answers = dns.query.https(query, dnsserver, timeout, dst_port,
                                              src_ip, src_port)
                else:
                    unsupported_feature()

            etime = time.perf_counter()
        except dns.resolver.NoNameservers as e:
            if not quiet:
                print("No response to DNS request", file=sys.stderr, flush=True)
                if verbose:
                    print("error:", e, file=sys.stderr, flush=True)
            sys.exit(1)
        except (requests.exceptions.ConnectTimeout, dns.exception.Timeout):
            if not quiet:
                print("Request timeout", flush=True)
        except requests.exceptions.ReadTimeout:
            if not quiet:
                print("Read timeout", flush=True)
        except ValueError:
            if not quiet:
                print("Invalid Response", flush=True)
                continue
        else:
            # convert time to milliseconds, considering that
            # time property is retruned differently by query.https
            if type(answers.time) is datetime.timedelta:
                elapsed = answers.time.total_seconds() * 1000
            else:
                elapsed = answers.time * 1000
            response_time.append(elapsed)
            if not quiet:
                if show_flags:
                    flags = " [%s]  %s" % (dns.flags.to_text(answers.flags), dns.rcode.to_text(answers.rcode()))
                else:
                    flags = ""
                print("%d bytes from %s: seq=%-3d time=%.3f ms%s" % (
                    len(answers.to_wire()), dnsserver, i, elapsed, flags), flush=True)
            if verbose:
                print(answers.to_text(), flush=True)

            time_to_next = (stime + interval) - etime
            if time_to_next > 0:
                time.sleep(time_to_next)

    r_sent = i
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

    print('\n--- %s dnsping statistics ---' % dnsserver, flush=True)
    print('%d requests transmitted, %d responses received, %.0f%% lost' % (r_sent, r_received, r_lost_percent),
          flush=True)
    print('min=%.3f ms, avg=%.3f ms, max=%.3f ms, stddev=%.3f ms' % (r_min, r_avg, r_max, r_stddev), flush=True)


if __name__ == '__main__':
    main()
