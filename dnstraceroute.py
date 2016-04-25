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


import getopt
import os
import signal
import socket
import sys
import time

import dns.rdatatype
import dns.resolver

# http://pythonhosted.org/cymruwhois/
try:
    import cymruwhois

    has_whois = True
except ImportError:
    has_whois = False

# Constants
__VERSION__ = 1.1
__PROGNAME__ = os.path.basename(sys.argv[0])
WHOIS_CACHE = 'whois.cache'

# Globarl Variables
should_stop = False

if has_whois:
    from cymruwhois import cymruwhois
    import pickle


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
    print('%s version %1.1f\n' % (__PROGNAME__, __VERSION__))
    print('usage: %s [-h] [-q] [-a] [-s server] [-p port] [-c count] [-t type] [-w wait] hostname' % __PROGNAME__)
    print('  -h  --help      Show this help')
    print('  -q  --quiet     Quiet')
    print('  -a  --asn       Turn on AS# lookups for each hop encountered')
    print('  -s  --server    DNS server to use (default: first system resolver)')
    print('  -p  --port      DNS server port number (default: 53)')
    print('  -c  --count     Maximum number of hops (default: 30)')
    print('  -w  --wait      Maximum wait time for a reply (default: 5)')
    print('  -t  --type      DNS request record type (default: A)')
    print('  ')
    exit()


def signal_handler(sig, frame):
    global should_stop
    if should_stop:  # pressed twice, so exit immediately
        exit(0)
    should_stop = True  # pressed once, exit gracefully


def main():
    try:
        signal.signal(signal.SIGTSTP, signal.SIG_IGN)  # ignore CTRL+Z
        signal.signal(signal.SIGINT, signal_handler)  # custom CTRL+C handler
    except AttributeError: # not all signals are supported on all platforms
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
    should_resolve = True

    try:
        opts, args = getopt.getopt(sys.argv[1:], "aqhc:s:t:w:p:n",
                                   ["help", "count=", "server=", "quiet", "type=", "wait=", "asn", "port"])
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
        elif o in ("-n"):
            should_resolve = False
        elif o in ("-a", "--asn"):
            if has_whois:
                as_lookup = True
            else:
                print('Warning: cymruwhois module cannot be loaded. AS Lookup disabled.')
        else:
            usage()

    resolver = dns.resolver.Resolver()
    resolver.nameservers = [dnsserver]
    resolver.timeout = timeout
    resolver.lifetime = timeout
    resolver.retry_servfail = 0

    icmp = socket.getprotobyname('icmp')

    ttl = 1
    reached = False

    if not quiet:
        print("%s DNS: %s:%d, hostname: %s, rdatatype: %s" % (__PROGNAME__, dnsserver, dest_port, hostname, dnsrecord))

    while True:
        if should_stop:
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
                exit(1)

        icmp_socket.bind(("", dest_port))
        icmp_socket.settimeout(timeout)

        try:  # send DNS request
            stime = time.time()
            resolver.query(hostname, dnsrecord, ipttl=ttl)
        except dns.resolver.NoNameservers as e:
            if not quiet:
                print("no or bad response:", e)
            exit(1)
        except dns.resolver.NXDOMAIN as e:
            if not quiet:
                print("Invalid hostname:", e)
            exit(1)
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
            exit(1)
        else:
            reached = True

        curr_addr = None
        curr_host = None

        try:  # expect ICMP response
            _, curr_addr = icmp_socket.recvfrom(512)
            curr_addr = curr_addr[0]

        except socket.error:
            pass

        finally:
            icmp_socket.close()

        etime = time.time()
        elapsed = (etime - stime) * 1000  # convert to milliseconds

        if reached:
            curr_addr = dnsserver

        elapsed -= timeout * 1000

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
            if has_whois and as_lookup:
                ASN = whoisrecord(curr_addr)
                as_name = ''
                try:
                    if ASN and ASN.asn != "NA":
                        as_name = "[%s %s] " % (ASN.asn, ASN.owner)
                except AttributeError:
                    if should_stop:
                        exit(0)
                    pass

            print("%d\t%s (%s) %s%d ms" % (ttl, curr_name, curr_addr, as_name, elapsed))
        else:
            print("%d\t *" % ttl)

        ttl += 1
        hops += 1
        if (hops >= count) or (curr_addr == dnsserver) or reached:
            break


if __name__ == '__main__':
    try:
        main()
    finally:
        if has_whois:
            pkl_file = open(WHOIS_CACHE, 'wb')
            pickle.dump(whois, pkl_file)
