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
import signal
import sys
import socket
import time

import dns.rdatatype
import dns.resolver

__VERSION__ = 1.0
__PROGNAME__ = sys.argv[0]
should_stop = False


def usage():
    print('%s version %1.1f\n' % (__PROGNAME__, __VERSION__))
    print('syntax: %s [-h] [-q] [-s server] [-c count] [-t type] [-w wait] hostname' % __PROGNAME__)
    print('  -h  --help      show this help')
    print('  -q  --quiet     quiet')
    print('  -s  --server    dns server to use (default: 8.8.8.8)')
    print('  -c  --count     maximum number of hops (default: 30)')
    print('  -w  --wait      maximum wait time for a reply (default: 5)')
    print('  -t  --type      DNS request record type (default: A)')
    print('  ')
    exit()


def signal_handler(sig, frame):
    global should_stop
    if should_stop:  # pressed twice, so exit immediately
        exit(0)
    should_stop = True  # pressed once, exit gracefully


def main():
    signal.signal(signal.SIGTSTP, signal.SIG_IGN)  # ignore CTRL+Z
    signal.signal(signal.SIGINT, signal_handler)  # custom CTRL+C handler

    if len(sys.argv) == 1:
        usage()

    dnsrecord = 'A'
    count = 30
    timeout = 1
    quiet = False
    dnsserver = '8.8.8.8'
    hostname = 'wikipedia.org'
    dnsport = 53
    hops = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:], "qhc:s:t:w:",
                                   ["help", "output=", "count=", "server=", "quiet", "type=", "wait="])
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
        else:
            usage()

    resolver = dns.resolver.Resolver()
    resolver.nameservers = [dnsserver]
    resolver.timeout = timeout
    resolver.lifetime = timeout
    resolver.retry_servfail = 0

    icmp = socket.getprotobyname('icmp')

    response_time = []
    i = 0
    ttl = 1
    reached = False

    print("%s %s: hostname=%s rdatatype=%s" % (__PROGNAME__, dnsserver, hostname, dnsrecord))

    while True:
        if should_stop:
            break

        icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
        icmp_socket.bind(("", dnsport))
        icmp_socket.settimeout(timeout)

        try: # send DNS request
            stime = time.time()
            answers = resolver.query(hostname, dnsrecord, ipttl = ttl)
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
        except:
            print("unxpected error: ", sys.exc_info()[0])
            exit(1)
        else:
            reached = True

        curr_addr = None
        curr_host = None

        try: # expect ICMP response
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

        try:
            if curr_addr:
                curr_name = socket.gethostbyaddr(curr_addr)[0]
        except socket.error:
            curr_name = curr_addr
        except:
            print("unxpected error: ", sys.exc_info()[0])

        if curr_addr:
            print("%d\t%s (%s)  %d ms" % (ttl, curr_name, curr_addr, elapsed))
        else:
            print("%d\t *" % ttl) 

        ttl += 1
        hops += 1
        if (hops >= count) or (curr_addr == dnsserver) or reached:
            break

if __name__ == '__main__':
    main()
