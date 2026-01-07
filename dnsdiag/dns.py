#!/usr/bin/env python3
#
# Copyright (c) 2016-2026, Babak Farrokhi
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
import errno
import socket
from statistics import stdev
from typing import Optional, List, Any

import httpx
import dns.edns
import dns.message
import dns.query
import dns.rcode
import dns.rdataclass

from dnsdiag.shared import random_string, err, unsupported_feature

# Transport protocols
PROTO_UDP: int = 0
PROTO_TCP: int = 1
PROTO_TLS: int = 2
PROTO_HTTPS: int = 3
PROTO_QUIC: int = 4
PROTO_HTTP3: int = 5

_TTL: Optional[int] = None


class PingResponse:
    def __init__(self) -> None:
        self.r_avg: float = 0.0
        self.r_min: float = 0.0
        self.r_max: float = 0.0
        self.r_stddev: float = 0.0
        self.r_lost_percent: float = 0.0
        self.flags: int = 0
        self.ednsflags: int = 0
        self.ttl: Optional[int] = None
        self.answer: Optional[Any] = None
        self.rcode: int = 0
        self.rcode_text: str = ''
        self.response: Optional[Any] = None


def proto_to_text(proto: int) -> str:
    _proto_name = {
        PROTO_UDP: 'UDP',
        PROTO_TCP: 'TCP',
        PROTO_TLS: 'TLS',
        PROTO_HTTPS: 'HTTPS',
        PROTO_QUIC: 'QUIC',
        PROTO_HTTP3: 'HTTP3',
    }
    return _proto_name[proto]


def get_default_port(proto: int) -> int:
    _proto_port = {
        PROTO_UDP: 53,
        PROTO_TCP: 53,
        PROTO_TLS: 853,  # RFC 7858, Secion 3.1
        PROTO_HTTPS: 443,
        PROTO_QUIC: 853,  # RFC 9250, Section 4.1.1
        PROTO_HTTP3: 443,
    }
    return _proto_port[proto]


class CustomSocket(socket.socket):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super(CustomSocket, self).__init__(*args, **kwargs)
        if _TTL:
            # Set TTL/hop limit based on address family
            if self.family == socket.AF_INET:
                self.setsockopt(socket.SOL_IP, socket.IP_TTL, _TTL)
            elif self.family == socket.AF_INET6:
                self.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_UNICAST_HOPS, _TTL)


def ping(qname: str, server: str, dst_port: int, rdtype: str, timeout: float, count: int, proto: int,
         src_ip: Optional[str], use_edns: bool = False, force_miss: bool = False,
         want_dnssec: bool = False, want_nsid: bool = False, socket_ttl: Optional[int] = None) -> PingResponse:
    retval = PingResponse()
    retval.rcode_text = "No Response"

    response_times: List[float] = []

    if socket_ttl:
        global _TTL
        _TTL = socket_ttl
        dns.query.socket_factory = CustomSocket

    for i in range(count):

        if force_miss:
            fqdn = "_dnsdiag_%s_.%s" % (random_string(), qname)
        else:
            fqdn = qname

        if use_edns:
            edns_options: List[dns.edns.Option] = []
            if want_nsid:
                edns_options.append(dns.edns.GenericOption(dns.edns.NSID, b''))
            query = dns.message.make_query(fqdn, rdtype, dns.rdataclass.IN, use_edns, want_dnssec, payload=1232,
                                           options=edns_options if edns_options else None)
        else:
            query = dns.message.make_query(fqdn, rdtype, dns.rdataclass.IN, use_edns=False, want_dnssec=False)

        try:
            if proto == PROTO_UDP:
                response = dns.query.udp(query, server, timeout=timeout, port=dst_port, source=src_ip,
                                         ignore_unexpected=True)
            elif proto == PROTO_TCP:
                response = dns.query.tcp(query, server, timeout=timeout, port=dst_port, source=src_ip)
            elif proto == PROTO_TLS:
                if hasattr(dns.query, 'tls'):
                    response = dns.query.tls(query, server, timeout, dst_port, src_ip)
                else:
                    unsupported_feature()
            elif proto == PROTO_HTTPS:
                if hasattr(dns.query, 'https'):
                    response = dns.query.https(query, server, timeout, dst_port, src_ip,
                                              http_version=dns.query.HTTPVersion.HTTP_2)
                else:
                    unsupported_feature()
            elif proto == PROTO_QUIC:
                if hasattr(dns.query, 'quic'):
                    response = dns.query.quic(query, server, timeout, dst_port, src_ip)
                else:
                    unsupported_feature()
            elif proto == PROTO_HTTP3:
                if hasattr(dns.query, '_http3'):
                    url = f"https://{server}:{dst_port}/dns-query"
                    response = dns.query._http3(query, server, url, timeout, dst_port, src_ip)
                else:
                    unsupported_feature()

        except dns.query.NoDOH:
            raise
        except (httpx.ConnectTimeout, httpx.ReadTimeout,
                httpx.ConnectError):
            raise ConnectionError('Connection failed')
        except ValueError:
            retval.rcode_text = "Invalid Response"
            break
        except dns.exception.Timeout:
            break
        except OSError as e:
            # Transient network errors should be re-raised for caller to handle
            if e.errno in (errno.EHOSTUNREACH, errno.ENETUNREACH):
                raise
            elif socket_ttl:  # other acceptable errors while doing traceroute
                break
            err(f"ERROR: {e.strerror}")
            raise OSError(e)
        except Exception as e:
            err(f"ERROR: {e}")
            break
        else:
            # convert time to milliseconds, considering that
            # time property is retruned differently by query.https
            # dns library returns float for most protocols but timedelta for HTTPS
            if isinstance(response.time, datetime.timedelta):
                elapsed = response.time.total_seconds() * 1000
            else:
                elapsed = response.time * 1000
            response_times.append(elapsed)
            if response:
                retval.response = response
                retval.flags = response.flags
                retval.ednsflags = response.ednsflags
                retval.answer = response.answer
                retval.rcode = response.rcode()
                retval.rcode_text = dns.rcode.to_text(response.rcode())
                if len(response.answer) > 0:
                    retval.ttl = response.answer[0].ttl

    r_sent = i + 1
    r_received = len(response_times)
    retval.r_lost_percent = (100 * (r_sent - r_received)) / r_sent
    if response_times:
        retval.r_min = min(response_times)
        retval.r_max = max(response_times)
        retval.r_avg = sum(response_times) / r_received
        if len(response_times) > 1:
            retval.r_stddev = stdev(response_times)
        else:
            retval.r_stddev = 0.0
    else:
        retval.r_min = 0.0
        retval.r_max = 0.0
        retval.r_avg = 0.0
        retval.r_stddev = 0.0

    return retval


def valid_rdatatype(rtype: str) -> bool:
    # validate RR type
    try:
        _ = dns.rdatatype.from_text(rtype)
    except dns.rdatatype.UnknownRdatatype:
        return False
    return True


# Standard DNS flags
_DNS_FLAG_QR = 0x8000
_DNS_FLAG_AA = 0x0400
_DNS_FLAG_TC = 0x0200
_DNS_FLAG_RD = 0x0100
_DNS_FLAG_RA = 0x0080
_DNS_FLAG_AD = 0x0020
_DNS_FLAG_CD = 0x0010

_DNS_FLAGS_BY_TEXT = {
    'QR': _DNS_FLAG_QR,
    'AA': _DNS_FLAG_AA,
    'TC': _DNS_FLAG_TC,
    'RD': _DNS_FLAG_RD,
    'RA': _DNS_FLAG_RA,
    'AD': _DNS_FLAG_AD,
    'CD': _DNS_FLAG_CD
}


def flags_to_text(flags: int) -> str:
    _by_value = {value: key for key, value in _DNS_FLAGS_BY_TEXT.items()}

    order = sorted(_by_value.items(), reverse=True)
    text_flags = []
    for k, v in order:
        if (flags & k) != 0:
            text_flags.append(v)
        else:
            text_flags.append('--')

    return ' '.join(text_flags)
