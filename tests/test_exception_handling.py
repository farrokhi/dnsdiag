"""
Offline tests for how dnsping and dnsdiag.dns.ping() react to transport errors,
and for what the tools pass to dnspython's encrypted transports.

The dnspython query functions are replaced with stubs that raise a chosen
exception or record their arguments, so every handler can be reached without a
network or a server that misbehaves on demand. test_local_responses.py covers
the subset that can be triggered for real.
"""

import inspect
import signal
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, NoReturn

import dns.exception
import dns.message
import dns.query
import httpx2
import pytest
from aioquic.h3.exceptions import H3Error
from aioquic.quic.connection import QuicConnectionError
from aioquic.quic.stream import StreamFinishedError
from dns.quic._common import UnexpectedEOF

import dnsdiag.dns
import dnseval
import dnsping
import dnstraceroute
from dnsdiag.dns import PROTO_HTTP3, PROTO_HTTPS, PROTO_QUIC, PROTO_TLS, PROTO_UDP

ALL_LOST = "1 requests transmitted, 0 responses received, 100% lost"
SERVER_IP = "192.0.2.1"
SERVER_NAME = "dns.example"
DOH_URL = "https://dns.example:8443/dns-query"
H2 = dns.query.HTTPVersion.HTTP_2
H3 = dns.query.HTTPVersion.H3


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
def restore_sigint() -> Iterator[None]:
    # main() installs its own SIGINT handler; give pytest its handler back afterwards
    previous_sigint = signal.getsignal(signal.SIGINT)
    yield
    signal.signal(signal.SIGINT, previous_sigint)


@pytest.fixture
def run_dnsping_main(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
                     restore_sigint: None) -> Callable[..., DNSPingRun]:
    """Run dnsping.main() in-process for one query with the given arguments."""

    def run(*args: str) -> DNSPingRun:
        monkeypatch.setattr(sys, "argv", ["dnsping.py", "-c", "1", "-w", "1", *args, "example.com"])
        exit_code: int | str | None = 0
        try:
            dnsping.main()
        except SystemExit as e:
            exit_code = e.code
        captured = capsys.readouterr()
        return DNSPingRun(exit_code, captured.out, captured.err)

    return run


@pytest.fixture
def run_dnsping(monkeypatch: pytest.MonkeyPatch,
                run_dnsping_main: Callable[..., DNSPingRun]) -> Callable[..., DNSPingRun]:
    """Run dnsping.main() in-process with one dns.query function raising exc."""

    def run(query_function: str, exc: BaseException, *args: str) -> DNSPingRun:
        monkeypatch.setattr(dns.query, query_function, raiser(exc))
        return run_dnsping_main("-s", "127.0.0.1", *args)

    return run


def record_query(monkeypatch: pytest.MonkeyPatch, query_function: str) -> list[dict[str, Any]]:
    """Replace a dns.query function with one that records its arguments by parameter name."""
    signature = inspect.signature(getattr(dns.query, query_function))
    calls: list[dict[str, Any]] = []

    def query(*args: Any, **kwargs: Any) -> dns.message.Message:
        calls.append(dict(signature.bind(*args, **kwargs).arguments))
        return dns.message.make_response(args[0])

    monkeypatch.setattr(dns.query, query_function, query)
    return calls


def selected(call: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    return {name: call.get(name) for name in expected}


CONNECTION_CLOSED = "Connection closed unexpectedly"
QUIC_CONNECTION_ERROR = QuicConnectionError(error_code=0, frame_type=0, reason_phrase="closed")


class TestDNSPingDoH:
    """dnsping --doh, where dnspython raises httpx2 exceptions"""

    @pytest.mark.parametrize("exc,message", [
        (httpx2.ConnectError("no address worked"), "Connection failed"),
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
        ("https", PROTO_HTTP3),
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
        ("https", PROTO_HTTP3, dns.query.NoDOH),
        ("quic", PROTO_QUIC, dns.query.NoDOQ),
    ])
    def test_transport_unavailable(self, monkeypatch: pytest.MonkeyPatch, query_function: str, proto: int,
                                   exc: type[BaseException]) -> None:
        monkeypatch.setattr(dns.query, query_function, raiser(exc()))
        with pytest.raises(exc):
            ping(proto)


class TestPingServerName:
    """ping() connects to the address it is given and sends the name for SNI and certificates"""

    @pytest.mark.parametrize("query_function,proto,expected", [
        ("tls", PROTO_TLS, {"where": SERVER_IP, "port": 8443, "server_hostname": SERVER_NAME}),
        ("quic", PROTO_QUIC, {"where": SERVER_IP, "port": 8443, "hostname": SERVER_NAME}),
        ("https", PROTO_HTTPS, {"where": DOH_URL, "bootstrap_address": SERVER_IP, "http_version": H2}),
        ("https", PROTO_HTTP3, {"where": DOH_URL, "bootstrap_address": SERVER_IP, "http_version": H3}),
    ], ids=["dot", "doq", "doh", "doh3"])
    def test_with_hostname(self, monkeypatch: pytest.MonkeyPatch, query_function: str, proto: int,
                           expected: dict[str, Any]) -> None:
        calls = record_query(monkeypatch, query_function)
        dnsdiag.dns.ping("example.com", SERVER_IP, 8443, "A", 1, 1, proto, None, server_hostname=SERVER_NAME)
        assert selected(calls[0], expected) == expected

    @pytest.mark.parametrize("query_function,proto,expected", [
        ("tls", PROTO_TLS, {"where": SERVER_IP, "port": 8443, "server_hostname": None}),
        ("quic", PROTO_QUIC, {"where": SERVER_IP, "port": 8443, "hostname": None}),
        ("https", PROTO_HTTPS, {"where": SERVER_IP, "port": 8443, "bootstrap_address": None, "http_version": H2}),
        ("https", PROTO_HTTP3, {"where": SERVER_IP, "port": 8443, "bootstrap_address": None, "http_version": H3}),
    ], ids=["dot", "doq", "doh", "doh3"])
    def test_without_hostname(self, monkeypatch: pytest.MonkeyPatch, query_function: str, proto: int,
                              expected: dict[str, Any]) -> None:
        calls = record_query(monkeypatch, query_function)
        dnsdiag.dns.ping("example.com", SERVER_IP, 8443, "A", 1, 1, proto, None)
        assert selected(calls[0], expected) == expected

    def test_http3_brackets_ipv6_address(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Stops one level below https(), so dnspython's own URL building is exercised
        calls = record_query(monkeypatch, "_http3")
        dnsdiag.dns.ping("example.com", "2001:db8::1", 443, "A", 1, 1, PROTO_HTTP3, None)
        assert calls[0]["url"] == "https://[2001:db8::1]:443/dns-query"
        assert calls[0]["where"] == "2001:db8::1"


class TestToolsPassServerName:
    """Each tool resolves a hostname itself and must keep the name for the transports"""

    @pytest.mark.parametrize("entry,expected", [(SERVER_NAME, SERVER_NAME), (SERVER_IP, None)],
                             ids=["hostname", "address"])
    def test_dnseval(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, restore_sigint: None,
                     entry: str, expected: str | None) -> None:
        seen = []

        def fake_ping(qname: str, server: str, *args: Any, **kwargs: Any) -> dnsdiag.dns.PingResponse:
            seen.append((server, kwargs.get("server_hostname")))
            return dnsdiag.dns.PingResponse()

        monkeypatch.setattr(dnsdiag.dns, "ping", fake_ping)
        monkeypatch.setattr(dnseval, "_resolve_server", lambda server: SERVER_IP)
        monkeypatch.setattr(dnseval.time, "sleep", lambda seconds: None)
        servers = tmp_path / "servers.txt"
        servers.write_text(f"{entry}\n")
        monkeypatch.setattr(sys, "argv", ["dnseval.py", "--quic", "-f", str(servers), "-c", "1", "example.com"])

        dnseval.main()

        # Once for the cache warmup and once for the measurement
        assert seen == [(SERVER_IP, expected), (SERVER_IP, expected)]

    def test_dnstraceroute(self, monkeypatch: pytest.MonkeyPatch) -> None:
        seen: dict[str, Any] = {}

        def fake_ping(*args: Any, **kwargs: Any) -> dnsdiag.dns.PingResponse:
            seen.update(kwargs)
            return dnsdiag.dns.PingResponse()

        monkeypatch.setattr(dnsdiag.dns, "ping", fake_ping)

        dnstraceroute.ping("example.com", SERVER_IP, "A", PROTO_QUIC, 853, 64, 1, None, False, False,
                           server_hostname=SERVER_NAME)

        assert seen["server_hostname"] == SERVER_NAME

    @pytest.mark.parametrize("flag,version", [("--doh", H2), ("--http3", H3)], ids=["doh", "doh3"])
    def test_dnsping_connects_to_the_resolved_address(self, monkeypatch: pytest.MonkeyPatch,
                                                      run_dnsping_main: Callable[..., DNSPingRun],
                                                      flag: str, version: dns.query.HTTPVersion) -> None:
        calls = record_query(monkeypatch, "https")
        monkeypatch.setattr(dnsping, "resolve_server_address", lambda server, af: SERVER_IP)

        result = run_dnsping_main(flag, "-s", SERVER_NAME, "-p", "8443")

        assert result.exit_code == 0, result.stderr
        expected = {"where": DOH_URL, "bootstrap_address": SERVER_IP, "http_version": version}
        assert selected(calls[0], expected) == expected

    @pytest.mark.parametrize("flag,version", [("--doh", H2), ("--http3", H3)], ids=["doh", "doh3"])
    def test_dnsping_with_address_sends_no_name(self, monkeypatch: pytest.MonkeyPatch,
                                                run_dnsping_main: Callable[..., DNSPingRun],
                                                flag: str, version: dns.query.HTTPVersion) -> None:
        calls = record_query(monkeypatch, "https")

        result = run_dnsping_main(flag, "-s", SERVER_IP, "-p", "8443")

        assert result.exit_code == 0, result.stderr
        expected = {"where": SERVER_IP, "port": 8443, "bootstrap_address": None, "http_version": version}
        assert selected(calls[0], expected) == expected
