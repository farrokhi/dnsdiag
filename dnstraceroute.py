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


import concurrent.futures
import getopt
import ipaddress
import os
import socket
import sys
import time

import dns.query
import dns.rdatatype
import dns.resolver

import util.whois
from util.dns import PROTO_UDP, PROTO_TCP, setup_signal_handler
from util.shared import __version__, Colors

# Global Variables
quiet = False
whois_cache = {}

# Constants
__author__ = 'Babak Farrokhi (babak@farrokhi.net)'
__license__ = 'BSD'
__progname__ = os.path.basename(sys.argv[0])


def test_import():
    #  passing this test means imports were successful
    pass


def usage():
    print("""%s version %s
Usage: %s [-aeqhCx] [-s server] [-p port] [-c count] [-t type] [-w wait] hostname

Options:
  -h, --help        Show this help message
  -q, --quiet       Enable quiet mode: suppress additional information, showing only traceroute output
  -T, --tcp         Use TCP as the transport protocol
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

    try:
        resp = util.dns.ping(qname, server, port, rdtype, timeout, 1, proto, src_ip, use_edns, force_miss=False,
                             want_dnssec=False, socket_ttl=ttl)

    except SystemExit:
        pass
    except Exception as e:
        print("unxpected error: ", e)
        sys.exit(1)
    else:
        if resp.answer:
            reached = True
            resp_time = resp.r_max

    return reached, resp_time


def main():
    global quiet
    shutdown = False

    setup_signal_handler()

    if len(sys.argv) == 1:
        usage()

    rdatatype = 'A'
    count = 30
    timeout = 2
    dnsserver = None
    dest_port = 53
    src_ip = None
    hops = 0
    proto = PROTO_UDP
    as_lookup = False
    expert_mode = False
    should_resolve = True
    use_edns = False
    color_mode = False

    args = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "aqhc:s:S:t:w:p:nexCT",
                                   ["help", "count=", "server=", "quiet", "type=", "wait=", "asn", "port", "expert",
                                    "color", "srcip=", "tcp"])
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
        elif o in ("-C", "--color"):
            color_mode = True
        elif o in "-n":
            should_resolve = False
        elif o in ("-T", "--tcp"):
            proto = PROTO_TCP
        elif o in ("-a", "--asn"):
            as_lookup = True
        elif o in ("-e", "--edns"):
            use_edns = True
        else:
            usage()

    color = Colors(color_mode)

    # validate RR type
    if not util.dns.valid_rdatatype(rdatatype):
        print('Error: Invalid record type "%s" ' % rdatatype)
        sys.exit(1)

    # Use system DNS server if parameter is not specified
    # remember not all systems have /etc/resolv.conf (i.e. Android)
    if dnsserver is None:
        dnsserver = dns.resolver.get_default_resolver().nameservers[0]

    # check if we have a valid dns server address
    try:
        ipaddress.ip_address(dnsserver)
    except ValueError:  # so it is not a valid IPv4 or IPv6 address, so try to resolve host name
        try:
            dnsserver = socket.getaddrinfo(dnsserver, port=None, family=socket.AF_INET)[1][4][0]
        except OSError:
            print('Error: cannot resolve hostname:', dnsserver)
            sys.exit(1)

    icmp = socket.getprotobyname('icmp')

    ttl = 1
    reached = False
    trace_path = []

    if not quiet:
        print("%s DNS: %s:%d, hostname: %s, rdatatype: %s" % (__progname__, dnsserver, dest_port, qname, rdatatype),
              flush=True)

    while True:

        # some platforms permit opening a DGRAM socket for ICMP without root permission
        # if not availble, we will fall back to RAW which explicitly requires root permission
        try:
            icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
        except OSError:
            try:
                icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, icmp)
            except OSError:
                print("Error: Unable to create ICMP socket with unprivileged user. Please run as root.")
                sys.exit(1)

        icmp_socket.bind(("", dest_port))
        icmp_socket.settimeout(timeout)

        curr_addr = None

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:  # dispatch dns lookup to another thread
            stime = time.perf_counter()
            thr = pool.submit(ping, qname, dnsserver, rdatatype, proto, dest_port, ttl, timeout, src_ip=src_ip,
                              use_edns=use_edns)

            try:  # expect ICMP response
                packet, curr_addr = icmp_socket.recvfrom(512)
                if len(packet) > 51:
                    icmp_type = packet[20]
                    l4_dst_port = packet[50] << 8 | packet[51]
                    if icmp_type == 11 and l4_dst_port == dest_port:
                        curr_addr = curr_addr[0]
                    else:
                        curr_addr = None
            except socket.error:
                pass
            except SystemExit:
                shutdown = True
                break
            finally:
                etime = time.perf_counter()
                icmp_socket.close()

        reached, resp_time = thr.result()

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
            except SystemExit:
                pass
            except Exception:
                print("unxpected error: ", sys.exc_info()[0])

        global whois_cache
        if curr_addr:
            as_name = ""
            if as_lookup:
                asn, whois_cache = util.whois.asn_lookup(curr_addr, whois_cache)
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
        whois_cache = util.whois.restore()
        main()
    finally:
        util.whois.save(whois_cache)
