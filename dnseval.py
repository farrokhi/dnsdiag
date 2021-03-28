#!/usr/bin/env python3
#
# Copyright (c) 2020, Babak Farrokhi
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
import json
import os
import random
import signal
import socket
import string
import sys
from statistics import stdev

import dns.rcode
import dns.rdatatype
import dns.resolver
import requests.exceptions

__author__ = 'Babak Farrokhi (babak@farrokhi.net)'
__license__ = 'BSD'
__version__ = "1.7.0"
__progname__ = os.path.basename(sys.argv[0])
shutdown = False

# Transport protocols
PROTO_UDP = 0
PROTO_TCP = 1
PROTO_TLS = 2
PROTO_HTTPS = 3


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
  -h  --help        Show this help
  -f  --file        DNS server list to use (default: system resolvers)
  -c  --count       Number of requests to send (default: 10)
  -m  --cache-miss  Force cache miss measurement by prepending a random hostname
  -w  --wait        Maximum wait time for a reply (default: 2)
  -t  --type        DNS request record type (default: A)
  -T  --tcp         Use TCP instead of UDP
  -p  --port        DNS server port number (default: 53 for TCP/UDP and 853 for TLS)
  -S  --srcip       Query source IP address
  -e  --edns        Disable EDNS0 (default: Enabled)
  -C  --color       Print colorful output
  -v  --verbose     Print actual dns response
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
    # DO = 0x8000

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


def random_string(min_length=5, max_length=10):
    char_set = string.ascii_letters + string.digits
    length = random.randint(min_length, max_length)
    return ''.join(map(lambda unused: random.choice(char_set), range(length)))


def dnsping(qname, server, dst_port, rdtype, timeout, count, proto, src_ip, use_edns=False, force_miss=False,
            want_dnssec=False):
    flags = 0
    ttl = None
    response = None
    rcode_text = "No Response"

    response_times = []
    i = 0

    for i in range(count):
        if shutdown:  # user pressed CTRL+C
            break
        try:
            if force_miss:
                fqdn = "_dnsdiag_%s_.%s" % (random_string(), qname)
            else:
                fqdn = qname

            if use_edns:
                query = dns.message.make_query(fqdn, rdtype, dns.rdataclass.IN, use_edns, want_dnssec,
                                               ednsflags=dns.flags.edns_from_text('DO'), payload=8192)
            else:
                query = dns.message.make_query(fqdn, rdtype, dns.rdataclass.IN, use_edns, want_dnssec)

            if proto is PROTO_UDP:
                response = dns.query.udp(query, server, timeout, dst_port, src_ip, ignore_unexpected=True)
            elif proto is PROTO_TCP:
                response = dns.query.tcp(query, server, timeout, dst_port, src_ip)
            elif proto is PROTO_TLS:
                response = dns.query.tls(query, server, timeout, dst_port, src_ip)
            elif proto is PROTO_HTTPS:
                response = dns.query.https(query, server, timeout, dst_port, src_ip)

        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
            raise ConnectionError('Connection failed')
        except ValueError as e:
            rcode_text = "Invalid Response"
            break
        else:
            # convert time to milliseconds, considering that
            # time property is retruned differently by query.https
            if type(response.time) is datetime.timedelta:
                elapsed = response.time.total_seconds() * 1000
            else:
                elapsed = response.time * 1000
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

    if response is not None:
        flags = response.flags
        rcode_text = dns.rcode.to_text(response.rcode())
        if len(response.answer) > 0:
            ttl = response.answer[0].ttl

    return server, r_avg, r_min, r_max, r_stddev, r_lost_percent, flags, ttl, response, rcode_text


def main():
    try:
        signal.signal(signal.SIGTSTP, signal.SIG_IGN)  # ignore CTRL+Z
        signal.signal(signal.SIGINT, signal_handler)  # catch CTRL+C
    except AttributeError:  # Some systems (e.g. Windows) may not support all signals
        pass

    if len(sys.argv) == 1:
        usage()

    # defaults
    rdatatype = 'A'
    proto = PROTO_UDP
    src_ip = None
    dst_port = 53  # default for UDP and TCP
    count = 10
    waittime = 2
    inputfilename = None
    fromfile = False
    save_json = False
    use_edns = True
    force_miss = False
    verbose = False
    color_mode = False
    qname = 'wikipedia.org'

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:c:t:w:S:TevCmXH",
                                   ["help", "file=", "count=", "type=", "wait=", "json", "tcp", "edns", "verbose",
                                    "color", "force-miss", "srcip=", "tls", "doh"])
    except getopt.GetoptError as err:
        print(err)
        usage()

    if args and len(args) == 1:
        qname = args[0]
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
        elif o in ("-m", "--cache-miss"):
            force_miss = True
        elif o in ("-t", "--type"):
            rdatatype = a
        elif o in ("-T", "--tcp"):
            proto = PROTO_TCP
        elif o in ("-S", "--srcip"):
            src_ip = a
        elif o in ("-j", "--json"):
            save_json = True
        elif o in ("-e", "--edns"):
            use_edns = False
        elif o in ("-C", "--color"):
            color_mode = True
        elif o in ("-v", "--verbose"):
            verbose = True
        elif o in ("-X", "--tls"):
            proto = PROTO_TLS
            dst_port = 853  # default for DoT, unless overriden using -p
        elif o in ("-H", "--doh"):
            proto = PROTO_HTTPS
            dst_port = 443  # default for DoH, unless overriden using -p
        elif o in ("-p", "--port"):
            dst_port = int(a)

        else:
            print("Invalid option: %s" % o)
            usage()

    color = Colors(color_mode)

    try:
        if fromfile:
            if inputfilename == '-':
                # read from stdin
                with sys.stdin as flist:
                    f = flist.read().splitlines()
            else:
                try:
                    with open(inputfilename, 'rt') as flist:
                        f = flist.read().splitlines()
                except Exception as e:
                    print(e)
                    sys.exit(1)
        else:
            f = dns.resolver.get_default_resolver().nameservers

        if len(f) == 0:
            print("No nameserver specified")

        f = [name.strip() for name in f]  # remove annoying blanks
        f = [x for x in f if not x.startswith('#') and len(x)]  # remove comments and empty entries

        width = maxlen(f)
        blanks = (width - 5) * ' '
        print('server ', blanks,
              ' avg(ms)     min(ms)     max(ms)     stddev(ms)  lost(%)  ttl        flags                  response')
        print((104 + width) * '-')
        for server in f:
            # check if we have a valid dns server address
            if server.lstrip() == '':  # deal with empty lines
                continue
            server = server.replace(' ', '')
            try:
                ipaddress.ip_address(server)
            except ValueError:  # so it is not a valid IPv4 or IPv6 address, so try to resolve host name
                try:
                    resolver = socket.getaddrinfo(server, port=None)[1][4][0]
                except OSError:
                    print('Error: cannot resolve hostname:', server)
                    resolver = None
                except Exception:
                    pass
            else:
                resolver = server

            if not resolver:
                continue

            try:
                (resolver, r_avg, r_min, r_max, r_stddev, r_lost_percent, flags, ttl, response, rcode_text) = dnsping(
                    qname,
                    resolver,
                    dst_port,
                    rdatatype,
                    waittime,
                    count,
                    proto,
                    src_ip,
                    use_edns=use_edns,
                    force_miss=force_miss,
                    want_dnssec=False
                )

            except Exception as e:
                print('%s: %s' % (server, e))
                continue

            resolver = server.ljust(width + 1)
            text_flags = flags_to_text(flags)

            s_ttl = str(ttl)
            if s_ttl == "None":
                s_ttl = "N/A"

            if r_lost_percent > 0:
                l_color = color.O
            else:
                l_color = color.N
            print("%s    %-8.3f    %-8.3f    %-8.3f    %-8.3f    %s%%%-3d%s     %-8s  %21s   %-20s" % (
                resolver, r_avg, r_min, r_max, r_stddev, l_color, r_lost_percent, color.N, s_ttl, text_flags,
                rcode_text), flush=True)

            if save_json:
                dns_data = {
                    'hostname': qname,
                    'timestamp': str(datetime.datetime.now()),
                    'r_min': r_min,
                    'r_avg': r_avg,
                    'resolver': resolver,
                    'r_max': r_max,
                    'r_lost_percent': r_lost_percent,
                    's_ttl': s_ttl,
                    'text_flags': text_flags
                }
                outer_data = {
                    'hostname': qname,
                    'data': dns_data
                }
                with open('results.json', 'a+') as outfile:
                    json.dump(outer_data, outfile)
            if verbose and hasattr(response, 'answer'):
                ans_index = 1
                for answer in response.answer:
                    print("Answer %d [ %s%s%s ]" % (ans_index, color.G, answer, color.N))
                    ans_index += 1
                print("")

    except Exception as e:
        print('%s: %s' % (server, e))
        sys.exit(1)


if __name__ == '__main__':
    main()
