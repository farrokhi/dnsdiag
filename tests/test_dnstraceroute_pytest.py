#!/usr/bin/env python3

"""
DNS Traceroute Test Suite - pytest version

Comprehensive test suite for dnstraceroute.py functionality using pytest framework.
Tests IPv4/IPv6 support, address family handling, and various CLI options.

Usage:
    pytest tests/test_dnstraceroute_pytest.py
    pytest tests/test_dnstraceroute_pytest.py -v
    pytest tests/test_dnstraceroute_pytest.py -k "ipv6"
    pytest tests/test_dnstraceroute_pytest.py::TestBasicFunctionality
"""

import subprocess
import pytest
import time
from typing import Tuple, Optional
from dataclasses import dataclass

# Test configuration
RESOLVERS_IPV4 = {
    'google': '8.8.8.8',
    'cloudflare': '1.1.1.1',
    'quad9': '9.9.9.9'
}

RESOLVERS_IPV6 = {
    'google': '2001:4860:4860::8888',
    'cloudflare': '2606:4700:4700::1111',
    'quad9': '2620:fe::fe'
}

RESOLVER_HOSTNAMES = {
    'google': 'dns.google',
    'cloudflare': 'one.one.one.one'
}

@dataclass
class TracerouteResult:
    """Result from a dnstraceroute command execution"""
    success: bool
    output: str
    has_hops: bool
    error: Optional[str]

class DNSTracerouteRunner:
    """Helper class for running dnstraceroute commands"""

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.dnstraceroute_path = './dnstraceroute.py'

    def run(self, args: list) -> TracerouteResult:
        """Run dnstraceroute with given arguments"""
        cmd = ['python3', self.dnstraceroute_path] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            output = result.stdout + result.stderr
            success = result.returncode == 0
            has_hops = bool(result.stdout and '\t' in result.stdout)
            error = result.stderr if result.stderr else None
            
            return TracerouteResult(
                success=success,
                output=output,
                has_hops=has_hops,
                error=error
            )
        except subprocess.TimeoutExpired:
            return TracerouteResult(
                success=False,
                output="",
                has_hops=False,
                error="Command timed out"
            )
        except Exception as e:
            return TracerouteResult(
                success=False,
                output="",
                has_hops=False,
                error=str(e)
            )

@pytest.fixture
def runner():
    """Fixture providing DNSTracerouteRunner instance"""
    return DNSTracerouteRunner()


class TestBasicFunctionality:
    """Basic functionality tests for dnstraceroute"""

    @pytest.mark.parametrize("resolver_name,resolver_ip", [
        ('google', RESOLVERS_IPV4['google']),
        ('cloudflare', RESOLVERS_IPV4['cloudflare']),
    ])
    def test_basic_ipv4_traceroute(self, runner, resolver_name, resolver_ip):
        """Test basic IPv4 traceroute"""
        result = runner.run(['-c', '3', '-s', resolver_ip, 'google.com'])
        assert result.success, f"IPv4 traceroute failed: {result.error}"
        assert "DNS:" in result.output
        assert resolver_ip in result.output

    @pytest.mark.parametrize("resolver_name,resolver_ip", [
        ('google', RESOLVERS_IPV6['google']),
        ('cloudflare', RESOLVERS_IPV6['cloudflare']),
    ])
    def test_basic_ipv6_traceroute(self, runner, resolver_name, resolver_ip):
        """Test basic IPv6 traceroute"""
        result = runner.run(['-c', '3', '-s', resolver_ip, 'google.com'])
        assert result.success, f"IPv6 traceroute failed: {result.error}"
        assert "DNS:" in result.output
        assert resolver_ip in result.output


class TestAddressFamilyHandling:
    """Tests for IPv4/IPv6 address family handling"""

    def test_ipv4_flag_with_hostname(self, runner):
        """Test -4 flag forces IPv4 resolution of hostname"""
        result = runner.run(['-4', '-c', '2', '-s', 'dns.google', 'google.com'])
        assert result.success, f"IPv4 flag test failed: {result.error}"
        assert "DNS:" in result.output
        # Should resolve to IPv4 address
        assert ("8.8.8.8" in result.output or "8.8.4.4" in result.output)

    def test_ipv6_flag_with_hostname(self, runner):
        """Test -6 flag forces IPv6 resolution of hostname"""
        result = runner.run(['-6', '-c', '2', '-s', 'dns.google', 'google.com'])
        assert result.success, f"IPv6 flag test failed: {result.error}"
        assert "DNS:" in result.output
        # Should resolve to IPv6 address
        assert "2001:4860:4860:" in result.output

    def test_conflicting_ipv4_server_with_ipv6_flag(self, runner):
        """Test error when -6 flag is used with IPv4 server"""
        result = runner.run(['-6', '-s', '8.8.8.8', 'google.com'])
        assert not result.success, "Should fail with conflicting flags"
        assert "ERROR" in result.output

    def test_conflicting_ipv6_server_with_ipv4_flag(self, runner):
        """Test error when -4 flag is used with IPv6 server"""
        result = runner.run(['-4', '-s', '2001:4860:4860::8888', 'google.com'])
        assert not result.success, "Should fail with conflicting flags"
        assert "ERROR" in result.output

    def test_auto_detect_ipv4(self, runner):
        """Test auto-detection of IPv4 address family"""
        result = runner.run(['-c', '2', '-s', '8.8.8.8', 'google.com'])
        assert result.success, f"Auto-detect IPv4 failed: {result.error}"
        assert "8.8.8.8" in result.output

    def test_auto_detect_ipv6(self, runner):
        """Test auto-detection of IPv6 address family"""
        result = runner.run(['-c', '2', '-s', '2001:4860:4860::8888', 'google.com'])
        assert result.success, f"Auto-detect IPv6 failed: {result.error}"
        assert "2001:4860:4860::8888" in result.output


class TestCLIOptions:
    """Tests for various CLI options"""

    @pytest.mark.parametrize("resolver", [
        RESOLVERS_IPV4['google'],
        RESOLVERS_IPV6['google']
    ])
    def test_no_hostname_resolution(self, runner, resolver):
        """Test -n flag disables hostname resolution"""
        result = runner.run(['-n', '-c', '2', '-s', resolver, 'google.com'])
        assert result.success, f"No hostname resolution test failed: {result.error}"
        assert result.has_hops or '*' in result.output

    def test_hop_count_limit(self, runner):
        """Test -c flag limits number of hops"""
        result = runner.run(['-c', '2', '-s', '8.8.8.8', 'google.com'])
        assert result.success, f"Hop count limit test failed: {result.error}"
        # Count hop lines (lines with tab character and starting with digit)
        hop_lines = [l for l in result.output.split('\n') if l and l[0].isdigit() and '\t' in l]
        assert len(hop_lines) <= 2, f"Expected max 2 hops, got {len(hop_lines)}"

    def test_quiet_mode(self, runner):
        """Test -q flag enables quiet mode"""
        result = runner.run(['-q', '-c', '2', '-s', '8.8.8.8', 'google.com'])
        assert result.success, f"Quiet mode test failed: {result.error}"
        # In quiet mode, should still show hop lines but less verbose
        assert result.has_hops


class TestSourceIPValidation:
    """Tests for source IP address validation"""

    def test_ipv4_source_with_ipv4_target(self, runner):
        """Test valid IPv4 source with IPv4 target (may fail without privilege)"""
        # This test might fail due to permissions, which is acceptable
        result = runner.run(['-S', '127.0.0.1', '-c', '1', '-s', '8.8.8.8', 'google.com'])
        # Either succeeds or fails with permission error
        if not result.success:
            assert ("ERROR" in result.output or "Permission" in result.output)

    def test_ipv4_source_with_ipv6_target(self, runner):
        """Test error when IPv4 source is used with IPv6 target"""
        result = runner.run(['-S', '127.0.0.1', '-s', '2001:4860:4860::8888', 'google.com'])
        assert not result.success, "Should fail with mismatched address families"
        assert "ERROR" in result.output


class TestErrorHandling:
    """Tests for error handling"""

    def test_invalid_server_address(self, runner):
        """Test handling of invalid server address"""
        result = runner.run(['-c', '1', '-s', 'not.a.valid.ip.address', 'google.com'])
        assert not result.success, "Should fail with invalid server"
        assert "ERROR" in result.output

    def test_invalid_record_type(self, runner):
        """Test handling of invalid record type"""
        result = runner.run(['-c', '1', '-s', '8.8.8.8', '-t', 'INVALID', 'google.com'])
        assert not result.success, "Should fail with invalid record type"
        assert "ERROR" in result.output


class TestRegressionBugs:
    """Tests for specific regression bugs and fixes"""

    def test_ipv6_support_issue_45(self, runner):
        """Test IPv6 support works (GitHub issue #45)"""
        result = runner.run(['-c', '3', '-s', '2001:4860:4860::8888', 'google.com'])
        assert result.success, "IPv6 should work (issue #45)"
        assert "2001:4860:4860::8888" in result.output

# Mark all tests as requiring network
pytestmark = pytest.mark.network


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
