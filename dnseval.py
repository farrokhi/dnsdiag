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


import os

import getopt
import ipaddress
import signal
import socket
import sys
import time
from statistics import stdev

import dns.rdatatype
import dns.resolver

__author__ = 'Babak Farrokhi (babak@farrokhi.net)'
__license__ = 'BSD'
__version__ = "1.6.3"
__progname__ = os.path.basename(sys.argv[0])
shutdown = False

resolvers = dns.resolver.get_default_resolver().nameservers


class Colors(object):
    N = '\033[m'  # native
    R = '\033[31m'  # red
    G = '\033[32m'  # green
    O = '\033[33m'  # orange
    B = '\033[34m'  # blue

    def __init__(self, mode):
        if not mode:
            self.N = ''
            self.R = ''
            self.G = ''
            self.O = ''
            self.B = ''


def usage():
    print("""%s version %s

usage: %s [-h] [-f server-list] [-c count] [-t type] [-w wait] hostname
  -h  --help      show this help
  -f  --file      dns server list to use (default: system resolvers)
  -c  --count     number of requests to send (default: 10)
  -w  --wait      maximum wait time for a reply (default: 2)
  -t  --type      DNS request record type (default: A)
  -T  --tcp       Use TCP instead of UDP
  -e  --edns      Disable EDNS0 (Default: Enabled)
  -C  --color     Print colorful output
  -v  --verbose   Print actual dns response
""" % (__progname__, __version__, __progname__))
    sys.exit()


def signal_handler(sig, frame):
    global shutdown
    if shutdown:  # pressed twice, so exit immediately
        sys.exit(0)
    shutdown = True  # pressed once, exit gracefully


def maxlen(names):
    sn = sorted(names, key=len)
    return len(sn[-1])


def _order_flags(table):
    return sorted(table.items(), reverse=True)


def flags_to_text(flags):
    # Standard DNS flags

    QR = 0x8000
    AA = 0x0400
    TC = 0x0200
    RD = 0x0100
    RA = 0x0080
    AD = 0x0020
    CD = 0x0010

    # EDNS flags

    DO = 0x8000

    _by_text = {
        'QR': QR,
        'AA': AA,
        'TC': TC,
        'RD': RD,
        'RA': RA,
        'AD': AD,
        'CD': CD
    }

    _by_value = dict([(y, x) for x, y in _by_text.items()])
    _flags_order = _order_flags(_by_value)

    _by_value = dict([(y, x) for x, y in _by_text.items()])

    order = sorted(_by_value.items(), reverse=True)
    text_flags = []
    for k, v in order:
        if flags & k != 0:
            text_flags.append(v)
        else:
            text_flags.append('--')

    return ' '.join(text_flags)


def dnsping(host, server, dnsrecord, timeout, count, use_tcp=False, use_edns=False):
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [server]
    resolver.timeout = timeout
    resolver.lifetime = timeout
    resolver.retry_servfail = 0
    flags = 0
    ttl = None
    answers = None
    if use_edns:
        resolver.use_edns(edns=0, payload=8192, ednsflags=dns.flags.edns_from_text('DO'))

    response_times = []
    i = 0

    for i in range(count):
        if shutdown:  # user pressed CTRL+C
            break
        try:
            stime = time.perf_counter()
            answers = resolver.query(host, dnsrecord, tcp=use_tcp,
                                     raise_on_no_answer=False)  # todo: response validation in future
            etime = time.perf_counter()
        except (dns.resolver.NoNameservers, dns.resolver.NoAnswer):
            break
        except dns.resolver.Timeout:
            pass
        else:
            elapsed = (etime - stime) * 1000  # convert to milliseconds
            response_times.append(elapsed)

    r_sent = i + 1
    r_received = len(response_times)
    r_lost = r_sent - r_received
    r_lost_percent = (100 * r_lost) / r_sent
    if response_times:
        r_min = min(response_times)
        r_max = max(response_times)
        r_avg = sum(response_times) / r_received
        if len(response_times) > 1:
            r_stddev = stdev(response_times)
        else:
            r_stddev = 0
    else:
        r_min = 0
        r_max = 0
        r_avg = 0
        r_stddev = 0

    if answers is not None:
        flags = answers.response.flags
        if len(answers.response.answer) > 0:
            ttl = answers.response.answer[0].ttl

    return server, r_avg, r_min, r_max, r_stddev, r_lost_percent, flags, ttl, answers


def main():
    try:
        signal.signal(signal.SIGTSTP, signal.SIG_IGN)  # ignore CTRL+Z
        signal.signal(signal.SIGINT, signal_handler)  # catch CTRL+C
    except AttributeError:  # Some systems (e.g. Windows) may not support all signals
        pass

    if len(sys.argv) == 1:
        usage()

    # defaults
    dnsrecord = 'A'
    count = 10
    waittime = 2
    inputfilename = None
    fromfile = False
    use_tcp = False
    use_edns = True
    verbose = False
    color_mode = False
    hostname = 'wikipedia.org'

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:c:t:w:TevC",
                                   ["help", "file=", "count=", "type=", "wait=", "tcp", "edns", "verbose", "color"])
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
        elif o in ("-T", "--tcp"):
            use_tcp = True
        elif o in ("-e", "--edns"):
            use_edns = False
        elif o in ("-C", "--color"):
            color_mode = True
        elif o in ("-v", "--verbose"):
            verbose = True
        else:
            print("Invalid option: %s" % o)
            usage()

    color = Colors(color_mode)

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
        print('server ', blanks, ' avg(ms)     min(ms)     max(ms)     stddev(ms)  lost(%)  ttl        flags')
        print((93 + width) * '-')
        for server in f:
            # check if we have a valid dns server address
            if server.lstrip() == '':  # deal with empty lines
                continue
            server = server.replace(' ', '')
            try:
                ipaddress.ip_address(server)
            except ValueError:  # so it is not a valid IPv4 or IPv6 address, so try to resolve host name
                try:
                    s = socket.getaddrinfo(server, port=None)[1][4][0]
                except OSError:
                    print('Error: cannot resolve hostname:', server)
                    s = None
                except:
                    pass
            else:
                s = server

            if not s:
                continue

            try:
                (s, r_avg, r_min, r_max, r_stddev, r_lost_percent, flags, ttl, answers) = dnsping(hostname, s,
                                                                                                  dnsrecord,
                                                                                                  waittime,
                                                                                                  count,
                                                                                                  use_tcp=use_tcp,
                                                                                                  use_edns=use_edns)
            except dns.resolver.NXDOMAIN:
                print('%-15s  NXDOMAIN' % server)
                continue
            except Exception as e:
                print('%s: %s' % (server, e))
                continue

            s = server.ljust(width + 1)
            text_flags = flags_to_text(flags)

            s_ttl = str(ttl)
            if s_ttl == "None":
                s_ttl = "N/A"

            if r_lost_percent > 0:
                l_color = color.O
            else:
                l_color = color.N
            print("%s    %-8.3f    %-8.3f    %-8.3f    %-8.3f    %s%%%-3d%s     %-8s  %21s" % (
                s, r_avg, r_min, r_max, r_stddev, l_color, r_lost_percent, color.N, s_ttl, text_flags), flush=True)
            if verbose and hasattr(answers, 'response'):
                ans_index = 1
                for answer in answers.response.answer:
                    print("Answer %d [ %s%s%s ]" % (ans_index, color.G, answer, color.N))
                    ans_index += 1
                print("")

    except Exception as e:
        print('%s: %s' % (server, e))
        sys.exit(1)


if __name__ == '__main__':
    main()
