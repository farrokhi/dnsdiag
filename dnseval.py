#!/usr/bin/env python3
#
# Copyright (c) 2016-2024, Babak Farrokhi
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
import socket
import sys

import dns.rcode
import dns.rdatatype
import dns.resolver

import util.dns

__author__ = 'Babak Farrokhi (babak@farrokhi.net)'
__license__ = 'BSD'
__progname__ = os.path.basename(sys.argv[0])

from util.dns import PROTO_UDP, PROTO_TCP, PROTO_TLS, PROTO_HTTPS, setup_signal_handler, flags_to_text
from util.shared import __version__, Colors


def usage():
    print("""%s version %s
Usage: %s [-ehmvCTXH] [-f server-list] [-j output.json] [-c count] [-t type] [-p port] [-w wait] hostname

  -h, --help         Display this help message
  -f, --file         Specify a DNS server list file to use (default: system resolvers)
  -c, --count        Number of requests to send (default: 10)
  -m, --cache-miss   Force a cache miss measurement by prepending a random hostname
  -w, --wait         Set the maximum wait time for a reply in seconds (default: 2)
  -t, --type         Set the DNS request record type (default: A)
  -T, --tcp          Use TCP as the transport protocol instead of UDP
  -X, --tls          Use TLS as the transport protocol
  -j, --json         Save the results to a specified file in JSON format
  -H, --doh          Use HTTPS as the transport protocol (DoH)
  -p, --port         Specify the DNS server port number (default: 53 for TCP/UDP, 853 for TLS)
  -S, --srcip        Set the query source IP address
  -e, --edns         Enable EDNS0 in requests
  -D, --dnssec       Enable the 'DNSSEC desired' (DO flag) in requests
  -C, --color        Enable colorful output
  -v, --verbose      Print the full DNS response details
""" % (__progname__, __version__, __progname__))
    sys.exit()


def maxlen(names):
    sn = sorted(names, key=len)
    return len(sn[-1])


def main():
    setup_signal_handler()

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
    json_output = False
    use_edns = False
    want_dnssec = False
    force_miss = False
    verbose = False
    color_mode = False
    qname = 'wikipedia.org'

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:c:t:w:S:TevCmXHDj:p:",
                                   ["help", "file=", "count=", "type=", "wait=", "json=", "tcp", "edns", "verbose",
                                    "color", "cache-miss", "srcip=", "tls", "doh", "dnssec", "port="])
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
            json_output = True
            json_filename = a
        elif o in ("-e", "--edns"):
            use_edns = True
        elif o in ("-D", "--dnssec"):
            want_dnssec = True
            use_edns = True  # implied
        elif o in ("-C", "--color"):
            color_mode = True
        elif o in ("-v", "--verbose"):
            verbose = True
        elif o in ("-X", "--tls"):
            proto = PROTO_TLS
            dst_port = 853  # default for DoT, unless overridden using -p
        elif o in ("-H", "--doh"):
            proto = PROTO_HTTPS
            dst_port = 443  # default for DoH, unless overridden using -p
        elif o in ("-p", "--port"):
            dst_port = int(a)

        else:
            print("Invalid option: %s" % o)
            usage()

    # validate RR type
    if not util.dns.valid_rdatatype(rdatatype):
        print('Error: Invalid record type "%s" ' % rdatatype)
        sys.exit(1)

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
            print("Error: No nameserver specified")

        f = [name.strip() for name in f]  # remove annoying blanks
        f = [x for x in f if not x.startswith('#') and len(x)]  # remove comments and empty entries

        width = maxlen(f)
        blanks = (width - 5) * ' '

        if not json_output:
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
                retval = util.dns.ping(qname, resolver, dst_port, rdatatype, waittime, count, proto, src_ip,
                                       use_edns=use_edns, force_miss=force_miss, want_dnssec=want_dnssec)

            except SystemExit:
                break
            except Exception as e:
                print('%s: %s' % (server, e))
                continue

            resolver = server.ljust(width + 1)
            text_flags = flags_to_text(retval.flags)

            s_ttl = str(retval.ttl)
            if s_ttl == "None":
                s_ttl = "N/A"

            if retval.r_lost_percent > 0:
                l_color = color.O
            else:
                l_color = color.N

            if json_output:
                dns_data = {
                    'hostname': qname,
                    'timestamp': str(datetime.datetime.now()),
                    'r_min': retval.r_min,
                    'r_avg': retval.r_avg,
                    'resolver': resolver.rstrip(),
                    'r_max': retval.r_max,
                    'r_lost_percent': retval.r_lost_percent,
                    's_ttl': s_ttl,
                    'text_flags': text_flags,
                    'flags': retval.flags,
                    'rcode': retval.rcode,
                    'rcode_text': retval.rcode_text,
                }
                outer_data = {
                    'hostname': qname,
                    'data': dns_data
                }

                if json_filename == '-':  # stdout
                    print(json.dumps(outer_data, indent=2))
                else:
                    with open(json_filename, 'a+') as outfile:
                        json.dump(outer_data, outfile, indent=2)

            else:
                result = "%s    %-8.3f    %-8.3f    %-8.3f    %-8.3f    %s%%%-3d%s     %-8s  %21s   %-20s" % (
                    resolver, retval.r_avg, retval.r_min, retval.r_max, retval.r_stddev, l_color, retval.r_lost_percent,
                    color.N, s_ttl, text_flags, retval.rcode_text)
                print(result.rstrip(), flush=True)

            if verbose and retval.answer and not json_output:
                ans_index = 1
                for answer in retval.answer:
                    print("Answer %d [ %s%s%s ]" % (ans_index, color.G, answer, color.N))
                    ans_index += 1
                print("")

    except Exception as e:
        print('%s: %s' % (server, e))
        sys.exit(1)


if __name__ == '__main__':
    main()
