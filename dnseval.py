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

__VERSION__ = 1.0
__PROGNAME__ = os.path.basename(sys.argv[0])
shutdown = False

resolvers = dns.resolver.get_default_resolver().nameservers


def usage():
    print("""%s version %1.1f

usage: %s [-h] [-f server-list] [-c count] [-t type] [-w wait] hostname
  -h  --help      show this help
  -f  --file      dns server list to use (default: system resolvers)
  -c  --count     number of requests to send (default: 10)
  -w  --wait      maximum wait time for a reply (default: 5)
  -t  --type      DNS request record type (default: A)
""" % (__PROGNAME__, __VERSION__, __PROGNAME__))
    sys.exit()


def signal_handler(sig, frame):
    global shutdown
    if shutdown:  # pressed twice, so exit immediately
        sys.exit(0)
    shutdown = True  # pressed once, exit gracefully


def maxlen(names):
    sn = sorted(names, key=len)
    return len(sn[-1])


def dnsping(host, server, dnsrecord, timeout, count):
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [server]
    resolver.timeout = timeout
    resolver.lifetime = timeout
    resolver.retry_servfail = 0

    response_time = []
    i = 0

    for i in range(count):
        if shutdown:
            break
        try:
            stime = time.time()
            answers = resolver.query(host, dnsrecord)  # todo: response validation in future
            etime = time.time()
        except (dns.resolver.NoNameservers, dns.resolver.NoAnswer):
            break
        except dns.resolver.Timeout:
            pass
        else:
            elapsed = (etime - stime) * 1000  # convert to milliseconds
            response_time.append(elapsed)

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

    return (server, r_avg, r_min, r_max, r_stddev, r_lost_percent)


def main():
    try:
        signal.signal(signal.SIGTSTP, signal.SIG_IGN)  # ignore CTRL+Z
        signal.signal(signal.SIGINT, signal_handler)  # ignore CTRL+C
    except AttributeError:  # Some systems may not support all signals
        pass

    if len(sys.argv) == 1:
        usage()

    dnsrecord = 'A'
    count = 10
    waittime = 5
    inputfilename = None
    fromfile = False
    hostname = 'wikipedia.org'

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:c:t:w:",
                                   ["help", "file=", "count=", "type=", "wait="])
    except getopt.GetoptError as err:
        print(err)
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
        elif o in ("-f", "--file"):
            inputfilename = a
            fromfile = True
        elif o in ("-w", "--wait"):
            waittime = int(a)
        elif o in ("-t", "--type"):
            dnsrecord = a
        else:
            print("Invalid option: %s" % o)
            usage()

    try:
        if fromfile:
            with open(inputfilename, 'rt') as flist:
                f = flist.read().splitlines()
        else:
            f = resolvers
        if len(f) == 0:
            print("No nameserver specified")

        f = [name.strip() for name in f]
        width = maxlen(f)
        blanks = (width - 5) * ' '
        print('server ', blanks, ' avg(ms)     min(ms)     max(ms)     stddev(ms)  lost(%)')
        print((60 + width) * '-')
        for server in f:
            # check if we have a valid dns server address
            try:
                ipaddress.ip_address(server)
            except ValueError:  # so it is not a valid IPv4 or IPv6 address, so try to resolve host name
                try:
                    s = socket.getaddrinfo(server, port=None)[1][4][0]
                except OSError:
                    print('Error: cannot resolve hostname:', server)
                    s = None
            else:
                s = server

            if not s:
                continue
            (s, r_avg, r_min, r_max, r_stddev, r_lost_percent) = dnsping(hostname, s, dnsrecord, waittime,
                                                                         count)

            s = server.ljust(width + 1)
            print("%s    %-8.3f    %-8.3f    %-8.3f    %-8.3f    %%%d" % (
                s, r_avg, r_min, r_max, r_stddev, r_lost_percent), flush=True)

    except Exception as e:
        print('error: %s' % e)
        sys.exit(1)


if __name__ == '__main__':
    main()
