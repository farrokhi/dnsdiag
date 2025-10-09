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


import concurrent.futures
import getopt
import ipaddress
import os
import signal
import socket
import sys
import time

import dns.query
import dns.rdatatype
import dns.resolver

import dnsdiag.whois
from typing import Any, Dict
from dnsdiag.dns import PROTO_UDP, PROTO_TCP, PROTO_QUIC, PROTO_HTTP3, getDefaultPort, die, err
from dnsdiag.shared import __version__, Colors

# Global Variables
quiet = False
whois_cache: Dict[str, Any] = {}
shutdown = False

# Constants
__author__ = 'Babak Farrokhi (babak@farrokhi.net)'
__license__ = 'BSD'
__progname__ = os.path.basename(sys.argv[0])


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


def test_import():
    #  passing this test means imports were successful
    pass


def usage():
    print("""%s version %s
Usage: %s [-aenqhCxTSQ346] [-s server] [-p port] [-c count] [-t type] [-w wait] hostname

Options:
  -h, --help        Show this help message
  -q, --quiet       Enable quiet mode: suppress additional information, showing only traceroute output
  -T, --tcp         Use TCP as the transport protocol
  -Q, --quic        Use QUIC as the transport protocol (DoQ)
  -3, --http3       Use HTTP/3 as the transport protocol (DoH3)
  -4, --ipv4        Use IPv4 (only used when server is a hostname)
  -6, --ipv6        Use IPv6 (only used when server is a hostname)
  -x, --expert      Display expert hints, if available
  -a, --asn         Enable AS# lookups for each encountered hop
  -s, --server      Specify the DNS server to use (default: first system resolver)
  -p, --port        Set the DNS server port number (default: 53)
  -S, --srcip       Set the source IP address for the query (default: address of the default network interface)
  -c, --count       Specify the maximum number of hops (default: 30)
  -w, --wait        Set the maximum wait time for a reply, in seconds (default: 2)
  -t, --type        DNS request record type (default: A)
  -C, --color       Enable colorful output
  -e, --edns        Enable EDNS0 (default: disabled)
  -n                Disable hostname resolution for IP addresses
""" % (__progname__, __version__, __progname__))
    sys.exit()


def expert_report(trace_path, color_mode):
    color = Colors(color_mode)
    print("\n%s=== Expert Hints ===%s" % (color.B, color.N))
    if len(trace_path) == 0:
        print(" [*] empty trace - should not happen")
        return

    private_network_radius = 4  # number of hops we assume we are still inside our local network
    prev_hop = None
    if len(trace_path) > 1:
        prev_hop = trace_path[-2]

    if len(trace_path) < 2:
        print(
            " %s[*]%s path too short (possible DNS hijacking, unless it is a local DNS resolver)" % (color.R, color.N))
        return

    if prev_hop == '*' and len(trace_path) > private_network_radius:
        print(" %s[*]%s public DNS server is next to an invisible hop (probably a firewall)" % (color.R, color.N))
        return

    if prev_hop and len(trace_path) > private_network_radius and ipaddress.ip_address(prev_hop).is_private:
        print(" %s[*]%s public DNS server is next to a private IP address (possible hijacking)" % (color.R, color.N))
        return

    if prev_hop and len(trace_path) > private_network_radius and ipaddress.ip_address(prev_hop).is_reserved:
        print(" %s[*]%s public DNS server is next to a reserved IP address (possible hijacking)" % (color.R, color.N))
        return

    # no expert info available
    print(" %s[*]%s No expert hint available for this trace" % (color.G, color.N))


def ping(qname, server, rdtype, proto, port, ttl, timeout, src_ip, use_edns):
    reached = False
    resp_time = None
    resp = None

    try:
        resp = dnsdiag.dns.ping(qname, server, port, rdtype, timeout, 1, proto, src_ip, use_edns, force_miss=False,
                             want_dnssec=False, socket_ttl=ttl)

    except SystemExit:
        raise
    except Exception as e:
        die(f"unexpected error: {e}")
    else:
        if resp and resp.answer:
            reached = True
            resp_time = resp.r_max

    return reached, resp_time


def main():
    global quiet, shutdown

    setup_signal_handler()

    if len(sys.argv) == 1:
        usage()

    rdatatype = 'A'
    count = 30
    timeout = 2
    dnsserver = None
    proto = PROTO_UDP
    dest_port = getDefaultPort(proto)
    use_default_dest_port = True
    src_ip = None
    hops = 0
    as_lookup = False
    expert_mode = False
    should_resolve = True
    use_edns = False
    color_mode = False
    af = None  # auto-detect from server address

    args = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "aqhc:s:S:t:w:p:nexCTQ346",
                                   ["help", "count=", "server=", "quiet", "type=", "wait=", "asn", "port=", "expert",
                                    "color", "srcip=", "tcp", "quic", "http3", "ipv4", "ipv6"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err)  # will print something like "option -a not recognized"
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
        elif o in ("-x", "--expert"):
            expert_mode = True
        elif o in ("-s", "--server"):
            dnsserver = a
        elif o in ("-q", "--quiet"):
            quiet = True
        elif o in ("-S", "--srcip"):
            src_ip = a
        elif o in ("-w", "--wait"):
            timeout = int(a)
        elif o in ("-t", "--type"):
            rdatatype = a
        elif o in ("-p", "--port"):
            dest_port = int(a)
            use_default_dest_port = False
        elif o in ("-C", "--color"):
            color_mode = True
        elif o in "-n":
            should_resolve = False
        elif o in ("-T", "--tcp"):
            proto = PROTO_TCP
            if use_default_dest_port:
                dest_port = getDefaultPort(proto)
        elif o in ("-Q", "--quic"):
            proto = PROTO_QUIC
            if use_default_dest_port:
                dest_port = getDefaultPort(proto)
        elif o in ("-3", "--http3"):
            proto = PROTO_HTTP3
            if use_default_dest_port:
                dest_port = getDefaultPort(proto)
        elif o in ("-4", "--ipv4"):
            af = socket.AF_INET
        elif o in ("-6", "--ipv6"):
            af = socket.AF_INET6
        elif o in ("-a", "--asn"):
            as_lookup = True
        elif o in ("-e", "--edns"):
            use_edns = True
        else:
            usage()

    color = Colors(color_mode)

    # validate RR type
    if not dnsdiag.dns.valid_rdatatype(rdatatype):
        die(f'ERROR: invalid record type "{rdatatype}"')

    # Use system DNS server if parameter is not specified
    # remember not all systems have /etc/resolv.conf (i.e. Android)
    if dnsserver is None:
        nameservers = dns.resolver.get_default_resolver().nameservers
        # If user specified -4 or -6, filter for that address family
        if af is not None:
            filtered = []
            for ns in nameservers:
                try:
                    addr = ipaddress.ip_address(ns)
                    if (af == socket.AF_INET and isinstance(addr, ipaddress.IPv4Address)) or \
                       (af == socket.AF_INET6 and isinstance(addr, ipaddress.IPv6Address)):
                        filtered.append(ns)
                except ValueError:
                    pass
            if not filtered:
                af_name = "IPv4" if af == socket.AF_INET else "IPv6"
                die(f"ERROR: no {af_name} nameservers found in system resolver")
            dnsserver = filtered[0]
        else:
            dnsserver = nameservers[0]

    # check if we have a valid dns server address and detect/set address family
    try:
        addr = ipaddress.ip_address(dnsserver)
        # Auto-detect address family from IP address (or verify it matches user request)
        if isinstance(addr, ipaddress.IPv4Address):
            if af is not None and af != socket.AF_INET:
                die("ERROR: DNS server is IPv4 but -6 flag was specified")
            af = socket.AF_INET
        else:  # IPv6
            if af is not None and af != socket.AF_INET6:
                die("ERROR: DNS server is IPv6 but -4 flag was specified")
            af = socket.AF_INET6
    except ValueError:  # so it is not a valid IPv4 or IPv6 address, so try to resolve host name
        # If af not specified, default to IPv4
        if af is None:
            af = socket.AF_INET
        try:
            if af == socket.AF_INET6:
                dnsserver = socket.getaddrinfo(dnsserver, port=None, family=af, flags=socket.AI_V4MAPPED)[0][4][0]
            else:
                dnsserver = socket.getaddrinfo(dnsserver, port=None, family=af)[0][4][0]
        except OSError:
            die(f'ERROR: cannot resolve hostname: {dnsserver}')

    # Validate source IP address family if specified
    if src_ip:
        try:
            src_addr = ipaddress.ip_address(src_ip)
            if (af == socket.AF_INET and not isinstance(src_addr, ipaddress.IPv4Address)) or \
               (af == socket.AF_INET6 and not isinstance(src_addr, ipaddress.IPv6Address)):
                af_name = "IPv4" if af == socket.AF_INET else "IPv6"
                src_type = "IPv4" if isinstance(src_addr, ipaddress.IPv4Address) else "IPv6"
                die(f"ERROR: source IP is {src_type} but target DNS server is {af_name}")
        except ValueError:
            die(f"ERROR: invalid source IP address: {src_ip}")

    # Select correct ICMP protocol based on address family
    if af == socket.AF_INET:
        icmp_proto = socket.getprotobyname('icmp')
    else:  # AF_INET6
        icmp_proto = socket.getprotobyname('ipv6-icmp')

    ttl = 1
    reached = False
    trace_path = []

    if not quiet:
        # Wrap IPv6 addresses in brackets for better readability
        server_display = f"[{dnsserver}]" if ':' in dnsserver else dnsserver
        print("%s DNS: %s:%d, hostname: %s, rdatatype: %s" % (__progname__, server_display, dest_port, qname, rdatatype),
              flush=True)

    while True:
        # Check for shutdown signal
        if shutdown:
            break

        # some platforms permit opening a DGRAM socket for ICMP without root permission
        # if not availble, we will fall back to RAW which explicitly requires root permission
        try:
            icmp_socket = socket.socket(af, socket.SOCK_RAW, icmp_proto)
        except OSError:
            try:
                icmp_socket = socket.socket(af, socket.SOCK_DGRAM, icmp_proto)
            except OSError:
                die("ERROR: unable to create ICMP socket with unprivileged user. Please run as root.")

        # Bind socket based on address family
        if af == socket.AF_INET:
            icmp_socket.bind(("", dest_port))
        else:  # AF_INET6
            icmp_socket.bind(("::", dest_port))
        icmp_socket.settimeout(timeout)

        curr_addr = None

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:  # dispatch dns lookup to another thread
            stime = time.perf_counter()
            thr = pool.submit(ping, qname, dnsserver, rdatatype, proto, dest_port, ttl, timeout, src_ip=src_ip,
                              use_edns=use_edns)

            try:  # expect ICMP response
                packet, curr_addr = icmp_socket.recvfrom(512)
                # Parse ICMP packet based on address family
                if af == socket.AF_INET:
                    # IPv4: IP header (20 bytes) + ICMP header (8 bytes) + IP header (20 bytes) + UDP header
                    # ICMP Time Exceeded type = 11
                    if len(packet) > 51:
                        icmp_type = packet[20]
                        l4_dst_port = packet[50] << 8 | packet[51]
                        if icmp_type == 11 and l4_dst_port == dest_port:
                            curr_addr = curr_addr[0]
                        else:
                            curr_addr = None
                    else:
                        curr_addr = None
                else:  # AF_INET6
                    # IPv6: kernel strips IPv6 header, so we get:
                    # ICMPv6 header (8 bytes) + Original IPv6 header (40 bytes) + UDP header
                    # ICMPv6 Time Exceeded type = 3
                    if len(packet) > 50:
                        icmp_type = packet[0]
                        l4_dst_port = packet[50] << 8 | packet[51]
                        if icmp_type == 3 and l4_dst_port == dest_port:
                            curr_addr = curr_addr[0]
                        else:
                            curr_addr = None
                    else:
                        curr_addr = None
            except socket.error:
                pass
            except KeyboardInterrupt:
                shutdown = True
                break
            except SystemExit:
                shutdown = True
                break
            finally:
                etime = time.perf_counter()
                icmp_socket.close()

        try:
            reached, resp_time = thr.result()
        except SystemExit:
            shutdown = True
            break
        except KeyboardInterrupt:
            shutdown = True
            break

        if reached:
            curr_addr = dnsserver
            elapsed = resp_time
        else:
            elapsed = abs(etime - stime) * 1000  # convert to milliseconds

        curr_name = curr_addr
        if should_resolve:
            try:
                if curr_addr:
                    curr_name = socket.gethostbyaddr(curr_addr)[0]
            except socket.error:
                curr_name = curr_addr
            except KeyboardInterrupt:
                shutdown = True
                break
            except SystemExit:
                shutdown = True
                break
            except Exception:
                print("unxpected error: ", sys.exc_info()[0])

        # Check for shutdown signal after hostname resolution
        if shutdown:
            break

        global whois_cache
        if curr_addr:
            as_name = ""
            if as_lookup:
                asn, whois_cache = dnsdiag.whois.asn_lookup(curr_addr, whois_cache)
                as_name = ''
                try:
                    if asn and asn.asn != "NA":
                        as_name = "[AS%s %s] " % (asn.asn, asn.owner)
                except AttributeError:
                    if shutdown:
                        sys.exit(0)

            c = color.N  # default
            if curr_addr != '*':
                try:
                    IP = ipaddress.ip_address(curr_addr)
                    if IP.is_private:
                        c = color.R
                    if IP.is_reserved:
                        c = color.B
                    if curr_addr == dnsserver:
                        c = color.G
                except Exception:
                    pass

            print("%d\t%s (%s%s%s) %s%.3f ms" % (ttl, curr_name, c, curr_addr, color.N, as_name, elapsed), flush=True)
            trace_path.append(curr_addr)
        else:
            print("%d\t *" % ttl, flush=True)
            trace_path.append("*")

        ttl += 1
        hops += 1
        if (hops >= count) or (curr_addr == dnsserver) or reached:
            break

    if expert_mode and not shutdown:
        expert_report(trace_path, color_mode)


if __name__ == '__main__':
    try:
        whois_cache = dnsdiag.whois.restore()
        main()
    finally:
        dnsdiag.whois.save(whois_cache)
