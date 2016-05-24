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
import ipaddress
import os
import signal
import socket
import sys

import dns.flags
import dns.rdatatype
import dns.resolver

__VERSION__ = 1.1
__PROGNAME__ = os.path.basename(sys.argv[0])
shutdown = False


def usage():
    print("""%s version %1.1f
usage: %s [-h] [-q] [-v] [-s server] [-p port] [-P port] [-S address] [-c count] [-t type] [-w wait] hostname
  -h  --help      Show this help
  -q  --quiet     Quiet
  -v  --verbose   Print actual dns response
  -s  --server    DNS server to use (default: first entry from /etc/resolv.conf)
  -p  --port      DNS server port number (default: 53)
  -T  --tcp       Use TCP instead of UDP
  -4  --ipv4      Use IPv4 as default network protocol
  -6  --ipv6      Use IPv6 as default network protocol
""" % (__PROGNAME__, __VERSION__, __PROGNAME__))
    sys.exit(0)


class myResolver(dns.resolver.Resolver):
    def __init__(self, nameservers=None, port=53, af=socket.AF_INET, use_tcp=False):
        super(myResolver, self).__init__()
        self.use_tcp = use_tcp
        self.port = port
        self.default_af = af
        self.port = port
        self.retry_servfail = 0
        resolved_nameservers = []
        for n in nameservers:
            try:
                ipaddress.ip_address(n)
            except ValueError:  # so it is not a valid IPv4 or IPv6 address, so try to resolve host name
                try:
                    r = socket.getaddrinfo(n, port=None, family=self.default_af)[1][4][0]
                except OSError:
                    print('Error: cannot resolve hostname:', n)
                    sys.exit(1)
                else:
                    resolved_nameservers.append(r)

            else:
                resolved_nameservers.append(n)

        self.nameservers = resolved_nameservers

    def lookupA(self, hostname):
        try:
            answers = self.query(hostname, 'A', tcp=self.use_tcp, af=self.default_af,
                                 raise_on_no_answer=False)
        except Exception as e:
            print(e)
            pass

        else:
            a = []
            for t in answers:
                a.append(t.address)
            return a

        return []

    def lookupAAAA(self, hostname):
        try:
            answers = self.query(hostname, 'AAAA', tcp=self.use_tcp, af=self.default_af,
                                 raise_on_no_answer=False)
        except:
            pass

        else:
            a = []
            try:
                for t in answers:
                    a.append(t.address)
                return a
            except:
                return []

        return []

    def lookupNSRecords(self, hostname):
        try:
            answers = self.query(hostname, 'NS', tcp=self.use_tcp, af=self.default_af,
                                 raise_on_no_answer=False)
        except:
            pass

        else:
            return answers


def signal_handler(sig, frame):
    global shutdown
    if shutdown:  # pressed twice, so exit immediately
        sys.exit(0)
    shutdown = True  # pressed once, exit gracefully


def printHeader(title):
    print("\n>> %s" % title)
    print('=' * 65)


def validHostname(hostname):
    return True  # placeholder


def main():
    try:
        signal.signal(signal.SIGTSTP, signal.SIG_IGN)  # ignore CTRL+Z
        signal.signal(signal.SIGINT, signal_handler)  # custom CTRL+C handler
    except AttributeError:  # OS Does not support some signals, probably windows
        pass

    if len(sys.argv) == 1:
        usage()

    # defaults
    quiet = False
    verbose = False
    dnsserver = dns.resolver.get_default_resolver().nameservers[0]
    dst_port = 53
    use_tcp = False
    address_family = socket.AF_INET
    default_parent = 'a.gtld-servers.net'

    try:
        opts, args = getopt.getopt(sys.argv[1:], "qhs:vp:T46",
                                   ["help", "server=", "quiet", "verbose",
                                    "port=", "srcip=", "tcp", "ipv4", "ipv6"])
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
        elif o in ("-v", "--verbose"):
            verbose = True
        elif o in ("-s", "--server"):
            dnsserver = a
        elif o in ("-p", "--port"):
            dst_port = int(a)
        elif o in ("-q", "--quiet"):
            quiet = True
            verbose = False
        elif o in ("-T", "--tcp"):
            use_tcp = True
        elif o in ("-4", "--ipv4"):
            address_family = socket.AF_INET
        elif o in ("-6", "--ipv6"):
            address_family = socket.AF_INET6
        else:
            usage()

    # check if we have a valid hostname to evaluate
    if not validHostname(hostname):
        print("Invalid hostname:", hostname)
        exit(1)

    # check if a valid DNS Server is provided
    try:
        ipaddress.ip_address(dnsserver)
    except ValueError:  # so it is not a valid IPv4 or IPv6 address, so try to resolve host name
        try:
            dnsserver = socket.getaddrinfo(dnsserver, port=None, family=address_family)[1][4][0]
        except OSError:
            print('Error: cannot resolve hostname:', dnsserver)
            sys.exit(1)

    res = myResolver(nameservers=[default_parent], port=dst_port, af=address_family, use_tcp=use_tcp)

    printHeader("Domain NS Records (from parent: %s)" % default_parent)
    answers = res.lookupNSRecords(hostname)
    for a in answers:
        A = res.lookupA(a.target)
        AAAA = res.lookupAAAA(a.target)
        print("%-25s\t%s\t%s" % (a.target, '\t'.join(A), '\t'.join(AAAA)))


        # try:
        #     answers = resolver.query(hostname, dnsrecord, source_port=src_port, source=src_ip, tcp=use_tcp, af=address_family,
        #                              raise_on_no_answer=False)
        # except dns.resolver.NoNameservers as e:
        #     if not quiet:
        #         print("No response to dns request")
        #         if verbose:
        #             print("error:", e)
        #     sys.exit(1)
        # except dns.resolver.NXDOMAIN as e:
        #     if not quiet:
        #         print("Hostname does not exist")
        #     if verbose:
        #         print("Error:", e)
        #     sys.exit(1)
        # except dns.resolver.Timeout:
        #     if not quiet:
        #         print("Request timeout")
        #     pass
        # except dns.resolver.NoAnswer:
        #     if not quiet:
        #         print("No answer")
        #     pass
        # else:
        #     if verbose:
        #         print(answers.rrset)
        #         print("flags:", dns.flags.to_text(answers.response.flags))


if __name__ == '__main__':
    main()
