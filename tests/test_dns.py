import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dnsdiag import dns


def test_proto_to_text_and_ports():
    assert dns.proto_to_text(dns.PROTO_UDP) == "UDP"
    assert dns.proto_to_text(dns.PROTO_TCP) == "TCP"
    assert dns.getDefaultPort(dns.PROTO_UDP) == 53
    assert dns.getDefaultPort(dns.PROTO_TLS) == 853
    assert dns.getDefaultPort(dns.PROTO_HTTP3) == 443


def test_random_string_default_length():
    s = dns.random_string()
    assert 5 <= len(s) <= 10
    assert re.fullmatch(r"[A-Za-z0-9]+", s)


def test_random_string_custom_length():
    s = dns.random_string(3, 3)
    assert len(s) == 3


def test_valid_rdatatype():
    assert dns.valid_rdatatype("A") is True
    assert dns.valid_rdatatype("INVALID") is False


def test_flags_to_text():
    # All flags off
    assert dns.flags_to_text(0) == "-- -- -- -- -- -- --"
    # QR and AA on
    flags = dns.dns.flags.QR | dns.dns.flags.AA
    assert dns.flags_to_text(flags) == "QR AA -- -- -- -- --"
