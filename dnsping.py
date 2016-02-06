#!/usr/bin/env python3
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
import time
from statistics import stdev
import sys
import signal

import dns.rdatatype
import dns.resolver

__VERSION__ = 1.0
should_stop = False


def usage():
    print('dnsping version %1.1f\n' % __VERSION__)
    print('syntax: dnsping [-h] [-q] [-s server] [-c count] [-t type] [-w wait] hostname')
    print('  -h  --help      show this help')
    print('  -q  --quiet     quiet')
    print('  -v  --verbose   print actual dns response')
    print('  -s  --server    dns server to use (default: 8.8.8.8)')
    print('  -c  --count     number of requests to send (default: 10)')
    print('  -w  --wait      maximum wait time for a reply (default: 5)')
    print('  -t  --type      DNS request record type (default: A)')
    print('  ')
    exit()


def signal_handler(signal, frame):
    global should_stop
    if should_stop:  ## pressed twice, so exit immediately
        exit(0)
    should_stop = True  ## pressed once, exit gracefully


def main():
    signal.signal(signal.SIGTSTP, signal.SIG_IGN)  # ignore CTRL+Z
    signal.signal(signal.SIGINT, signal_handler)  # ignore CTRL+C

    if len(sys.argv) == 1:
        usage()

    dnsrecord = 'A'
    count = 10
    timeout = 5
    quiet = False
    verbose = False
    dnsserver = '8.8.8.8'

    try:
        opts, args = getopt.getopt(sys.argv[1:], "qhc:s:t:w:v",
                                   ["help", "output=", "count=", "server=", "quiet", "type=", "wait=", "verbose"])
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
        elif o in ("-q", "--quiet"):
            quiet = True
            verbose = False
        elif o in ("-w", "--wait"):
            timeout = int(a)
        elif o in ("-t", "--type"):
            dnsrecord = a
        else:
            usage()

    resolver = dns.resolver.Resolver()
    resolver.nameservers = [dnsserver]
    resolver.timeout = timeout
    resolver.lifetime = timeout
    resolver.retry_servfail = 0

    response_time = []

    print("DNSPING %s: hostname=%s rdatatype=%s" % (dnsserver, hostname, dnsrecord))

    for i in range(count):
        if should_stop:
            break
        try:
            stime = time.time()
            answers = resolver.query(hostname, dnsrecord)
            etime = time.time()
        except dns.resolver.NoNameservers:
            if not quiet:
                print("no response to dns request")
            exit(1)
        except dns.resolver.Timeout:
            if not quiet:
                print("request timeout")
            pass
        except dns.resolver.NoAnswer:
            if not quiet:
                print("invalid answer")
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
        r_stddev = stdev(response_time)
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
