"""
Offline tests that run the CLI tools against local stand-in servers.

Public resolvers rarely send unusual EDNS options or malformed replies, and
refused or stalled DoH connections depend on the network. Local servers make
these cases reproducible while still going through dnspython's real parser
and transports, so the tests also catch changes in what dnspython raises.
"""

import json
import socket
import subprocess
import sys
import threading
from collections.abc import Callable, Iterator
from pathlib import Path

import dns.edns
import dns.message
import dns.name
import dns.rrset
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ALL_LOST = "1 requests transmitted, 0 responses received, 100% lost"

ReplyBuilder = Callable[[bytes], bytes]


class UDPResponder:
    """Answer every UDP query on 127.0.0.1 with bytes from a reply builder."""

    def __init__(self, build_reply: ReplyBuilder) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.settimeout(0.1)
        self.port: int = self.sock.getsockname()[1]
        self._build_reply = build_reply
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._serve, daemon=True)

    def __enter__(self) -> "UDPResponder":
        self._thread.start()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self._stop.set()
        self._thread.join()
        self.sock.close()

    def _serve(self) -> None:
        while not self._stop.is_set():
            try:
                wire, peer = self.sock.recvfrom(65535)
            except TimeoutError:
                continue
            self.sock.sendto(self._build_reply(wire), peer)


def answer_with_options(*options: dns.edns.Option) -> ReplyBuilder:
    def build(wire: bytes) -> bytes:
        query = dns.message.from_wire(wire)
        response = dns.message.make_response(query)
        response.use_edns(0, options=list(options))
        response.answer.append(dns.rrset.from_text(query.question[0].name, 300, "IN", "A", "192.0.2.1"))
        return response.to_wire()
    return build


# ECS for 192.0.0.0/20 whose last address octet carries bits beyond the
# source prefix length; RFC 7871 section 6 requires them to be zero.
NONZERO_PAD_ECS = dns.edns.GenericOption(dns.edns.OptionType.ECS, b"\x00\x01\x14\x00\xc0\x00\x0f")


def nonzero_pad_ecs_reply(wire: bytes) -> bytes:
    return answer_with_options(NONZERO_PAD_ECS)(wire)


def truncated_reply(wire: bytes) -> bytes:
    return answer_with_options()(wire)[:-2]


def run_tool(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(PROJECT_ROOT / script), *args],
                          capture_output=True, text=True, timeout=30)


def assert_clean_exit(result: subprocess.CompletedProcess[str]) -> None:
    output = result.stdout + result.stderr
    assert "Traceback" not in output, output
    assert result.returncode == 0, output


@pytest.fixture
def closed_tcp_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port: int = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture
def silent_tcp_port() -> Iterator[int]:
    """A listener the kernel completes handshakes for, but which never speaks TLS."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    s.listen(8)
    yield s.getsockname()[1]
    s.close()


@pytest.fixture
def server_list(tmp_path: Path) -> Path:
    path = tmp_path / "servers.txt"
    path.write_text("127.0.0.1\n")
    return path


class TestEDNSOptionDisplay:
    """dnsping --verbose must print every EDNS option, typed or generic"""

    def test_typed_and_generic_options(self) -> None:
        options = [
            dns.edns.GenericOption(dns.edns.OptionType.REPORTCHANNEL, dns.name.from_text("agent.example.").to_wire()),
            dns.edns.GenericOption(dns.edns.OptionType.EDE_EXTRA_TEXT_LANGUAGE, b"en"),
            dns.edns.GenericOption(dns.edns.OptionType.FILTERING_CONTACT, b"mailto:abuse@example.net"),
            dns.edns.GenericOption(65001, b"\x01\x02\x03"),
        ]
        with UDPResponder(answer_with_options(*options)) as server:
            result = run_tool("dnsping.py", "-s", "127.0.0.1", "-p", str(server.port),
                              "-c", "1", "-w", "2", "-e", "-v", "example.com")

        assert_clean_exit(result)
        assert "REPORTCHANNEL (18): agent.example." in result.stdout
        assert "EDE-EXTRA-TEXT-LANGUAGE (22): en" in result.stdout
        assert "FILTERING-CONTACT (23): mailto:abuse@example.net" in result.stdout
        assert "UNKNOWN (65001): type=65001, length=3" in result.stdout


class TestMalformedResponses:
    """Replies that dnspython refuses to parse count as lost, not as crashes"""

    @pytest.mark.parametrize("build_reply", [nonzero_pad_ecs_reply, truncated_reply],
                             ids=["ecs-nonzero-pad", "truncated"])
    def test_dnsping(self, build_reply: ReplyBuilder) -> None:
        with UDPResponder(build_reply) as server:
            result = run_tool("dnsping.py", "-s", "127.0.0.1", "-p", str(server.port),
                              "-c", "1", "-w", "2", "-e", "example.com")

        assert_clean_exit(result)
        assert "Malformed response" in result.stdout
        assert ALL_LOST in result.stdout

    @pytest.mark.parametrize("build_reply", [nonzero_pad_ecs_reply, truncated_reply],
                             ids=["ecs-nonzero-pad", "truncated"])
    def test_dnseval(self, build_reply: ReplyBuilder, server_list: Path) -> None:
        with UDPResponder(build_reply) as server:
            result = run_tool("dnseval.py", "-f", str(server_list), "-p", str(server.port),
                              "-c", "1", "-w", "2", "-e", "--skip-warmup", "-j", "-", "example.com")

        assert_clean_exit(result)
        records = [json.loads(line) for line in result.stdout.splitlines() if line.startswith("{")]
        assert len(records) == 1, result.stdout
        assert records[0]["data"]["rcode_text"] == "Invalid Response"


class TestDoHConnectionFailures:
    """Failures raised by dnspython's DoH transport (httpx2) are reported, not raised"""

    def test_dnsping_connection_refused(self, closed_tcp_port: int) -> None:
        result = run_tool("dnsping.py", "--doh", "-s", "127.0.0.1", "-p", str(closed_tcp_port),
                          "-c", "1", "-w", "2", "example.com")

        assert_clean_exit(result)
        assert "Connection refused" in result.stdout
        assert ALL_LOST in result.stdout

    def test_dnsping_connect_timeout(self, silent_tcp_port: int) -> None:
        result = run_tool("dnsping.py", "--doh", "-s", "127.0.0.1", "-p", str(silent_tcp_port),
                          "-c", "1", "-w", "1", "example.com")

        assert_clean_exit(result)
        assert "Request timeout" in result.stdout
        assert ALL_LOST in result.stdout

    def test_dnseval_connection_refused(self, closed_tcp_port: int, server_list: Path) -> None:
        result = run_tool("dnseval.py", "--doh", "-f", str(server_list), "-p", str(closed_tcp_port),
                          "-c", "1", "-w", "2", "--skip-warmup", "example.com")

        assert_clean_exit(result)
        assert "127.0.0.1: Connection failed" in result.stdout

    def test_dnseval_connect_timeout(self, silent_tcp_port: int, server_list: Path) -> None:
        result = run_tool("dnseval.py", "--doh", "-f", str(server_list), "-p", str(silent_tcp_port),
                          "-c", "1", "-w", "1", "--skip-warmup", "example.com")

        assert_clean_exit(result)
        assert "127.0.0.1: Connection failed" in result.stdout
