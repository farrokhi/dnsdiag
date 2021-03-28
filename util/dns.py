import datetime
import random
import string
import sys
from statistics import stdev

import dns.flags
import dns.message
import dns.query
import dns.rcode
import dns.rdataclass
import requests.exceptions

shutdown = False

# Transport protocols
PROTO_UDP = 0
PROTO_TCP = 1
PROTO_TLS = 2
PROTO_HTTPS = 3


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
    }
    return _proto_name[proto]


def ping(qname, server, dst_port, rdtype, timeout, count, proto, src_ip, use_edns=False, force_miss=False,
         want_dnssec=False, custome_socket = None):
    retval = PingResponse()
    retval.rcode_text = "No Response"

    response_times = []
    i = 0

    if custome_socket:
        dns.query.socket_factory = custome_socket

    for i in range(count):

        if shutdown:  # user pressed CTRL+C
            raise SystemExit

        if force_miss:
            fqdn = "_dnsdiag_%s_.%s" % (random_string(), qname)
        else:
            fqdn = qname

        if use_edns:
            query = dns.message.make_query(fqdn, rdtype, dns.rdataclass.IN, use_edns, want_dnssec,
                                           ednsflags=dns.flags.edns_from_text('DO'), payload=8192)
        else:
            query = dns.message.make_query(fqdn, rdtype, dns.rdataclass.IN, use_edns, want_dnssec)

        try:
            if proto is PROTO_UDP:
                response = dns.query.udp(query, server, timeout, dst_port, src_ip, ignore_unexpected=True)
            elif proto is PROTO_TCP:
                response = dns.query.tcp(query, server, timeout, dst_port, src_ip)
            elif proto is PROTO_TLS:
                response = dns.query.tls(query, server, timeout, dst_port, src_ip)
            elif proto is PROTO_HTTPS:
                response = dns.query.https(query, server, timeout, dst_port, src_ip)

        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            raise ConnectionError('Connection failed')
        except ValueError as e:
            retval.rcode_text = "Invalid Response"
            break
        except Exception as e:
            print(e)
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
    _flags_order = sorted(_by_value.items(), reverse=True)

    _by_value = dict([(y, x) for x, y in _by_text.items()])

    order = sorted(_by_value.items(), reverse=True)
    text_flags = []
    for k, v in order:
        if flags & k != 0:
            text_flags.append(v)
        else:
            text_flags.append('--')

    return ' '.join(text_flags)
