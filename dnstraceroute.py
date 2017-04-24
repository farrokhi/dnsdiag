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


import concurrent.futures
import getopt
import ipaddress
import os
import pickle
import signal
import socket
import sys
import time

import dns.query
import dns.rdatatype
import dns.resolver

from cymruwhois import cymruwhois

__author__ = 'Babak Farrokhi (babak@farrokhi.net)'
__license__ = 'BSD'
__version__ = "1.6.0"
_ttl = None
quiet = False


class CustomSocket(socket.socket):
    def __init__(self, *args, **kwargs):
        super(CustomSocket, self).__init__(*args, **kwargs)

    def sendto(self, *args, **kwargs):
        global _ttl
        if _ttl:
            self.setsockopt(socket.SOL_IP, socket.IP_TTL, _ttl)
        super(CustomSocket, self).sendto(*args, **kwargs)


def test_import():
    #  passing this test means imports were successful
    pass


# Constants
__progname__ = os.path.basename(sys.argv[0])
WHOIS_CACHE = 'whois.cache'


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


# Globarl Variables
shutdown = False


def whoisrecord(ip):
    try:
        currenttime = time.perf_counter()
        ts = currenttime
        if ip in whois:
            asn, ts = whois[ip]
        else:
            ts = 0
        if (currenttime - ts) > 36000:
            c = cymruwhois.Client()
            asn = c.lookup(ip)
            whois[ip] = (asn, currenttime)
        return asn
    except Exception as e:
        return e


try:
    pkl_file = open(WHOIS_CACHE, 'rb')
    try:
        whois = pickle.load(pkl_file)
    except EOFError:
        whois = {}
except IOError:
    whois = {}


def usage():
    print('%s version %s\n' % (__progname__, __version__))
    print('usage: %s [-aeqhCx] [-s server] [-p port] [-c count] [-t type] [-w wait]  hostname' % __progname__)
    print('  -h  --help      Show this help')
    print('  -q  --quiet     Quiet')
    print('  -x  --expert    Print expert hints if available')
    print('  -a  --asn       Turn on AS# lookups for each hop encountered')
    print('  -s  --server    DNS server to use (default: first system resolver)')
    print('  -p  --port      DNS server port number (default: 53)')
    print('  -c  --count     Maximum number of hops (default: 30)')
    print('  -w  --wait      Maximum wait time for a reply (default: 2)')
    print('  -t  --type      DNS request record type (default: A)')
    print('  -C  --color     Print colorful output')
    print('  -e  --edns      Disable EDNS0 (Default: Enabled)')
    print('  ')
    sys.exit()


def signal_handler(sig, frame):
    global shutdown
    if shutdown:  # pressed twice, so exit immediately
        sys.exit(0)
    shutdown = True  # pressed once, exit gracefully


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


def ping(resolver, hostname, dnsrecord, ttl, use_edns=False):
    global _ttl

    reached = False

    dns.query.socket_factory = CustomSocket
    _ttl = ttl
    if use_edns:
        resolver.use_edns(edns=0, payload=8192, ednsflags=dns.flags.edns_from_text('DO'))

    try:
        resolver.query(hostname, dnsrecord, raise_on_no_answer=False)

    except dns.resolver.NoNameservers as e:
        if not quiet:
            print("no or bad response:", e)
        sys.exit(1)
    except dns.resolver.NXDOMAIN as e:
        if not quiet:
            print("Invalid hostname:", e)
        sys.exit(1)
    except dns.resolver.Timeout:
        pass
    except dns.resolver.NoAnswer:
        if not quiet:
            print("invalid answer")
        pass
    except SystemExit:
        pass
    except Exception as e:
        print("unxpected error: ", e)
        sys.exit(1)
    else:
        reached = True

    return reached


def main():
    global quiet

    try:
        signal.signal(signal.SIGTSTP, signal.SIG_IGN)  # ignore CTRL+Z
        signal.signal(signal.SIGINT, signal_handler)  # custom CTRL+C handler
    except AttributeError:  # not all signals are supported on all platforms
        pass

    if len(sys.argv) == 1:
        usage()

    dnsrecord = 'A'
    count = 30
    timeout = 2
    dnsserver = dns.resolver.get_default_resolver().nameservers[0]
    dest_port = 53
    hops = 0
    as_lookup = False
    expert_mode = False
    should_resolve = True
    use_edns = True
    color_mode = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], "aqhc:s:t:w:p:nexC",
                                   ["help", "count=", "server=", "quiet", "type=", "wait=", "asn", "port", "expert",
                                    "color"])
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
        elif o in ("-x", "--expert"):
            expert_mode = True
        elif o in ("-s", "--server"):
            dnsserver = a
        elif o in ("-q", "--quiet"):
            quiet = True
        elif o in ("-w", "--wait"):
            timeout = int(a)
        elif o in ("-t", "--type"):
            dnsrecord = a
        elif o in ("-p", "--port"):
            dest_port = int(a)
        elif o in ("-C", "--color"):
            color_mode = True
        elif o in ("-n"):
            should_resolve = False
        elif o in ("-a", "--asn"):
            as_lookup = True
        elif o in ("-e", "--edns"):
            use_edns = False
        else:
            usage()

    color = Colors(color_mode)

    # check if we have a valid dns server address
    try:
        ipaddress.ip_address(dnsserver)
    except ValueError:  # so it is not a valid IPv4 or IPv6 address, so try to resolve host name
        try:
            dnsserver = socket.getaddrinfo(dnsserver, port=None, family=socket.AF_INET)[1][4][0]
        except OSError:
            print('Error: cannot resolve hostname:', dnsserver)
            sys.exit(1)

    resolver = dns.resolver.Resolver()
    resolver.nameservers = [dnsserver]
    resolver.timeout = timeout
    resolver.lifetime = timeout
    resolver.retry_servfail = 0

    icmp = socket.getprotobyname('icmp')

    ttl = 1
    reached = False
    trace_path = []

    if not quiet:
        print("%s DNS: %s:%d, hostname: %s, rdatatype: %s" % (__progname__, dnsserver, dest_port, hostname, dnsrecord),
              flush=True)

    while True:
        if shutdown:
            break

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
        curr_host = None

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:  # dispatch dns lookup to another thread
            stime = time.perf_counter()
            thr = pool.submit(ping, resolver, hostname, dnsrecord, ttl, use_edns=use_edns)

            try:  # expect ICMP response
                _, curr_addr = icmp_socket.recvfrom(512)
                curr_addr = curr_addr[0]
            except socket.error:
                etime = time.perf_counter()
                pass
            finally:
                etime = time.perf_counter()
                icmp_socket.close()

        reached = thr.result()

        if reached:
            curr_addr = dnsserver
            stime = time.perf_counter()  # need to recalculate elapsed time for last hop without waiting for an icmp error reply
            ping(resolver, hostname, dnsrecord, ttl, use_edns=use_edns)
            etime = time.perf_counter()

        elapsed = abs(etime - stime) * 1000  # convert to milliseconds

        if should_resolve:
            try:
                if curr_addr:
                    curr_name = socket.gethostbyaddr(curr_addr)[0]
            except socket.error:
                curr_name = curr_addr
            except SystemExit:
                pass
            except:
                print("unxpected error: ", sys.exc_info()[0])
        else:
            curr_name = curr_addr

        if curr_addr:
            as_name = ""
            if as_lookup:
                asn = whoisrecord(curr_addr)
                as_name = ''
                try:
                    if asn and asn.asn != "NA":
                        as_name = "[%s %s] " % (asn.asn, asn.owner)
                except AttributeError:
                    if shutdown:
                        sys.exit(0)
                    pass

            c = color.N  # default
            if curr_addr != '*':
                IP = ipaddress.ip_address(curr_addr)
                if IP.is_private:
                    c = color.R
                if IP.is_reserved:
                    c = color.B
                if curr_addr == dnsserver:
                    c = color.G

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
        main()
    finally:
        pkl_file = open(WHOIS_CACHE, 'wb')
        pickle.dump(whois, pkl_file)
