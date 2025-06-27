import os
import sys
import time
import tempfile
import cymruwhois

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dnsdiag import whois


def test_save_and_restore(tmp_path):
    data = {"1.1.1.1": ("AS1", 123)}
    file_path = tmp_path / "cache.pkl"
    # patch constant
    orig_file = whois.WHOIS_CACHE_FILE
    whois.WHOIS_CACHE_FILE = str(file_path)
    try:
        whois.save(data)
        loaded = whois.restore()
        assert loaded == data
    finally:
        whois.WHOIS_CACHE_FILE = orig_file


def test_asn_lookup_cache(monkeypatch):
    called = []

    class Dummy:
        def lookup(self, ip):
            called.append(ip)
            return "ASNEW"

    monkeypatch.setattr(cymruwhois, "Client", lambda: Dummy())
    current = 1000
    monkeypatch.setattr(time, "time", lambda: current)

    cache = {"1.1.1.1": ("ASOLD", current - 100)}  # fresh cache
    asn, new_cache = whois.asn_lookup("1.1.1.1", cache)
    assert asn == "ASOLD"
    assert not called
    assert new_cache == cache

    # Expired cache triggers lookup
    cache_expired = {"1.1.1.1": ("ASOLD", current - 37000)}
    called.clear()
    asn, new_cache = whois.asn_lookup("1.1.1.1", cache_expired)
    assert asn == "ASNEW"
    assert called == ["1.1.1.1"]
    assert new_cache["1.1.1.1"][0] == "ASNEW"
