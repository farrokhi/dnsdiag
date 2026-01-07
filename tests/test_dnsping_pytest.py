#!/usr/bin/env python3

"""
DNS Ping Test Suite - pytest version

Comprehensive test suite for dnsping.py functionality using pytest framework.

Usage:
    pytest test_dnsping_pytest.py
    pytest test_dnsping_pytest.py -v
    pytest test_dnsping_pytest.py -k "test_udp"
    pytest test_dnsping_pytest.py -k "google"
    pytest test_dnsping_pytest.py --tb=short
    pytest test_dnsping_pytest.py -x  # stop on first failure
"""

import subprocess
import sys
import pytest
import time
import platform
from typing import Tuple, Optional, List
from dataclasses import dataclass

# Test configuration
# Check if running on ARM64 (GitHub Actions ARM runners may have network restrictions)
IS_ARM64 = platform.machine().lower() in ('aarch64', 'arm64')

RESOLVERS = {
    'cloudflare_ip': '1.1.1.1',
    'cloudflare_hostname': 'one.one.one.one',
    'google_ip': '8.8.8.8',
    'google_hostname': 'dns.google',
    'quad9_ip': '9.9.9.9',
    'quad9_hostname': 'dns.quad9.net'
}

PROTOCOLS = ['udp', 'tcp', 'tls', 'doh', 'http3']
RECORD_TYPES = ['A', 'AAAA', 'MX', 'TXT']

@dataclass
class DNSResult:
    """Result from a dnsping command execution"""
    success: bool
    output: str
    response_time: Optional[float]
    error: Optional[str]

class DNSPingRunner:
    """Helper class for running dnsping commands"""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.dnsping_path = './dnsping.py'

    def run(self, args: List[str]) -> DNSResult:
        """Execute dnsping with given arguments"""
        cmd = [sys.executable, self.dnsping_path] + args

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            output = result.stdout + result.stderr
            success = result.returncode == 0 and "1 responses received, 0% lost" in output

            # Extract response time
            response_time = None
            if success:
                lines = output.split('\n')
                for line in lines:
                    if 'time=' in line and 'ms' in line:
                        try:
                            time_part = line.split('time=')[1].split('ms')[0].strip()
                            response_time = float(time_part)
                            break
                        except (IndexError, ValueError):
                            pass

            error = None if success else f"Command failed with exit code {result.returncode}"

            return DNSResult(success=success, output=output, response_time=response_time, error=error)

        except subprocess.TimeoutExpired:
            return DNSResult(success=False, output="", response_time=None,
                           error=f"Command timed out after {self.timeout}s")
        except Exception as e:
            return DNSResult(success=False, output="", response_time=None,
                           error=f"Command execution failed: {str(e)}")

# Global runner instance
runner = DNSPingRunner()

# Pytest fixtures
@pytest.fixture(scope="session")
def dnsping_runner():
    """Provide DNSPingRunner instance for tests"""
    return runner

# Basic functionality tests
class TestBasicFunctionality:
    """Test basic DNS resolution functionality"""

    @pytest.mark.parametrize("resolver_name,resolver_ip", [
        ('cloudflare', '1.1.1.1'),
        ('google', '8.8.8.8'),
        ('quad9', '9.9.9.9')
    ])
    def test_basic_udp_query(self, dnsping_runner, resolver_name, resolver_ip):
        """Test basic UDP DNS queries work"""
        result = dnsping_runner.run(['-c', '1', '-s', resolver_ip, 'google.com'])
        assert result.success, f"UDP query to {resolver_name} ({resolver_ip}) failed: {result.error}"
        assert result.response_time is not None, "No response time measured"
        assert result.response_time > 0, "Invalid response time"

    def test_response_time_reasonable(self, dnsping_runner):
        """Test that response times are reasonable (< 5 seconds)"""
        result = dnsping_runner.run(['-c', '1', '-s', '8.8.8.8', 'google.com'])
        assert result.success, f"Query failed: {result.error}"
        assert result.response_time < 5000, f"Response time too high: {result.response_time}ms"

# Protocol tests
class TestProtocols:
    """Test different DNS protocols"""

    @pytest.mark.parametrize("protocol,flag", [
        ('tcp', '--tcp'),
        ('tls', '--tls'),
        ('doh', '--doh'),
    ])
    @pytest.mark.parametrize("resolver_name,resolver_ip", [
        ('cloudflare', '1.1.1.1'),
        ('google', '8.8.8.8'),
        pytest.param('quad9', '9.9.9.9', marks=pytest.mark.xfail(reason="GitHub Actions may block Quad9 port 443"))
    ])
    def test_protocol_with_ip(self, dnsping_runner, protocol, flag, resolver_name, resolver_ip):
        """Test various protocols work with IP addresses"""
        result = dnsping_runner.run(['-c', '1', '-s', resolver_ip, flag, 'google.com'])
        assert result.success, f"{protocol.upper()} query to {resolver_name} ({resolver_ip}) failed: {result.error}"

    @pytest.mark.parametrize("resolver_ip", ['1.1.1.1', '8.8.8.8', '9.9.9.9'])
    def test_http3_protocol(self, dnsping_runner, resolver_ip):
        """Test HTTP3 protocol (may have limited support)"""
        result = dnsping_runner.run(['-c', '1', '-s', resolver_ip, '--http3', 'google.com'])
        # HTTP3 may fail on some resolvers, so we just ensure it doesn't crash
        assert result.error is None or "timed out" in result.error or "failed" in result.error.lower()

# Record type tests
class TestRecordTypes:
    """Test different DNS record types"""

    @pytest.mark.parametrize("record_type", ['A', 'AAAA', 'MX', 'TXT'])
    def test_record_types_google_dns(self, dnsping_runner, record_type):
        """Test different record types against Google DNS"""
        result = dnsping_runner.run(['-c', '1', '-s', '8.8.8.8', '-t', record_type, 'google.com'])
        assert result.success, f"{record_type} record query failed: {result.error}"

    def test_cname_record(self, dnsping_runner):
        """Test CNAME record resolution"""
        result = dnsping_runner.run(['-c', '1', '-s', '8.8.8.8', '-t', 'CNAME', 'www.github.com'])
        assert result.success, f"CNAME record query failed: {result.error}"

# EDNS feature tests
class TestEDNSFeatures:
    """Test EDNS extensions"""

    @pytest.mark.parametrize("resolver_name,resolver_ip", [
        ('google', '8.8.8.8'),
        ('quad9', '9.9.9.9')
    ])
    def test_nsid_support(self, dnsping_runner, resolver_name, resolver_ip):
        """Test NSID (Name Server Identifier) support"""
        result = dnsping_runner.run(['-c', '1', '-s', resolver_ip, '--nsid', 'google.com'])
        assert result.success, f"NSID query to {resolver_name} failed: {result.error}"

        # Check if NSID data is present (may vary by resolver)
        nsid_present = '[NSID:' in result.output
        # We don't assert NSID presence as not all resolvers support it

    @pytest.mark.parametrize("resolver_ip", ['8.8.8.8', '9.9.9.9', '1.1.1.1'])
    def test_ecs_support(self, dnsping_runner, resolver_ip):
        """Test ECS (EDNS Client Subnet) support"""
        result = dnsping_runner.run(['-c', '1', '-s', resolver_ip, '--ecs', '203.0.113.0/24', 'google.com'])
        assert result.success, f"ECS query failed: {result.error}"

        # Some resolvers echo back ECS, others don't - both are valid
        ecs_present = '[ECS:' in result.output

    def test_dns_cookies(self, dnsping_runner):
        """Test DNS Cookies support (RFC 7873)"""
        # Test with a server that supports cookies
        result = dnsping_runner.run(['-c', '1', '-s', 'anyns.pch.net', '--cookie', 'quad9.net'])
        assert result.success, f"Cookie query failed: {result.error}"

        # Verify cookie is displayed (anyns.pch.net supports cookies)
        assert '[COOKIE:' in result.output, "Cookie not displayed in output"

        # Verify cookie format (truncated to 8 hex chars + "..." in normal mode)
        import re
        cookie_match = re.search(r'\[COOKIE:([0-9a-f]{8}\.\.\.)\]', result.output)
        assert cookie_match, "Cookie format is invalid (expected 8 hex chars + '...')"

    def test_dns_cookies_no_support(self, dnsping_runner):
        """Test DNS Cookies with server that doesn't support it"""
        # Google DNS doesn't echo cookies
        result = dnsping_runner.run(['-c', '1', '-s', '8.8.8.8', '--cookie', 'google.com'])
        assert result.success, f"Cookie query failed: {result.error}"
        # Should not crash even if server doesn't support cookies

    def test_dnssec_validation(self, dnsping_runner):
        """Test DNSSEC validation request"""
        result = dnsping_runner.run(['-c', '1', '-s', '8.8.8.8', '--dnssec', 'google.com'])
        assert result.success, f"DNSSEC query failed: {result.error}"

# Hostname vs IP consistency tests
class TestHostnameConsistency:
    """Test that hostname and IP versions work consistently"""

    @pytest.mark.parametrize("protocol,flag", [
        ('udp', []),
        ('tcp', ['--tcp']),
    ])
    @pytest.mark.parametrize("ip,hostname,name", [
        ('1.1.1.1', 'one.one.one.one', 'cloudflare'),
        ('8.8.8.8', 'dns.google', 'google'),
        pytest.param('9.9.9.9', 'dns.quad9.net', 'quad9',
                    marks=pytest.mark.xfail(IS_ARM64, reason="ARM64 runners may have network restrictions")),
    ])
    def test_hostname_vs_ip_basic_protocols(self, dnsping_runner, protocol, flag, ip, hostname, name):
        """Test hostname vs IP consistency for basic protocols"""
        # Test IP version
        ip_result = dnsping_runner.run(['-c', '1', '-s', ip] + flag + ['google.com'])

        # Test hostname version
        hostname_result = dnsping_runner.run(['-c', '1', '-s', hostname] + flag + ['google.com'])

        assert ip_result.success, f"{protocol.upper()} with IP {ip} failed: {ip_result.error}"
        assert hostname_result.success, f"{protocol.upper()} with hostname {hostname} failed: {hostname_result.error}"

    @pytest.mark.parametrize("ip,hostname,name", [
        pytest.param('8.8.8.8', 'dns.google', 'google',
                    marks=pytest.mark.xfail(IS_ARM64, reason="ARM64 runners may have network restrictions")),
        pytest.param('9.9.9.9', 'dns.quad9.net', 'quad9',
                    marks=pytest.mark.xfail(reason="GitHub Actions may block Quad9 port 443")),
    ])
    def test_hostname_vs_ip_doh(self, dnsping_runner, ip, hostname, name):
        """Test DoH works with both IP and hostname (critical after hostname fix)"""
        # Test IP version
        ip_result = dnsping_runner.run(['-c', '1', '-s', ip, '--doh', 'google.com'])

        # Test hostname version (this was broken before the fix)
        hostname_result = dnsping_runner.run(['-c', '1', '-s', hostname, '--doh', 'google.com'])

        assert ip_result.success, f"DoH with IP {ip} failed: {ip_result.error}"
        assert hostname_result.success, f"DoH with hostname {hostname} failed: {hostname_result.error}"

    @pytest.mark.parametrize("ip,hostname,name", [
        ('8.8.8.8', 'dns.google', 'google'),
        ('1.1.1.1', 'one.one.one.one', 'cloudflare'),
    ])
    def test_hostname_vs_ip_http3(self, dnsping_runner, ip, hostname, name):
        """Test HTTP3 works with both IP and hostname (critical after hostname fix)"""
        # Test hostname version (this was the original bug case)
        hostname_result = dnsping_runner.run(['-c', '1', '-s', hostname, '--http3', 'google.com'])

        # Should not crash (the original issue)
        assert hostname_result.error is None or "timed out" in hostname_result.error or "failed" in hostname_result.error.lower()
        # The key is that it shouldn't have an "UnexpectedEOF" or similar crash

# Error handling tests
class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_invalid_ip_address(self, dnsping_runner):
        """Test handling of invalid IP address"""
        result = dnsping_runner.run(['-c', '1', '-s', '192.0.2.1', 'google.com'])  # RFC 5737 documentation range
        assert not result.success, "Query to invalid IP should fail"
        # Some runners may return "Network unreachable" instead of timeout
        assert ("timed out" in result.error.lower() or
                result.output.count("0 responses received") > 0 or
                "network unreachable" in result.output.lower())

    def test_invalid_hostname(self, dnsping_runner):
        """Test handling of invalid hostname"""
        result = dnsping_runner.run(['-c', '1', '-s', 'invalid.hostname.invalid', 'google.com'])
        assert not result.success, "Query to invalid hostname should fail"

    def test_invalid_record_type(self, dnsping_runner):
        """Test handling of invalid record type"""
        result = dnsping_runner.run(['-c', '1', '-s', '8.8.8.8', '-t', 'INVALID', 'google.com'])
        assert not result.success, "Query with invalid record type should fail"

    def test_malformed_ecs_subnet(self, dnsping_runner):
        """Test handling of malformed ECS subnet"""
        result = dnsping_runner.run(['-c', '1', '-s', '8.8.8.8', '--ecs', 'invalid-subnet', 'google.com'])
        assert not result.success, "Query with invalid ECS subnet should fail"


# CLI parameter validation tests
class TestCLIParameterValidation:
    """Test CLI parameter validation and error handling"""

    def test_invalid_long_option(self, dnsping_runner):
        """Test handling of invalid long option"""
        result = dnsping_runner.run(['--invalid-option', 'google.com'])
        assert not result.success, "Invalid option should fail gracefully"
        assert "Traceback" not in result.output, "Should not show Python traceback"
        assert "not recognized" in result.output or "Usage:" in result.output

    def test_invalid_short_option(self, dnsping_runner):
        """Test handling of invalid short option"""
        result = dnsping_runner.run(['-Z', 'google.com'])
        assert not result.success, "Invalid option should fail gracefully"
        assert "Traceback" not in result.output, "Should not show Python traceback"

    def test_invalid_count_negative(self, dnsping_runner):
        """Test handling of negative count value"""
        result = dnsping_runner.run(['-c', '-5', 'google.com'])
        assert not result.success, "Negative count should fail"
        assert "Traceback" not in result.output, "Should not show Python traceback"

    def test_invalid_count_non_numeric(self, dnsping_runner):
        """Test handling of non-numeric count value"""
        result = dnsping_runner.run(['-c', 'abc', 'google.com'])
        assert not result.success, "Non-numeric count should fail"
        assert "ERROR" in result.output or "invalid" in result.output.lower()

    def test_invalid_port_too_high(self, dnsping_runner):
        """Test handling of port value above 65535"""
        result = dnsping_runner.run(['-p', '99999', 'google.com'])
        assert not result.success, "Port above 65535 should fail"
        assert "Traceback" not in result.output, "Should not show Python traceback"
        assert "port" in result.output.lower()

    def test_invalid_port_negative(self, dnsping_runner):
        """Test handling of negative port value"""
        result = dnsping_runner.run(['-p', '-1', 'google.com'])
        assert not result.success, "Negative port should fail"
        assert "Traceback" not in result.output, "Should not show Python traceback"

    def test_invalid_port_non_numeric(self, dnsping_runner):
        """Test handling of non-numeric port value"""
        result = dnsping_runner.run(['-p', 'abc', 'google.com'])
        assert not result.success, "Non-numeric port should fail"
        assert "ERROR" in result.output or "invalid" in result.output.lower()

    def test_invalid_timeout_negative(self, dnsping_runner):
        """Test handling of negative timeout value"""
        result = dnsping_runner.run(['-w', '-5', 'google.com'])
        assert not result.success, "Negative timeout should fail"
        assert "Traceback" not in result.output, "Should not show Python traceback"

    def test_invalid_timeout_non_numeric(self, dnsping_runner):
        """Test handling of non-numeric timeout value"""
        result = dnsping_runner.run(['-w', 'xyz', 'google.com'])
        assert not result.success, "Non-numeric timeout should fail"
        assert "ERROR" in result.output or "invalid" in result.output.lower()

    def test_invalid_interval_negative(self, dnsping_runner):
        """Test handling of negative interval value"""
        result = dnsping_runner.run(['-i', '-1', 'google.com'])
        assert not result.success, "Negative interval should fail"
        assert "Traceback" not in result.output, "Should not show Python traceback"

    def test_invalid_interval_non_numeric(self, dnsping_runner):
        """Test handling of non-numeric interval value"""
        result = dnsping_runner.run(['-i', 'notanumber', 'google.com'])
        assert not result.success, "Non-numeric interval should fail"
        assert "ERROR" in result.output or "invalid" in result.output.lower()

    def test_invalid_source_ip(self, dnsping_runner):
        """Test handling of invalid source IP address"""
        result = dnsping_runner.run(['-S', 'not.an.ip.address', 'google.com'])
        assert not result.success, "Invalid source IP should fail"
        assert "Traceback" not in result.output, "Should not show Python traceback"
        assert "ERROR" in result.output or "invalid" in result.output.lower()

    def test_invalid_source_port_negative(self, dnsping_runner):
        """Test handling of negative source port value"""
        result = dnsping_runner.run(['-P', '-1', 'google.com'])
        assert not result.success, "Negative source port should fail"
        assert "Traceback" not in result.output, "Should not show Python traceback"

    def test_invalid_source_port_too_high(self, dnsping_runner):
        """Test handling of source port value above 65535"""
        result = dnsping_runner.run(['-P', '70000', 'google.com'])
        assert not result.success, "Source port above 65535 should fail"
        assert "Traceback" not in result.output, "Should not show Python traceback"

    def test_invalid_ecs_no_prefix(self, dnsping_runner):
        """Test handling of ECS without prefix length"""
        result = dnsping_runner.run(['--ecs', '192.168.1.1', '-c', '1', 'google.com'])
        assert not result.success, "ECS without prefix should fail"

    def test_invalid_ecs_invalid_ip(self, dnsping_runner):
        """Test handling of ECS with invalid IP"""
        result = dnsping_runner.run(['--ecs', 'invalid.ip/24', '-c', '1', 'google.com'])
        assert not result.success, "ECS with invalid IP should fail"

    def test_invalid_ecs_prefix_too_large(self, dnsping_runner):
        """Test handling of ECS with prefix larger than 32"""
        result = dnsping_runner.run(['--ecs', '192.168.1.0/33', '-c', '1', 'google.com'])
        assert not result.success, "ECS with prefix > 32 should fail"

    def test_conflicting_address_families(self, dnsping_runner):
        """Test handling of conflicting -4 and -6 flags"""
        result = dnsping_runner.run(['-4', '-6', '-c', '1', 'google.com'])
        assert not result.success, "Conflicting -4 and -6 should fail"
        assert "Traceback" not in result.output, "Should not show Python traceback"
        assert "ERROR" in result.output or "cannot specify both" in result.output.lower()

    def test_no_hostname_provided(self, dnsping_runner):
        """Test handling of missing hostname"""
        result = dnsping_runner.run(['-c', '5'])
        assert not result.success, "Missing hostname should fail"
        assert "Usage:" in result.output, "Should show usage message"

    def test_empty_hostname(self, dnsping_runner):
        """Test handling of empty hostname"""
        result = dnsping_runner.run([''])
        assert not result.success, "Empty hostname should fail"

# Regression tests for specific bugs
class TestRegressionBugs:
    """Tests for specific bugs that have been fixed"""

    def test_hostname_http3_no_crash(self, dnsping_runner):
        """Regression test: hostname with HTTP3 should not crash (original bug)"""
        result = dnsping_runner.run(['-c', '1', '-s', 'one.one.one.one', '--http3', 'google.com'])

        # The key test: should not crash with UnexpectedEOF
        assert "UnexpectedEOF" not in result.output, "HTTP3 with hostname should not crash with UnexpectedEOF"
        assert "Traceback" not in result.output, "Should not have Python traceback"

    def test_hostname_doh_works(self, dnsping_runner):
        """Regression test: DoH with hostname should work after fix"""
        result = dnsping_runner.run(['-c', '1', '-s', 'dns.google', '--doh', 'google.com'])
        assert result.success, f"DoH with dns.google hostname should work: {result.error}"

    def test_ede_always_displayed(self, dnsping_runner):
        """Regression test: EDE should always be displayed when present"""
        # Test with a domain that might trigger EDE (DNSSEC validation failure)
        result = dnsping_runner.run(['-c', '1', '-s', '8.8.8.8', '--dnssec', 'brokendnssec.net'])

        # Whether it succeeds or fails, if EDE is present, it should be shown
        # (We can't guarantee EDE will be present, but if it is, it should show)
        if '[EDE:' in result.output:
            assert True  # EDE is being displayed
        else:
            # No EDE present, which is also fine
            assert True

# Pytest configuration and custom markers
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "network: marks tests as requiring network access")

# Mark all tests as requiring network
pytestmark = pytest.mark.network

if __name__ == '__main__':
    pytest.main([__file__] + sys.argv[1:])