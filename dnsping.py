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
import os
import signal
import socket
import sys
import time
from statistics import stdev

import dns.edns
import dns.exception
import dns.flags
import dns.message
import dns.query
import dns.rcode
import dns.rdata
import dns.rdataclass
import dns.rdatatype
import dns.resolver
import httpx

from dnsdiag.dns import PROTO_UDP, PROTO_TCP, PROTO_TLS, PROTO_HTTPS, PROTO_QUIC, PROTO_HTTP3, proto_to_text, \
    unsupported_feature, random_string, getDefaultPort, valid_rdatatype
from dnsdiag.shared import __version__

__author__ = 'Babak Farrokhi (babak@farrokhi.net)'
__license__ = 'BSD'
__progname__ = os.path.basename(sys.argv[0])
shutdown = False


def usage():
    print("""%s version %s
Usage: %s [-346aDeEFhLmqnrvTQxXHq] [-i interval] [-w wait] [-p dst_port] [-P src_port] [-S src_ip]
       %s [-c count] [-t qtype] [-C class] [-s server] [--ecs client_subnet] hostname

  -h, --help        Show this help message
  -q, --quiet       Suppress output
  -v, --verbose     Print the full DNS response
  -s, --server      Specify the DNS server to use (default: first entry from /etc/resolv.conf)
  -p, --port        Specify the DNS server port number (default: 53 for TCP/UDP, 853 for TLS)
  -T, --tcp         Use TCP as the transport protocol
  -X, --tls         Use TLS as the transport protocol
  -H, --doh         Use HTTPS as the transport protocol (DoH)
  -3, --http3       Use HTTP/3 as the transport protocol (DoH3)
  -Q, --quic        Use QUIC as the transport protocol (DoQ)
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
      --ecs         Set EDNS Client Subnet option (format: IP/prefix, e.g., 192.168.1.0/24)
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
    client_subnet = None
    show_ttl = False
    force_miss = False
    show_answer = False
    request_flags = dns.flags.from_text('RD')
    af = socket.AF_INET
    qname = 'wikipedia.org'

    try:
        opts, args = getopt.getopt(sys.argv[1:], "qhc:s:t:w:i:vp:P:S:TQ346meDFXHrnEC:Lxa",
                                   ["help", "count=", "server=", "quiet", "type=", "wait=", "interval=", "verbose",
                                    "port=", "srcip=", "tcp", "ipv4", "ipv6", "cache-miss", "srcport=", "edns",
                                    "dnssec", "flags", "norecurse", "tls", "doh", "nsid", "ede", "class=", "ttl",
                                    "expert", "answer", "quic", "http3", "ecs="])
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

        elif o in ("-3", "--http3"):
            proto = PROTO_HTTP3
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

        elif o == "--ecs":
            client_subnet = a
            use_edns = True  # ECS requires EDNS

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
            if client_subnet:
                try:
                    ecs_option = dns.edns.ECSOption.from_text(client_subnet)
                    edns_options.append(ecs_option)
                except Exception as e:
                    print_stderr("Error: Invalid ECS format '%s': %s" % (client_subnet, e), True)

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

            elif proto is PROTO_HTTP3:
                if hasattr(dns.query, 'quic'):
                    try:
                        answers = dns.query.https(query, dnsserver, timeout=timeout, port=dst_port,
                                                  source=src_ip, source_port=src_port,
                                                  http_version=dns.query.HTTPVersion.H3)
                    except ConnectionRefusedError:
                        print_stderr(f"The server did not respond to DNS-over-HTTPS/3 on port {dst_port}",
                                     should_die=True)
                else:
                    unsupported_feature("DNS-over-HTTPS/3 (DoH3)")

            elif proto is PROTO_QUIC:
                if hasattr(dns.query, 'quic'):
                    try:
                        answers = dns.query.quic(query, dnsserver, timeout=timeout, port=dst_port,
                                                 source=src_ip, source_port=src_port)
                    except dns.exception.Timeout:
                        print_stderr(f"The server did not respond to DoQ on port {dst_port}", should_die=True)
                    except ConnectionRefusedError:
                        print_stderr(f"The server did not respond to DNS-over-HTTPS/3 on port {dst_port}",
                                     should_die=True)
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
                    if want_dnssec and not (answers.flags & dns.flags.AD):
                        ans_flags += " --"  # add padding to printer output when dnssec is requested, but AD flag is not set
                    extras += " [%s]" % " ".join([ans_flags, edns_flags]).rstrip(' ')  # show both regular + edns flags

                # Display EDNS options compactly (only for explicitly enabled options)
                edns_parts = []

                if want_nsid and answers.options:
                    for ans_opt in answers.options:
                        if ans_opt.otype == dns.edns.OptionType.NSID:
                            nsid_val = ans_opt.nsid
                            if nsid_val:
                                edns_parts.append("NSID:%s" % nsid_val.decode("utf-8"))

                if show_ede and answers.options:
                    for ans_opt in answers.options:
                        if ans_opt.otype == dns.edns.EDE:
                            if ans_opt.text:
                                # Truncate EDE text for ping output to prevent display issues
                                truncated_text = ans_opt.text[:50] + "..." if len(ans_opt.text) > 50 else ans_opt.text
                                edns_parts.append("EDE:%d(\"%s\")" % (ans_opt.code, truncated_text))
                            else:
                                edns_parts.append("EDE:%d" % ans_opt.code)

                # Always show ECS if present (since it's typically echoed back when requested)
                if answers.options:
                    for ans_opt in answers.options:
                        if ans_opt.otype == dns.edns.OptionType.ECS:
                            if ans_opt.address:
                                edns_parts.append("ECS:%s/%d" % (ans_opt.address, ans_opt.scopelen or ans_opt.srclen))
                            else:
                                edns_parts.append("ECS:auto")

                if edns_parts:
                    extras += " [%s]" % ", ".join(edns_parts)

                if show_answer:  # The answer should be displayed at the rightmost
                    for ans in answers.answer:
                        if ans.rdtype == dns.rdatatype.from_text(rdatatype):  # is this the answer to our question?
                            extras += " [RDATA: %s]" % ans[0]
                            break

                print("%-3d bytes from %s: seq=%-3d time=%-7.3f ms %s" % (
                    len(answers.to_wire()), dnsserver, i, elapsed, extras), flush=True)

            if verbose:
                print(answers.to_text(), flush=True)

                # Display EDNS options if present
                if answers.options:
                    print(";EDNS OPTIONS")
                    for ans_opt in answers.options:
                        option_name = "UNKNOWN"
                        option_details = ""

                        if ans_opt.otype == dns.edns.OptionType.NSID:
                            option_name = "NSID"
                            nsid_val = ans_opt.nsid
                            option_details = nsid_val.decode("utf-8") if nsid_val else ""
                        elif ans_opt.otype == dns.edns.OptionType.ECS:
                            option_name = "ECS"
                            option_details = "family=%d, source=%d, scope=%d, address=%s" % (
                                ans_opt.family, ans_opt.srclen, ans_opt.scopelen,
                                ans_opt.address if ans_opt.address else "None")
                        elif ans_opt.otype == dns.edns.EDE:
                            option_name = "EDE"
                            option_details = "code=%d, text=\"%s\"" % (ans_opt.code, ans_opt.text or "")
                        elif ans_opt.otype == 10:  # COOKIE
                            option_name = "COOKIE"
                            option_details = "length=%d" % len(ans_opt.data)
                        elif ans_opt.otype == 11:  # TCP-KEEPALIVE
                            option_name = "TCP-KEEPALIVE"
                            if len(ans_opt.data) >= 2:
                                import struct
                                timeout = struct.unpack('!H', ans_opt.data[:2])[0]
                                option_details = "timeout=%ds" % timeout
                        elif ans_opt.otype == 12:  # PADDING
                            option_name = "PADDING"
                            option_details = "length=%d" % len(ans_opt.data)
                        elif ans_opt.otype == 13:  # CHAIN
                            option_name = "CHAIN"
                            option_details = "closest_encloser=%s" % ans_opt.data.decode('utf-8', errors='ignore')
                        elif ans_opt.otype == 14:  # KEY-TAG
                            option_name = "KEY-TAG"
                            import struct
                            if len(ans_opt.data) >= 2:
                                key_tags = []
                                for i in range(0, len(ans_opt.data), 2):
                                    if i + 1 < len(ans_opt.data):
                                        tag = struct.unpack('!H', ans_opt.data[i:i+2])[0]
                                        key_tags.append(str(tag))
                                option_details = "tags=[%s]" % ",".join(key_tags)
                        else:
                            option_details = "type=%d, length=%d" % (ans_opt.otype, len(ans_opt.data))

                        print("%s (%d): %s" % (option_name, ans_opt.otype, option_details), flush=True)

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
