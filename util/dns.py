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
import random
import signal
import socket
import sys
from statistics import stdev

import httpx
import dns.flags
import dns.message
import dns.query
import dns.rcode
import dns.rdataclass
import string

shutdown = False

# Transport protocols
PROTO_UDP = 0
PROTO_TCP = 1
PROTO_TLS = 2
PROTO_HTTPS = 3
PROTO_QUIC = 4

_TTL = None


class PingResponse:
    def __init__(self):
        self.r_avg = 0
        self.r_min = 0
        self.r_max = 0
        self.r_stddev = 0
        self.r_lost_percent = 0
        self.flags = 0
        self.ttl = None
        self.answer = None
        self.rcode = 0
        self.rcode_text = ''


def proto_to_text(proto):
    _proto_name = {
        PROTO_UDP: 'UDP',
        PROTO_TCP: 'TCP',
        PROTO_TLS: 'TLS',
        PROTO_HTTPS: 'HTTPS',
        PROTO_QUIC: 'QUIC',
    }
    return _proto_name[proto]


def getDefaultPort(proto):
    _proto_port = {
        PROTO_UDP: 53,
        PROTO_TCP: 53,
        PROTO_TLS: 853,  # RFC 7858, Secion 3.1
        PROTO_HTTPS: 443,
        PROTO_QUIC: 853,  # RFC 9250, Section 4.1.1
    }
    return _proto_port[proto]


class CustomSocket(socket.socket):
    def __init__(self, *args, **kwargs):
        super(CustomSocket, self).__init__(*args, **kwargs)
        if _TTL:
            self.setsockopt(socket.SOL_IP, socket.IP_TTL, _TTL)


def ping(qname, server, dst_port, rdtype, timeout, count, proto, src_ip, use_edns=False, force_miss=False,
         want_dnssec=False, socket_ttl=None):
    retval = PingResponse()
    retval.rcode_text = "No Response"

    response_times = []
    i = 0

    if socket_ttl:
        global _TTL
        _TTL = socket_ttl
        dns.query.socket_factory = CustomSocket

    for i in range(count):

        if shutdown:  # user pressed CTRL+C
            raise SystemExit

        if force_miss:
            fqdn = "_dnsdiag_%s_.%s" % (random_string(), qname)
        else:
            fqdn = qname

        if use_edns:
            query = dns.message.make_query(fqdn, rdtype, dns.rdataclass.IN, use_edns, want_dnssec, payload=1232)
        else:
            query = dns.message.make_query(fqdn, rdtype, dns.rdataclass.IN, use_edns=False, want_dnssec=False)

        try:
            if proto is PROTO_UDP:
                response = dns.query.udp(query, server, timeout=timeout, port=dst_port, source=src_ip,
                                         ignore_unexpected=True)
            elif proto is PROTO_TCP:
                response = dns.query.tcp(query, server, timeout=timeout, port=dst_port, source=src_ip)
            elif proto is PROTO_TLS:
                if hasattr(dns.query, 'tls'):
                    response = dns.query.tls(query, server, timeout, dst_port, src_ip)
                else:
                    unsupported_feature()
            elif proto is PROTO_HTTPS:
                if hasattr(dns.query, 'https'):
                    response = dns.query.https(query, server, timeout, dst_port, src_ip)
                else:
                    unsupported_feature()

        except (httpx.ConnectTimeout, httpx.ReadTimeout,
                httpx.ConnectError):
            raise ConnectionError('Connection failed')
        except ValueError:
            retval.rcode_text = "Invalid Response"
            break
        except dns.exception.Timeout:
            break
        except OSError as e:
            if socket_ttl:  # this is an acceptable error while doing traceroute
                break
            print("error: %s" % e.strerror, file=sys.stderr, flush=True)
            raise OSError(e)
        except Exception as e:
            print("error: %s" % e, file=sys.stderr, flush=True)
            break
        else:
            # convert time to milliseconds, considering that
            # time property is retruned differently by query.https
            if type(response.time) is datetime.timedelta:
                elapsed = response.time.total_seconds() * 1000
            else:
                elapsed = response.time * 1000
            response_times.append(elapsed)
            if response:
                retval.flags = response.flags
                retval.answer = response.answer
                retval.rcode = response.rcode()
                retval.rcode_text = dns.rcode.to_text(response.rcode())
                if len(response.answer) > 0:
                    retval.ttl = response.answer[0].ttl

    r_sent = i + 1
    r_received = len(response_times)
    retval.r_lost_count = r_sent - r_received
    retval.r_lost_percent = (100 * retval.r_lost_count) / r_sent
    if response_times:
        retval.r_min = min(response_times)
        retval.r_max = max(response_times)
        retval.r_avg = sum(response_times) / r_received
        if len(response_times) > 1:
            retval.r_stddev = stdev(response_times)
        else:
            retval.r_stddev = 0
    else:
        retval.r_min = 0
        retval.r_max = 0
        retval.r_avg = 0
        retval.r_stddev = 0

    return retval


def random_string(min_length=5, max_length=10):
    char_set = string.ascii_letters + string.digits
    length = random.randint(min_length, max_length)
    return ''.join(map(lambda unused: random.choice(char_set), range(length)))


def signal_handler(sig, frame):
    global shutdown
    if shutdown:  # pressed twice, so exit immediately
        sys.exit(0)
    shutdown = True  # pressed once, exit gracefully


def unsupported_feature(feature=""):
    print("Error: You have an unsupported version of Python interpreter dnspython library.")
    print("       Some features such as DoT and DoH are not available. You should upgrade")
    print("       the Python interpreter to at least 3.7 and reinstall dependencies.")
    if feature:
        print("Missing Feature: %s" % feature)
    sys.exit(127)


def valid_rdatatype(rtype):
    # validate RR type
    try:
        _ = dns.rdatatype.from_text(rtype)
    except dns.rdatatype.UnknownRdatatype:
        return False
    return True


def flags_to_text(flags):
    # Standard DNS flags

    QR = 0x8000
    AA = 0x0400
    TC = 0x0200
    RD = 0x0100
    RA = 0x0080
    AD = 0x0020
    CD = 0x0010

    # EDNS flags
    # DO = 0x8000

    _by_text = {
        'QR': QR,
        'AA': AA,
        'TC': TC,
        'RD': RD,
        'RA': RA,
        'AD': AD,
        'CD': CD
    }

    _by_value = dict([(y, x) for x, y in _by_text.items()])
    # _flags_order = sorted(_by_value.items(), reverse=True)

    _by_value = dict([(y, x) for x, y in _by_text.items()])

    order = sorted(_by_value.items(), reverse=True)
    text_flags = []
    for k, v in order:
        if flags & k != 0:
            text_flags.append(v)
        else:
            text_flags.append('--')

    return ' '.join(text_flags)


def setup_signal_handler():
    try:
        signal.signal(signal.SIGTSTP, signal.SIG_IGN)  # ignore CTRL+Z
        signal.signal(signal.SIGINT, signal_handler)  # custom CTRL+C handler
    except AttributeError:  # not all signals are supported on all platforms
        pass
