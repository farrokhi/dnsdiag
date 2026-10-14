"""
Offline tests for how dnsping and dnsdiag.dns.ping() react to transport errors.

The dnspython query functions are replaced with stubs that raise a chosen
exception, so every handler can be reached without a network or a server that
misbehaves on demand. test_local_responses.py covers the subset that can be
triggered for real.
"""

import signal
import sys
from collections.abc import Callable, Iterator
from typing import NoReturn

import dns.exception
import dns.query
import httpx2
import pytest
from aioquic.h3.exceptions import H3Error
from aioquic.quic.connection import QuicConnectionError
from aioquic.quic.stream import StreamFinishedError
from dns.quic._common import UnexpectedEOF

import dnsdiag.dns
import dnsping
from dnsdiag.dns import PROTO_HTTP3, PROTO_HTTPS, PROTO_QUIC, PROTO_UDP

ALL_LOST = "1 requests transmitted, 0 responses received, 100% lost"


def raiser(exc: BaseException) -> Callable[..., NoReturn]:
    def query(*args: object, **kwargs: object) -> NoReturn:
        raise exc
    return query


class DNSPingRun:
    def __init__(self, exit_code: int | str | None, stdout: str, stderr: str) -> None:
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr


@pytest.fixture
def run_dnsping(monkeypatch: pytest.MonkeyPatch,
                capsys: pytest.CaptureFixture[str]) -> Iterator[Callable[..., DNSPingRun]]:
    """Run dnsping.main() in-process with one dns.query function raising exc."""

    def run(query_function: str, exc: BaseException, *args: str) -> DNSPingRun:
        monkeypatch.setattr(dns.query, query_function, raiser(exc))
        monkeypatch.setattr(sys, "argv", ["dnsping.py", "-s", "127.0.0.1", "-c", "1", "-w", "1", *args,
                                          "example.com"])
        exit_code: int | str | None = 0
        try:
            dnsping.main()
        except SystemExit as e:
            exit_code = e.code
        captured = capsys.readouterr()
        return DNSPingRun(exit_code, captured.out, captured.err)

    # main() installs its own SIGINT handler; give pytest its handler back afterwards
    previous_sigint = signal.getsignal(signal.SIGINT)
    yield run
    signal.signal(signal.SIGINT, previous_sigint)


CONNECTION_CLOSED = "Connection closed unexpectedly"
QUIC_CONNECTION_ERROR = QuicConnectionError(error_code=0, frame_type=0, reason_phrase="closed")


class TestDNSPingDoH:
    """dnsping --doh, where dnspython raises httpx2 exceptions"""

    @pytest.mark.parametrize("exc,message", [
        (httpx2.ConnectError("refused"), "Connection refused"),
        (httpx2.ConnectTimeout("timed out"), "Request timeout"),
        (httpx2.ReadTimeout("timed out"), "Read timeout"),
        (httpx2.WriteTimeout("timed out"), "Connection failed"),
        (httpx2.StreamError("stream"), "Connection failed"),
        (httpx2.ProtocolError("protocol"), "Connection failed"),
        (dns.exception.FormError("bad wire"), "Malformed response"),
    ], ids=lambda v: type(v).__name__ if isinstance(v, BaseException) else None)
    def test_transient_errors(self, run_dnsping: Callable[..., DNSPingRun], exc: BaseException,
                              message: str) -> None:
        result = run_dnsping("https", exc, "--doh")
        assert result.exit_code == 0, result.stderr
        assert message in result.stdout
        assert ALL_LOST in result.stdout

    def test_invalid_response(self, run_dnsping: Callable[..., DNSPingRun]) -> None:
        result = run_dnsping("https", ValueError("responded with status code 500"), "--doh")
        assert result.exit_code == 0
        assert "ERROR: invalid response" in result.stderr
        assert ALL_LOST in result.stdout

    def test_doh_unavailable(self, run_dnsping: Callable[..., DNSPingRun]) -> None:
        result = run_dnsping("https", dns.query.NoDOH(), "--doh")
        assert result.exit_code == 1
        assert "requires the httpx2, httpcore2 and h2 modules" in result.stderr


class TestDNSPingDoH3:
    """dnsping --http3, which goes through aioquic and dnspython's QUIC layer"""

    @pytest.mark.parametrize("exc,message", [
        (httpx2.WriteTimeout("timed out"), "Connection failed"),
        (httpx2.StreamError("stream"), "Connection failed"),
        (httpx2.ProtocolError("protocol"), "Connection failed"),
        (httpx2.ConnectTimeout("timed out"), "Request timeout"),
        (UnexpectedEOF(), CONNECTION_CLOSED),
        (QUIC_CONNECTION_ERROR, CONNECTION_CLOSED),
        (H3Error(), CONNECTION_CLOSED),
        (dns.exception.FormError("bad wire"), "Malformed response"),
    ], ids=lambda v: type(v).__name__ if isinstance(v, BaseException) else None)
    def test_transient_errors(self, run_dnsping: Callable[..., DNSPingRun], exc: BaseException,
                              message: str) -> None:
        result = run_dnsping("https", exc, "--http3")
        assert result.exit_code == 0, result.stderr
        assert message in result.stdout
        assert ALL_LOST in result.stdout

    def test_doh3_unavailable(self, run_dnsping: Callable[..., DNSPingRun]) -> None:
        result = run_dnsping("https", dns.query.NoDOH("DNS-over-HTTP3 is not available."), "--http3")
        assert result.exit_code == 1
        assert "DNS-over-HTTP/3 requires the aioquic module" in result.stderr


class TestDNSPingDoQ:
    """dnsping --quic"""

    @pytest.mark.parametrize("exc,message", [
        (dns.exception.Timeout(), "Request timeout"),
        (UnexpectedEOF(), CONNECTION_CLOSED),
        (QUIC_CONNECTION_ERROR, CONNECTION_CLOSED),
        (StreamFinishedError(), CONNECTION_CLOSED),
        (dns.exception.FormError("bad wire"), "Malformed response"),
    ], ids=lambda v: type(v).__name__ if isinstance(v, BaseException) else None)
    def test_transient_errors(self, run_dnsping: Callable[..., DNSPingRun], exc: BaseException,
                              message: str) -> None:
        result = run_dnsping("quic", exc, "--quic")
        assert result.exit_code == 0, result.stderr
        assert message in result.stdout
        assert ALL_LOST in result.stdout

    def test_doq_unavailable(self, run_dnsping: Callable[..., DNSPingRun]) -> None:
        result = run_dnsping("quic", dns.query.NoDOQ(), "--quic")
        assert result.exit_code == 1
        assert "DNS-over-QUIC requires the aioquic module" in result.stderr


class TestDNSPingUDP:
    """dnsping over plain UDP"""

    def test_malformed_response(self, run_dnsping: Callable[..., DNSPingRun]) -> None:
        result = run_dnsping("udp", dns.exception.FormError("bad wire"))
        assert result.exit_code == 0, result.stderr
        assert "Malformed response" in result.stdout
        assert ALL_LOST in result.stdout

    def test_malformed_response_quiet(self, run_dnsping: Callable[..., DNSPingRun]) -> None:
        result = run_dnsping("udp", dns.exception.FormError("bad wire"), "-q")
        assert result.exit_code == 0, result.stderr
        assert "Malformed response" not in result.stdout
        assert ALL_LOST in result.stdout


def ping(proto: int) -> dnsdiag.dns.PingResponse:
    return dnsdiag.dns.ping("example.com", "127.0.0.1", 53, "A", 1, 1, proto, None)


class TestPingFunction:
    """dnsdiag.dns.ping(), shared by dnseval and dnstraceroute"""

    @pytest.mark.parametrize("exc", [
        httpx2.ConnectError("refused"),
        httpx2.ConnectTimeout("timed out"),
        httpx2.ReadTimeout("timed out"),
    ], ids=lambda e: type(e).__name__)
    def test_doh_connection_failures(self, monkeypatch: pytest.MonkeyPatch, exc: BaseException) -> None:
        monkeypatch.setattr(dns.query, "https", raiser(exc))
        with pytest.raises(ConnectionError, match="Connection failed"):
            ping(PROTO_HTTPS)

    @pytest.mark.parametrize("query_function,proto", [
        ("udp", PROTO_UDP),
        ("https", PROTO_HTTPS),
        ("_http3", PROTO_HTTP3),
        ("quic", PROTO_QUIC),
    ])
    @pytest.mark.parametrize("exc", [ValueError("bad status"), dns.exception.FormError("bad wire")],
                             ids=lambda e: type(e).__name__)
    def test_invalid_response(self, monkeypatch: pytest.MonkeyPatch, query_function: str, proto: int,
                              exc: BaseException) -> None:
        monkeypatch.setattr(dns.query, query_function, raiser(exc))
        result = ping(proto)
        assert result.rcode_text == "Invalid Response"
        assert result.r_lost_percent == 100.0

    def test_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(dns.query, "udp", raiser(dns.exception.Timeout()))
        result = ping(PROTO_UDP)
        assert result.rcode_text == "No Response"
        assert result.r_lost_percent == 100.0

    @pytest.mark.parametrize("query_function,proto,exc", [
        ("https", PROTO_HTTPS, dns.query.NoDOH),
        ("_http3", PROTO_HTTP3, dns.query.NoDOH),
        ("quic", PROTO_QUIC, dns.query.NoDOQ),
    ])
    def test_transport_unavailable(self, monkeypatch: pytest.MonkeyPatch, query_function: str, proto: int,
                                   exc: type[BaseException]) -> None:
        monkeypatch.setattr(dns.query, query_function, raiser(exc()))
        with pytest.raises(exc):
            ping(proto)
