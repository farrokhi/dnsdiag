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
import signal
import sys
import time
from statistics import stdev

import dns.rdatatype
import dns.resolver

__VERSION__ = 1.0
should_stop = False

resolvers = [
    '4.2.2.1',
    '4.2.2.2',
    '64.6.64.6',
    '64.6.65.6',
    '8.8.4.4',
    '8.8.8.8',
    '208.67.222.222',
    '208.67.220.220'
]


def usage():
    print('dnsperf version %1.1f\n' % __VERSION__)
    print('syntax: dnsping [-h] [-f server-list] [-c count] [-t type] [-w wait] hostname')
    print('  -h  --help      show this help')
    print('  -f  --file      dns server list to use')
    print('  -c  --count     number of requests to send (default: 10)')
    print('  -w  --wait      maximum wait time for a reply (default: 5)')
    print('  -t  --type      DNS request record type (default: A)')
    exit()


def signal_handler(sig, frame):
    global should_stop
    if should_stop:  # pressed twice, so exit immediately
        exit(0)
    should_stop = True  # pressed once, exit gracefully


def dnsping(host, server, dnsrecord, timeout, count):
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [server]
    resolver.timeout = timeout
    resolver.lifetime = timeout
    resolver.retry_servfail = 0

    response_time = []
    i = 0

    # print('DEBUG: host = %s , server = %s , count = %d' % (host, resolver.nameservers[0], count))

    for i in range(count):
        if should_stop:
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
        r_stddev = stdev(response_time)
    else:
        r_min = 0
        r_max = 0
        r_avg = 0
        r_stddev = 0

    print("%-15s    %-8.3f    %-8.3f    %-8.3f    %-8.3f    %%%d" % (
        server, r_avg, r_min, r_max, r_stddev, r_lost_percent))


def main():
    signal.signal(signal.SIGTSTP, signal.SIG_IGN)  # ignore CTRL+Z
    signal.signal(signal.SIGINT, signal_handler)  # ignore CTRL+C

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
            f = open(inputfilename, 'rt')
        else:
            f = resolvers
        print('server             avg(ms)     min(ms)     max(ms)     stddev(ms)  lost(%)')
        print('--------------------------------------------------------------------------')
        for server in f:
            s = server.strip()
            if not s:
                continue
            dnsping(hostname, s, dnsrecord, waittime, count)
        if fromfile:
            f.close()
    except Exception as e:
        print('error: %s' % e)
        exit(1)


if __name__ == '__main__':
    main()
