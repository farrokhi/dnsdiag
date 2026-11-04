"""
Offline tests for dnstraceroute's AS number lookups and its use of the working directory.

dnstraceroute normally runs as root from whatever directory the user is in, so
it must not load or write anything there. The trace tests run main() in-process
with a fake ICMP socket, and lookups use the real cymruwhois client with only
its network call replaced.
"""

import itertools
import os
import pickle
import signal
import subprocess
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import cymruwhois
import pytest

import dnsdiag.whois
import dnstraceroute
from dnsdiag import shared

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVER = "192.0.2.1"
OTHER_ADDRESS = "192.0.2.2"
CACHE_FILE = "whois.cache"
MARKER_FILE = "cache-was-loaded"
GOOGLE = cymruwhois.record("15169", SERVER, "192.0.2.0/24", "US", "GOOGLE, US")
UNROUTED = cymruwhois.record("NA", SERVER, "NA", "", "NA")


class MarkerPayload:
    """Creates a file when unpickled, so a test can tell whether the cache was loaded."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def __reduce__(self) -> tuple[Any, ...]:
        return (open, (str(self.path), "w"))


def plant_cache(directory: Path) -> bytes:
    """Put a hostile cache file in a directory, as an older version's file would sit there."""
    planted = pickle.dumps(MarkerPayload(directory / MARKER_FILE))
    (directory / CACHE_FILE).write_bytes(planted)
    return planted


@pytest.fixture
def whois_answers(monkeypatch: pytest.MonkeyPatch) -> Iterator[list[str]]:
    """Answer cymruwhois lookups with GOOGLE and return the addresses that reached the network."""
    asked: list[str] = []

    def lookup_raw(self: cymruwhois.Client, ips: list[str]) -> Iterator[cymruwhois.record]:
        asked.extend(ips)
        return iter(cymruwhois.record(GOOGLE.asn, ip, GOOGLE.prefix, GOOGLE.cc, GOOGLE.owner) for ip in ips)

    monkeypatch.setattr(cymruwhois.Client, "_lookupmany_raw", lookup_raw)
    yield asked


def failing_lookup(self: cymruwhois.Client, ips: list[str]) -> Iterator[cymruwhois.record]:
    raise OSError("whois.cymru.com unreachable")


class TestAsnLookup:
    def test_returns_the_record(self, whois_answers: list[str]) -> None:
        asn, _ = dnsdiag.whois.asn_lookup(SERVER, {})
        assert (asn.asn, asn.owner) == ("15169", "GOOGLE, US")

    def test_repeated_address_is_looked_up_once(self, whois_answers: list[str]) -> None:
        cache: dict[str, Any] = {}
        first, cache = dnsdiag.whois.asn_lookup(SERVER, cache)
        second, cache = dnsdiag.whois.asn_lookup(SERVER, cache)
        assert whois_answers == [SERVER]
        assert second is first

    def test_each_address_gets_its_own_lookup(self, whois_answers: list[str]) -> None:
        cache: dict[str, Any] = {}
        _, cache = dnsdiag.whois.asn_lookup(SERVER, cache)
        other, cache = dnsdiag.whois.asn_lookup(OTHER_ADDRESS, cache)
        assert whois_answers == [SERVER, OTHER_ADDRESS]
        assert other.ip == OTHER_ADDRESS

    def test_failed_lookup_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(cymruwhois.Client, "_lookupmany_raw", failing_lookup)
        assert dnsdiag.whois.asn_lookup(SERVER, {}) == (None, {})

    def test_failed_lookup_is_retried(self, monkeypatch: pytest.MonkeyPatch, whois_answers: list[str]) -> None:
        answering_lookup = cymruwhois.Client._lookupmany_raw
        monkeypatch.setattr(cymruwhois.Client, "_lookupmany_raw", failing_lookup)
        _, cache = dnsdiag.whois.asn_lookup(SERVER, {})

        monkeypatch.setattr(cymruwhois.Client, "_lookupmany_raw", answering_lookup)
        asn, _ = dnsdiag.whois.asn_lookup(SERVER, cache)

        assert asn.asn == "15169"

    def test_memcached_is_not_used(self, monkeypatch: pytest.MonkeyPatch, whois_answers: list[str]) -> None:
        # python-memcached unpickles what the server returns, and any local user can listen on its port
        servers: list[list[str]] = []

        def memcache_client(hosts: list[str]) -> SimpleNamespace:
            servers.append(hosts)
            return SimpleNamespace(get_multi=lambda keys: {}, set=lambda *args: None)

        monkeypatch.setattr(cymruwhois, "HAVE_MEMCACHE", True)
        monkeypatch.setattr(cymruwhois, "memcache", SimpleNamespace(Client=memcache_client), raising=False)

        asn, _ = dnsdiag.whois.asn_lookup(SERVER, {})

        assert servers == []
        assert asn.asn == "15169"


STARTS = {
    # How the source tree, the Docker image and the standalone binaries start the tool
    "script": [sys.executable, str(PROJECT_ROOT / "dnstraceroute.py")],
    # How the console script from a pip install starts it
    "entry point": [sys.executable, "-c",
                    "import sys, dnstraceroute; sys.argv[0] = 'dnstraceroute'; dnstraceroute.main()"],
}
# -h exits before any trace, so start-up code runs without root or a network. The -a case
# reaches it with the flag on the command line; the trace tests below cover -a inside main().
ARGUMENTS = {"-h": ["-h"], "-a -h": ["-a", "-h"]}


@pytest.fixture(params=list(itertools.product(STARTS, ARGUMENTS)), ids=lambda param: " ".join(param))
def start_tool(request: pytest.FixtureRequest) -> Callable[[Path], subprocess.CompletedProcess[str]]:
    start_with, arguments = request.param

    def start(cwd: Path) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT), "PYTHONDONTWRITEBYTECODE": "1"}
        return subprocess.run([*STARTS[start_with], *ARGUMENTS[arguments]], cwd=cwd, env=env,
                              capture_output=True, text=True, timeout=30)

    return start


@pytest.fixture
def read_only_dir(tmp_path: Path) -> Iterator[Path]:
    if not hasattr(os, "geteuid") or os.geteuid() == 0:
        pytest.skip("directory permissions do not stop root, or do not apply on this platform")
    tmp_path.chmod(0o555)
    yield tmp_path
    tmp_path.chmod(0o755)


class TestWorkingDirectory:
    def test_cache_file_is_not_loaded(self, start_tool: Callable[..., Any], tmp_path: Path) -> None:
        plant_cache(tmp_path)
        start_tool(tmp_path)
        assert not (tmp_path / MARKER_FILE).exists()

    def test_cache_file_from_older_version_is_left_alone(self, start_tool: Callable[..., Any],
                                                         tmp_path: Path) -> None:
        planted = plant_cache(tmp_path)
        start_tool(tmp_path)
        assert (tmp_path / CACHE_FILE).read_bytes() == planted

    def test_no_file_is_created(self, start_tool: Callable[..., Any], tmp_path: Path) -> None:
        start_tool(tmp_path)
        assert list(tmp_path.iterdir()) == []

    def test_read_only_directory_gives_clean_exit(self, start_tool: Callable[..., Any],
                                                  read_only_dir: Path) -> None:
        result = start_tool(read_only_dir)
        assert result.returncode == 0, result.stderr
        assert "Traceback" not in result.stderr


class FakeIcmpSocket:
    """Stands in for the raw socket that needs root. No ICMP arrives, so only the server is a hop."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def bind(self, address: Any) -> None:
        pass

    def settimeout(self, timeout: float) -> None:
        pass

    def recvfrom(self, size: int) -> tuple[bytes, Any]:
        raise TimeoutError

    def close(self) -> None:
        pass


@pytest.fixture
def trace(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
          tmp_path: Path) -> Iterator[Callable[..., str]]:
    """Run dnstraceroute.main() in-process for a trace that reaches the server at the first hop."""

    def run(*args: str) -> str:
        monkeypatch.setattr(sys, "argv", ["dnstraceroute.py", "-n", "-c", "1", "-s", SERVER, *args, "example.com"])
        dnstraceroute.main()
        return capsys.readouterr().out

    monkeypatch.setattr(dnstraceroute.socket, "socket", FakeIcmpSocket)
    monkeypatch.setattr(dnstraceroute, "ping", lambda *args, **kwargs: (True, 12.5, None))
    monkeypatch.setattr(dnstraceroute, "whois_cache", {})
    monkeypatch.setattr(shared, "shutdown", False)
    monkeypatch.chdir(tmp_path)
    # main() installs its own SIGINT handler; give pytest its handler back afterwards
    previous_sigint = signal.getsignal(signal.SIGINT)
    yield run
    signal.signal(signal.SIGINT, previous_sigint)


class TestTraceWithAsn:
    def test_asn_and_owner_are_printed(self, trace: Callable[..., str], whois_answers: list[str]) -> None:
        assert f"1\t{SERVER} ({SERVER}) [AS15169 GOOGLE, US] 12.500 ms\n" in trace("-a")

    def test_no_lookup_without_the_flag(self, trace: Callable[..., str], whois_answers: list[str]) -> None:
        assert f"1\t{SERVER} ({SERVER}) 12.500 ms\n" in trace()
        assert whois_answers == []

    def test_unrouted_address_prints_no_asn(self, monkeypatch: pytest.MonkeyPatch,
                                            trace: Callable[..., str]) -> None:
        monkeypatch.setattr(cymruwhois.Client, "_lookupmany_raw", lambda self, ips: iter([UNROUTED]))
        assert f"1\t{SERVER} ({SERVER}) 12.500 ms\n" in trace("-a")

    def test_failed_lookup_still_prints_the_hop(self, monkeypatch: pytest.MonkeyPatch,
                                                trace: Callable[..., str]) -> None:
        monkeypatch.setattr(cymruwhois.Client, "_lookupmany_raw", failing_lookup)
        assert f"1\t{SERVER} ({SERVER}) 12.500 ms\n" in trace("-a")

    def test_text_from_the_whois_service_is_escaped(self, monkeypatch: pytest.MonkeyPatch,
                                                    trace: Callable[..., str]) -> None:
        hostile = cymruwhois.record("15169\x1b[2J", SERVER, "192.0.2.0/24", "US", "EVIL\x1b]0;title\x07 ‮CORP")
        monkeypatch.setattr(cymruwhois.Client, "_lookupmany_raw", lambda self, ips: iter([hostile]))
        expected = f"1\t{SERVER} ({SERVER}) [AS15169\\027[2J EVIL\\027]0;title\\007 \\u202eCORP] 12.500 ms\n"
        assert expected in trace("-a")

    def test_trace_leaves_the_working_directory_alone(self, trace: Callable[..., str], whois_answers: list[str],
                                                      tmp_path: Path) -> None:
        planted = plant_cache(tmp_path)
        trace("-a")
        assert [path.name for path in tmp_path.iterdir()] == [CACHE_FILE]
        assert (tmp_path / CACHE_FILE).read_bytes() == planted
