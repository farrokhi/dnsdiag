#!/usr/bin/env python3
#
# Copyright (c) 2016-2025, Babak Farrokhi
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
import signal
import socket
import sys
import time

import dns.rcode
import dns.rdatatype
import dns.resolver

import dnsdiag.dns
from dnsdiag.dns import PROTO_UDP, PROTO_TCP, PROTO_TLS, PROTO_HTTPS, PROTO_QUIC, PROTO_HTTP3, flags_to_text, getDefaultPort
from dnsdiag.shared import __version__, Colors, valid_hostname, die, err

__author__ = 'Babak Farrokhi (babak@farrokhi.net)'
__license__ = 'BSD'
__progname__ = os.path.basename(sys.argv[0])
shutdown = False


def setup_signal_handler():
    try:
        signal.signal(signal.SIGTSTP, signal.SIG_IGN)  # ignore CTRL+Z
        signal.signal(signal.SIGINT, signal_handler)  # custom CTRL+C handler
    except AttributeError:  # not all signals are supported on all platforms
        pass


def signal_handler(sig, frame):
    global shutdown
    if shutdown:  # pressed twice, so exit immediately
        sys.exit(0)
    shutdown = True  # pressed once, exit gracefully


def usage(exit_code=0):
    print("""%s version %s
Usage: %s [-ehmvCTXHQ3SD] [-f server-list] [-j output.json] [-c count] [-t type] [-p port] [-w wait] hostname

  -h, --help         Display this help message
  -f, --file         Specify a DNS server list file to use (default: system resolvers)
  -c, --count        Number of requests to send (default: 10)
  -m, --cache-miss   Force a cache miss measurement by prepending a random hostname
  -w, --wait         Set the maximum wait time for a reply in seconds (default: 2)
  -t, --type         Set the DNS request record type (default: A)
  -T, --tcp          Use TCP as the transport protocol instead of UDP
  -X, --tls          Use TLS as the transport protocol (DoT)
  -Q, --quic         Use QUIC as the transport protocol (DoQ)
  -H, --doh          Use HTTPS as the transport protocol (DoH)
  -3, --http3        Use HTTP/3 as the transport protocol (DoH3)
  -j, --json         Save the results to a specified file in JSON format
  -p, --port         Specify the DNS server port number (default: protocol-specific)
  -S, --srcip        Set the query source IP address
  -e, --edns         Enable EDNS0 in requests
  -D, --dnssec       Enable the 'DNSSEC desired' (DO flag) in requests
  -C, --color        Enable colorful output
  -v, --verbose      Print the full DNS response details
      --skip-warmup  Disable cache warmup (default: warmup enabled)
""" % (__progname__, __version__, __progname__))
    sys.exit(exit_code)


def maxlen(names):
    sn = sorted(names, key=len)
    return len(sn[-1])


def main():
    global shutdown
    setup_signal_handler()

    if len(sys.argv) == 1:
        usage()

    # defaults
    rdatatype = 'A'
    proto = PROTO_UDP
    src_ip = None
    dst_port = getDefaultPort(proto)
    use_default_dst_port = True
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
    warmup = True
    qname = 'wikipedia.org'

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:c:t:w:S:TevCmXHQ3Dj:p:",
                                   ["help", "file=", "count=", "type=", "wait=", "json=", "tcp", "edns", "verbose",
                                    "color", "cache-miss", "srcip=", "tls", "doh", "quic", "http3", "dnssec", "port=", "skip-warmup"])
    except getopt.GetoptError as getopt_err:
        err(str(getopt_err))
        usage(1)

    if args and len(args) == 1:
        qname = args[0]
        if not valid_hostname(qname, allow_underscore=True):
            die(f"ERROR: invalid hostname: {qname}")
    else:
        usage(1)

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-c", "--count"):
            try:
                count = int(a)
                if count < 1:
                    die(f"ERROR: count must be positive: {a}")
            except ValueError:
                die(f"ERROR: invalid count value: {a}")
        elif o in ("-f", "--file"):
            inputfilename = a
            fromfile = True
        elif o in ("-w", "--wait"):
            try:
                waittime = int(a)
                if waittime < 0:
                    die(f"ERROR: wait time must be non-negative: {a}")
            except ValueError:
                die(f"ERROR: invalid wait time value: {a}")
        elif o in ("-m", "--cache-miss"):
            force_miss = True
        elif o in ("-t", "--type"):
            rdatatype = a
        elif o in ("-T", "--tcp"):
            proto = PROTO_TCP
            if use_default_dst_port:
                dst_port = getDefaultPort(proto)
        elif o in ("-S", "--srcip"):
            try:
                ipaddress.ip_address(a)
                src_ip = a
            except ValueError:
                die(f"ERROR: invalid source IP address: {a}")
        elif o in ("-j", "--json"):
            json_output = True
            json_filename = a
        elif o in ("-e", "--edns"):
            use_edns = True
        elif o in ("-D", "--dnssec"):
            want_dnssec = True
            use_edns = True
        elif o in ("-C", "--color"):
            color_mode = True
        elif o in ("-v", "--verbose"):
            verbose = True
        elif o in ("-X", "--tls"):
            proto = PROTO_TLS
            if use_default_dst_port:
                dst_port = getDefaultPort(proto)
        elif o in ("-H", "--doh"):
            proto = PROTO_HTTPS
            if use_default_dst_port:
                dst_port = getDefaultPort(proto)
        elif o in ("-Q", "--quic"):
            proto = PROTO_QUIC
            if use_default_dst_port:
                dst_port = getDefaultPort(proto)
        elif o in ("-3", "--http3"):
            proto = PROTO_HTTP3
            if use_default_dst_port:
                dst_port = getDefaultPort(proto)
        elif o in ("-p", "--port"):
            try:
                dst_port = int(a)
                if not (0 < dst_port <= 65535):
                    die(f"ERROR: port must be between 1 and 65535: {a}")
                use_default_dst_port = False
            except ValueError:
                die(f"ERROR: invalid port value: {a}")
        elif o in ("--skip-warmup",):
            warmup = False

        else:
            print("Invalid option: %s" % o)
            usage(1)

    # validate RR type
    if not dnsdiag.dns.valid_rdatatype(rdatatype):
        die(f'ERROR: invalid record type "{rdatatype}"')

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
                    die(str(e))
        else:
            f = dns.resolver.get_default_resolver().nameservers

        if len(f) == 0:
            print("ERROR: No nameserver specified")

        f = [name.strip() for name in f]  # remove annoying blanks
        f = [x for x in f if not x.startswith('#') and len(x)]  # remove comments and empty entries

        width = maxlen(f)
        blanks = (width - 5) * ' '

        if warmup and not json_output:
            print("Warming up DNS caches...")
            for server in f:
                if shutdown:
                    break
                if server.lstrip() == '':
                    continue
                server = server.replace(' ', '')
                try:
                    ipaddress.ip_address(server)
                except ValueError:
                    try:
                        resolver = socket.getaddrinfo(server, port=None)[1][4][0]
                    except (OSError, Exception):
                        resolver = None
                else:
                    resolver = server

                if resolver:
                    try:
                        dnsdiag.dns.ping(qname, resolver, dst_port, rdatatype, waittime, 1, proto, src_ip,
                                        use_edns=use_edns, force_miss=force_miss, want_dnssec=want_dnssec)
                    except (KeyboardInterrupt, SystemExit):
                        shutdown = True
                        break
                    except Exception:
                        pass
            if not shutdown:
                time.sleep(1)

        if not json_output:
            print('server' + blanks +
                  '  avg(ms)  min(ms)  max(ms)  stddev(ms)  lost(%)  ttl      flags                      response')
            print((95 + width) * '-')

        for server in f:
            # Check for shutdown signal
            if shutdown:
                break

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
                    print('ERROR: cannot resolve hostname:', server)
                    resolver = None
                except Exception:
                    pass
            else:
                resolver = server

            if not resolver:
                continue

            try:
                retval = dnsdiag.dns.ping(qname, resolver, dst_port, rdatatype, waittime, count, proto, src_ip,
                                       use_edns=use_edns, force_miss=force_miss, want_dnssec=want_dnssec)

            except KeyboardInterrupt:
                shutdown = True
                break
            except SystemExit:
                shutdown = True
                break
            except Exception as e:
                print('%s: %s' % (server, e))
                continue

            resolver = server.ljust(width + 1)
            text_flags = flags_to_text(retval.flags)
            edns_flags_text = dns.flags.edns_to_text(retval.ednsflags)
            if edns_flags_text:
                text_flags = " ".join([text_flags, edns_flags_text])
            else:
                text_flags = " ".join([text_flags, "--"])

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
                    'ednsflags': retval.ednsflags,
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
                result = "%s  %-7.2f  %-7.2f  %-7.2f  %-10.2f  %s%%%-3d%s     %-7s  %-26s  %-12s" % (
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
        die(f'{server}: {e}')


if __name__ == '__main__':
    main()
