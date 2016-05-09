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

import dns.rdatatype
import dns.resolver
from cymruwhois import cymruwhois

__author__ = 'Babak Farrokhi (babak@farrokhi.net)'
__license__ = 'BSD'
__version__ = 1.3


def test_import():
    #  passing this test means imports were successful
    pass


# Constants
__PROGNAME__ = os.path.basename(sys.argv[0])
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
        currenttime = time.time()
        ts = currenttime
        if ip in whois:
            ASN, ts = whois[ip]
        else:
            ts = 0
        if ((currenttime - ts) > 36000):
            c = cymruwhois.Client()
            ASN = c.lookup(ip)
            whois[ip] = (ASN, currenttime)
        return ASN
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
    print('%s version %1.1f\n' % (__PROGNAME__, __version__))
    print('usage: %s [-h] [-q] [-a] [-s server] [-p port] [-c count] [-t type] [-w wait] hostname' % __PROGNAME__)
    print('  -h  --help      Show this help')
    print('  -q  --quiet     Quiet')
    print('  -e  --expert    Print expert hints if available')
    print('  -a  --asn       Turn on AS# lookups for each hop encountered')
    print('  -s  --server    DNS server to use (default: first system resolver)')
    print('  -p  --port      DNS server port number (default: 53)')
    print('  -c  --count     Maximum number of hops (default: 30)')
    print('  -w  --wait      Maximum wait time for a reply (default: 5)')
    print('  -t  --type      DNS request record type (default: A)')
    print('  -C  --color     Print colorful output')
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

    prev_hop = None
    if len(trace_path) > 1:
        prev_hop = trace_path[-2]

    if len(trace_path) < 2:
        print(
            " %s[*]%s path too short (possible DNS hijacking, unless it is a local DNS resolver)" % (color.R, color.N))
        return

    if prev_hop == '*':
        print(" %s[*]%s public DNS server is next to an invisible hop (probably a firewall)" % (color.R, color.N))
        return

    if prev_hop and ipaddress.ip_address(prev_hop).is_private:
        print(" %s[*]%s public DNS server is next to a private IP address (possible hijacking)" % (color.R, color.N))
        return

    if prev_hop and ipaddress.ip_address(prev_hop).is_reserved:
        print(" %s[*]%s public DNS server is next to a reserved IP address (possible hijacking)" % (color.R, color.N))
        return

    ## no expert info available
    print(" %s[*]%s No expert hint available for this trace" % (color.G, color.N))


def ping(resolver, hostname, dnsrecord, ttl):
    reached = False

    try:
        resolver.query(hostname, dnsrecord, ipttl=ttl)

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
    except:
        print("unxpected error: ", sys.exc_info()[0])
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
    timeout = 1
    quiet = False
    dnsserver = dns.resolver.get_default_resolver().nameservers[0]
    dest_port = 53
    hops = 0
    as_lookup = False
    expert_mode = False
    should_resolve = True
    color_mode = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], "aqhc:s:t:w:p:neC",
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
        elif o in ("-e", "--expert"):
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
        else:
            usage()

    color = Colors(color_mode)

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
        print("%s DNS: %s:%d, hostname: %s, rdatatype: %s" % (__PROGNAME__, dnsserver, dest_port, hostname, dnsrecord))

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
            stime = time.time()
            thr = pool.submit(ping, resolver, hostname, dnsrecord, ttl)

            try:  # expect ICMP response
                _, curr_addr = icmp_socket.recvfrom(512)
                curr_addr = curr_addr[0]
            except socket.error:
                etime = time.time()
                pass
            finally:
                etime = time.time()
                icmp_socket.close()

        reached = thr.result()

        if reached:
            curr_addr = dnsserver
            stime = time.time()  # need to recalculate elapsed time for last hop without waiting for an icmp error reply
            ping(resolver, hostname, dnsrecord, ttl)
            etime = time.time()

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
                ASN = whoisrecord(curr_addr)
                as_name = ''
                try:
                    if ASN and ASN.asn != "NA":
                        as_name = "[%s %s] " % (ASN.asn, ASN.owner)
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

            print("%d\t%s (%s%s%s) %s%d ms" % (ttl, curr_name, c, curr_addr, color.N, as_name, elapsed), flush=True)
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
