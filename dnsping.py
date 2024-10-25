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
import os
import signal
import socket
import sys
import time
import httpx
from statistics import stdev

import dns.flags
import dns.resolver

from util.dns import PROTO_UDP, PROTO_TCP, PROTO_TLS, PROTO_HTTPS, PROTO_QUIC, proto_to_text, unsupported_feature, \
    random_string, getDefaultPort, valid_rdatatype
from util.shared import __version__

__author__ = 'Babak Farrokhi (babak@farrokhi.net)'
__license__ = 'BSD'
__progname__ = os.path.basename(sys.argv[0])
shutdown = False


def usage():
    print("""%s version %s
Usage: %s [-46aDeEFhLmqnrvTQxXH] [-i interval] [-w wait] [-p dst_port] [-P src_port] [-S src_ip]
       %s [-c count] [-t qtype] [-C class] [-s server] hostname

  -h, --help        Show this help message
  -q, --quiet       Suppress output
  -v, --verbose     Print the full DNS response
  -s, --server      Specify the DNS server to use (default: first entry from /etc/resolv.conf)
  -p, --port        Specify the DNS server port number (default: 53 for TCP/UDP, 853 for TLS)
  -T, --tcp         Use TCP as the transport protocol
  -X, --tls         Use TLS as the transport protocol
  -H, --doh         Use HTTPS as the transport protocol (DoH)
  -Q, --doq         Use QUIC as the transport protocol (DoQ)
  -4, --ipv4        Use IPv4 as the network protocol
  -6, --ipv6        Use IPv6 as the network protocol
  -P, --srcport     Specify the source port number for the query (default: 0)
  -S, --srcip       Specify the source IP address for the query (default: default interface address)
  -c, --count       Number of requests to send (default: 10, 0 for unlimited)
  -r, --norecurse   Enforce a non-recursive query by clearing the RD (recursion desired) bit
  -m, --cache-miss  Force cache miss measurement by prepending a random hostname
  -w, --wait        Maximum wait time for a reply (default: 2 seconds)
  -i, --interval    Time interval between requests (default: 1 second)
  -t, --type        DNS request record type (default: A)
  -L, --ttl         Display the response TTL (if present)
  -C, --class       DNS request record class (default: IN)
  -a, --answer      Display the first matching answer in rdata, if applicable
  -e, --edns        Enable EDNS0 and set its options
  -E, --ede         Display EDE (Extended DNS Error) messages, when available
  -n, --nsid        Enable the NSID bit to retrieve resolver identification (implies EDNS)
  -D, --dnssec      Enable the DNSSEC desired flag (implies EDNS)
  -F, --flags       Display response flags
  -x, --expert      Display additional information (implies --ttl, --flags, --ede)
""" % (__progname__, __version__, __progname__, ' ' * len(__progname__)))
    sys.exit(0)


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


def print_stderr(s, should_die):
    print(s, file=sys.stderr, flush=True)
    if should_die:
        sys.exit(1)


def validate_server_address(dnsserver, address_family):
    """checks if we have a valid dns server address and resolve if it is a hostname"""

    try:
        ipaddress.ip_address(dnsserver)
    except ValueError:  # so it is not a valid IPv4 or IPv6 address, so try to resolve host name
        try:
            dnsserver = socket.getaddrinfo(dnsserver, port=None, family=address_family)[1][4][0]
        except OSError:
            print_stderr('Error: cannot resolve hostname: %s' % dnsserver, True)
    return dnsserver


def main():
    setup_signal_handler()

    if len(sys.argv) == 1:
        usage()

    dns.rdata.load_all_types()
    # defaults
    rdatatype = 'A'
    rdata_class = dns.rdataclass.from_text('IN')
    count = 10
    timeout = 2
    interval = 1
    quiet = False
    verbose = False
    show_flags = False
    show_ede = False
    dnsserver = None  # do not try to use system resolver by default
    proto = PROTO_UDP
    dst_port = getDefaultPort(proto)
    use_default_dst_port = True
    src_port = 0
    src_ip = None
    use_edns = False
    want_nsid = False
    want_dnssec = False
    show_ttl = False
    force_miss = False
    show_answer = False
    request_flags = dns.flags.from_text('RD')
    af = socket.AF_INET
    qname = 'wikipedia.org'

    try:
        opts, args = getopt.getopt(sys.argv[1:], "qhc:s:t:w:i:vp:P:S:TQ46meDFXHrnEC:Lxa",
                                   ["help", "count=", "server=", "quiet", "type=", "wait=", "interval=", "verbose",
                                    "port=", "srcip=", "tcp", "ipv4", "ipv6", "cache-miss", "srcport=", "edns",
                                    "dnssec", "flags", "norecurse", "tls", "doh", "nsid", "ede", "class=", "ttl",
                                    "expert", "answer", "quic"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print_stderr(err, False)  # will print something like "option -a not recognized"
        usage()

    if args and len(args) == 1:
        qname = args[0]
    else:
        usage()

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()

        elif o in ("-c", "--count"):
            if a.isdigit():
                count = abs(int(a))
            else:
                print_stderr("Invalid count of requests: %s" % a, True)

        elif o in ("-v", "--verbose"):
            verbose = True

        elif o in ("-s", "--server"):
            dnsserver = a

        elif o in ("-q", "--quiet"):
            quiet = True
            verbose = False

        elif o in ("-w", "--wait"):
            timeout = int(a)

        elif o in ("-a", "--answer"):
            show_answer = True

        elif o in ("-x", "--expert"):
            show_flags = True
            show_ede = True
            show_ttl = True

        elif o in ("-m", "--cache-miss"):
            force_miss = True

        elif o in ("-i", "--interval"):
            interval = float(a)

        elif o in ("-L", "--ttl"):
            show_ttl = True

        elif o in ("-t", "--type"):
            rdatatype = a

        elif o in ("-C", "--class"):
            try:
                rdata_class = dns.rdataclass.from_text(a)
            except dns.rdataclass.UnknownRdataclass:
                print_stderr("Invalid RR class: %s" % a, True)

        elif o in ("-T", "--tcp"):
            proto = PROTO_TCP
            if use_default_dst_port:
                dst_port = getDefaultPort(proto)

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

        elif o in ("-4", "--ipv4"):
            af = socket.AF_INET

        elif o in ("-6", "--ipv6"):
            af = socket.AF_INET6

        elif o in ("-e", "--edns"):
            use_edns = True

        elif o in ("-n", "--nsid"):
            use_edns = True  # required
            want_nsid = True

        elif o in ("-r", "--norecurse"):
            request_flags = dns.flags.from_text('')

        elif o in ("-D", "--dnssec"):
            use_edns = True  # required
            want_dnssec = True

        elif o in ("-F", "--flags"):
            show_flags = True

        elif o in ("-E", "--ede"):
            show_ede = True

        elif o in ("-p", "--port"):
            dst_port = int(a)
            use_default_dst_port = False

        elif o in ("-P", "--srcport"):
            src_port = int(a)
            if src_port < 1024 and not quiet:
                print_stderr("WARNING: Source ports below 1024 are only available to superuser", False)

        elif o in ("-S", "--srcip"):
            src_ip = a

        else:
            usage()

    # Use system DNS server if parameter is not specified
    # remember not all systems have /etc/resolv.conf (i.e. Android)
    if dnsserver is None:
        dnsserver = dns.resolver.get_default_resolver().nameservers[0]

    dnsserver = validate_server_address(dnsserver, af)

    response_time = []
    i = 0

    # validate RR type
    if not valid_rdatatype(rdatatype):
        print_stderr('Error: Invalid record type: %s ' % rdatatype, True)

    print("%s DNS: %s:%d, hostname: %s, proto: %s, class: %s, type: %s, flags: [%s]" %
          (__progname__, dnsserver, dst_port, qname, proto_to_text(proto), dns.rdataclass.to_text(rdata_class),
           rdatatype, dns.flags.to_text(request_flags)), flush=True)

    while not shutdown:

        if 0 < count <= i:
            break
        else:
            i += 1

        if force_miss:
            fqdn = "_dnsdiag_%s_.%s" % (random_string(8, 8), qname)
        else:
            fqdn = qname

        if use_edns:
            edns_options = []
            if want_nsid:
                edns_options.append(dns.edns.GenericOption(dns.edns.NSID, ''))

            query = dns.message.make_query(fqdn, rdatatype, rdata_class, flags=request_flags,
                                           use_edns=True, want_dnssec=want_dnssec, payload=1232,
                                           options=edns_options)
        else:
            query = dns.message.make_query(fqdn, rdatatype, rdata_class, flags=request_flags,
                                           use_edns=False, want_dnssec=False)

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
                    answers = dns.query.tls(query, dnsserver, timeout=timeout, port=dst_port,
                                            source=src_ip, source_port=src_port)
                else:
                    unsupported_feature("DNS-over-TLS")

            elif proto is PROTO_HTTPS:
                if hasattr(dns.query, 'https'):
                    try:
                        answers = dns.query.https(query, dnsserver, timeout=timeout, port=dst_port,
                                                  source=src_ip, source_port=src_port)
                    except httpx.ConnectError:
                        print_stderr(f"The server did not respond to DoH on port {dst_port}", should_die=True)
                else:
                    unsupported_feature("DNS-over-HTTPS (DoH)")

            elif proto is PROTO_QUIC:
                if hasattr(dns.query, 'quic'):
                    try:
                        answers = dns.query.quic(query, dnsserver, timeout=timeout, port=dst_port,
                                                 source=src_ip, source_port=src_port)
                    except dns.exception.Timeout:
                        print_stderr(f"The server did not respond to DoQ on port {dst_port}", should_die=True)
                else:
                    unsupported_feature("DNS-over-QUIC (DoQ)")

            etime = time.perf_counter()
        except dns.resolver.NoNameservers as e:
            if not quiet:
                print_stderr("No response to DNS request", False)
                if verbose:
                    print_stderr("error: %s" % e, False)
            sys.exit(1)
        except (httpx.ConnectTimeout, dns.exception.Timeout):
            if not quiet:
                print("Request timeout", flush=True)
        except httpx.ReadTimeout:
            if not quiet:
                print("Read timeout", flush=True)
        except PermissionError:
            if not quiet:
                print_stderr("Permission denied", True)
            sys.exit(1)
        except OSError as e:
            if not quiet:
                print_stderr("%s" % e, True)
            sys.exit(1)
        except ValueError:
            if not quiet:
                print_stderr("Invalid Response", False)
                continue
        else:
            # convert time to milliseconds, considering that
            # time property is returned differently by query.https
            if type(answers.time) is datetime.timedelta:
                elapsed = answers.time.total_seconds() * 1000
            else:
                elapsed = answers.time * 1000
            response_time.append(elapsed)
            if not quiet:
                extras = ""
                extras += " %s" % dns.rcode.to_text(answers.rcode())  # add response code

                if show_ttl:
                    if answers.answer:
                        ans_ttl = str(answers.answer[0].ttl)
                        extras += " [TTL=%-4s]" % ans_ttl

                if show_flags:
                    ans_flags = dns.flags.to_text(answers.flags)
                    edns_flags = dns.flags.edns_to_text(answers.ednsflags)
                    extras += " [%s]" % " ".join([ans_flags, edns_flags]).rstrip(' ')  # show both regular + edns flags

                if want_nsid:
                    for ans_opt in answers.options:
                        if ans_opt.otype == dns.edns.OptionType.NSID:
                            nsid_val = ans_opt.nsid
                            extras += " [ID: %s]" % nsid_val.decode("utf-8")

                if show_ede:
                    for ans_opt in answers.options:  # EDE response is optional, but print if there is one
                        if ans_opt.otype == dns.edns.EDE:
                            extras += " [EDE %d: %s]" % (ans_opt.code, ans_opt.text)

                if show_answer:  # The answer should be displayed at the rightmost
                    for ans in answers.answer:
                        if ans.rdtype == dns.rdatatype.from_text(rdatatype):  # is this the answer to our question?
                            # extras += " [%s]" % ans[0]
                            extras += " [RDATA: %s]" % ans[0]
                            break

                print("%-3d bytes from %s: seq=%-3d time=%-7.3f ms %s" % (
                    len(answers.to_wire()), dnsserver, i, elapsed, extras), flush=True)

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
