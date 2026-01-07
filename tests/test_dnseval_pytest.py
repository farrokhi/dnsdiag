#!/usr/bin/env python3

"""
DNS Eval Test Suite - pytest version

Comprehensive test suite for dnseval.py functionality using pytest framework.

Usage:
    pytest tests/test_dnseval_pytest.py
    pytest tests/test_dnseval_pytest.py -v
    pytest tests/test_dnseval_pytest.py -k "warmup"
"""

import subprocess
import sys
import pytest
import json
from typing import Optional, List
from dataclasses import dataclass

RESOLVERS = {
    'google': '8.8.8.8',
    'cloudflare': '1.1.1.1',
    'quad9': '9.9.9.9'
}


@dataclass
class DNSEvalResult:
    """Result from a dnseval command execution"""
    success: bool
    output: str
    has_results: bool
    warmup_shown: bool
    error: Optional[str]


class DNSEvalRunner:
    """Helper class for running dnseval commands"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.dnseval_path = './dnseval.py'

    def run(self, args: List[str], stdin: Optional[bytes] = None) -> DNSEvalResult:
        """Run dnseval with given arguments"""
        cmd = [sys.executable, self.dnseval_path] + args
        try:
            stdin_text = stdin.decode('utf-8') if stdin else None
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                input=stdin_text,
                timeout=self.timeout
            )

            output = result.stdout + result.stderr
            success = result.returncode == 0
            has_results = 'avg(ms)' in output and 'min(ms)' in output
            warmup_shown = 'Warming up DNS caches' in output
            error = result.stderr if result.stderr and result.returncode != 0 else None

            return DNSEvalResult(
                success=success,
                output=output,
                has_results=has_results,
                warmup_shown=warmup_shown,
                error=error
            )
        except subprocess.TimeoutExpired:
            return DNSEvalResult(
                success=False,
                output="",
                has_results=False,
                warmup_shown=False,
                error="Command timed out"
            )
        except Exception as e:
            return DNSEvalResult(
                success=False,
                output="",
                has_results=False,
                warmup_shown=False,
                error=str(e)
            )


@pytest.fixture
def runner():
    """Fixture providing DNSEvalRunner instance"""
    return DNSEvalRunner()


class TestBasicFunctionality:
    """Basic functionality tests for dnseval"""

    def test_basic_evaluation_single_server(self, runner):
        """Test basic evaluation with single server"""
        result = runner.run(['-c', '2', '-f', '-', 'google.com'],
                           stdin=b'8.8.8.8\n')
        assert result.success, f"Evaluation failed: {result.error}"
        assert result.has_results, "Expected results in output"
        assert '8.8.8.8' in result.output

    @pytest.mark.parametrize("resolver_name,resolver_ip", [
        ('google', RESOLVERS['google']),
        ('cloudflare', RESOLVERS['cloudflare']),
        ('quad9', RESOLVERS['quad9']),
    ])
    def test_specific_servers(self, runner, resolver_name, resolver_ip):
        """Test evaluation with specific DNS servers"""
        result = runner.run(['-c', '2', '-f', '-', 'google.com'],
                           stdin=resolver_ip.encode() + b'\n')
        assert result.success, f"Evaluation of {resolver_name} failed: {result.error}"
        assert resolver_ip in result.output

    def test_multiple_servers(self, runner):
        """Test evaluation with multiple servers"""
        servers = '\n'.join([RESOLVERS['google'], RESOLVERS['cloudflare']])
        result = runner.run(['-c', '2', '-f', '-', 'google.com'],
                           stdin=servers.encode())
        assert result.success, f"Multi-server evaluation failed: {result.error}"
        assert RESOLVERS['google'] in result.output
        assert RESOLVERS['cloudflare'] in result.output


class TestWarmupFeature:
    """Tests for cache warmup feature"""

    def test_warmup_enabled_by_default(self, runner):
        """Test warmup is enabled by default"""
        result = runner.run(['-c', '2', '-f', '-', 'google.com'],
                           stdin=b'8.8.8.8\n')
        assert result.success, f"Evaluation failed: {result.error}"
        assert result.warmup_shown, "Expected warmup message in output"
        assert 'Warming up DNS caches' in result.output

    def test_skip_warmup_flag(self, runner):
        """Test --skip-warmup disables warmup"""
        result = runner.run(['--skip-warmup', '-c', '2', '-f', '-', 'google.com'],
                           stdin=b'8.8.8.8\n')
        assert result.success, f"Evaluation failed: {result.error}"
        assert not result.warmup_shown, "Warmup should be disabled"
        assert 'Warming up DNS caches' not in result.output

    def test_warmup_with_multiple_servers(self, runner):
        """Test warmup works with multiple servers"""
        servers = '\n'.join([RESOLVERS['google'], RESOLVERS['cloudflare'], RESOLVERS['quad9']])
        result = runner.run(['-c', '2', '-f', '-', 'google.com'],
                           stdin=servers.encode())
        assert result.success, f"Multi-server evaluation failed: {result.error}"
        assert result.warmup_shown, "Expected warmup message"


class TestProtocols:
    """Tests for different DNS protocols"""

    def test_tcp_protocol(self, runner):
        """Test evaluation with TCP protocol"""
        result = runner.run(['--tcp', '-c', '2', '-f', '-', 'google.com'],
                           stdin=b'8.8.8.8\n')
        assert result.success, f"TCP evaluation failed: {result.error}"
        assert result.has_results

    def test_tls_protocol(self, runner):
        """Test evaluation with TLS protocol"""
        result = runner.run(['--tls', '-c', '2', '-f', '-', 'google.com'],
                           stdin=b'8.8.8.8\n')
        assert result.success, f"TLS evaluation failed: {result.error}"
        assert result.has_results

    def test_quic_protocol(self, runner):
        """Test evaluation with QUIC protocol"""
        result = runner.run(['--quic', '-c', '2', '-f', '-', 'google.com'],
                           stdin=b'94.140.14.14\n')
        assert result.success, f"QUIC evaluation failed: {result.error}"
        assert result.has_results

    def test_http3_protocol(self, runner):
        """Test evaluation with HTTP/3 protocol"""
        result = runner.run(['--http3', '-c', '2', '-f', '-', 'google.com'],
                           stdin=b'1.1.1.1\n')
        assert result.success, f"HTTP/3 evaluation failed: {result.error}"
        assert result.has_results


class TestRecordTypes:
    """Tests for different DNS record types"""

    @pytest.mark.parametrize("record_type", ['A', 'AAAA', 'MX'])
    def test_record_types(self, runner, record_type):
        """Test evaluation with different record types"""
        result = runner.run(['-c', '2', '-t', record_type, '-f', '-', 'google.com'],
                           stdin=b'8.8.8.8\n')
        assert result.success, f"{record_type} query failed: {result.error}"
        assert result.has_results


class TestErrorHandling:
    """Tests for error handling"""

    def test_invalid_record_type(self, runner):
        """Test handling of invalid record type"""
        result = runner.run(['-c', '2', '-t', 'INVALID', '-f', '-', 'google.com'],
                           stdin=b'8.8.8.8\n')
        assert not result.success, "Should fail with invalid record type"
        assert 'invalid record type' in result.output


class TestCLIParameterValidation:
    """Test CLI parameter validation and error handling"""

    def test_invalid_long_option(self, runner):
        """Test handling of invalid long option"""
        result = runner.run(['--invalid-option', 'google.com'])
        assert not result.success, "Invalid option should fail gracefully"
        assert "Traceback" not in result.output, "Should not show Python traceback"

    def test_invalid_short_option(self, runner):
        """Test handling of invalid short option"""
        result = runner.run(['-Z', 'google.com'])
        assert not result.success, "Invalid option should fail gracefully"
        assert "Traceback" not in result.output, "Should not show Python traceback"

    def test_invalid_count_negative(self, runner):
        """Test handling of negative count value"""
        result = runner.run(['-c', '-5', 'google.com'])
        assert not result.success, "Negative count should fail"
        assert "Traceback" not in result.output, "Should not show Python traceback"

    def test_invalid_count_zero(self, runner):
        """Test handling of zero count value"""
        result = runner.run(['-c', '0', 'google.com'])
        assert not result.success, "Zero count should fail"
        assert "positive" in result.output.lower() or "ERROR" in result.output

    def test_invalid_count_non_numeric(self, runner):
        """Test handling of non-numeric count value"""
        result = runner.run(['-c', 'abc', 'google.com'])
        assert not result.success, "Non-numeric count should fail"
        assert "ERROR" in result.output or "invalid" in result.output.lower()

    def test_invalid_port_too_high(self, runner):
        """Test handling of port value above 65535"""
        result = runner.run(['-p', '99999', 'google.com'])
        assert not result.success, "Port above 65535 should fail"
        assert "Traceback" not in result.output, "Should not show Python traceback"
        assert "port" in result.output.lower()

    def test_invalid_port_negative(self, runner):
        """Test handling of negative port value"""
        result = runner.run(['-p', '-1', 'google.com'])
        assert not result.success, "Negative port should fail"
        assert "Traceback" not in result.output, "Should not show Python traceback"

    def test_invalid_port_non_numeric(self, runner):
        """Test handling of non-numeric port value"""
        result = runner.run(['-p', 'abc', 'google.com'])
        assert not result.success, "Non-numeric port should fail"
        assert "ERROR" in result.output or "invalid" in result.output.lower()

    def test_invalid_wait_negative(self, runner):
        """Test handling of negative wait value"""
        result = runner.run(['-w', '-5', 'google.com'])
        assert not result.success, "Negative wait should fail"
        assert "Traceback" not in result.output, "Should not show Python traceback"

    def test_invalid_wait_non_numeric(self, runner):
        """Test handling of non-numeric wait value"""
        result = runner.run(['-w', 'xyz', 'google.com'])
        assert not result.success, "Non-numeric wait should fail"
        assert "ERROR" in result.output or "invalid" in result.output.lower()

    def test_invalid_source_ip(self, runner):
        """Test handling of invalid source IP address"""
        result = runner.run(['-S', 'not.an.ip', 'google.com'])
        assert not result.success, "Invalid source IP should fail"
        assert "Traceback" not in result.output, "Should not show Python traceback"
        assert "ERROR" in result.output or "invalid" in result.output.lower()

    def test_no_hostname_provided(self, runner):
        """Test handling of missing hostname"""
        result = runner.run(['-c', '5'])
        assert not result.success, "Missing hostname should fail"
        assert "Usage:" in result.output, "Should show usage message"

    def test_empty_hostname(self, runner):
        """Test handling of empty hostname"""
        result = runner.run([''])
        assert not result.success, "Empty hostname should fail"

    def test_invalid_hostname_double_dots(self, runner):
        """Test handling of hostname with double dots"""
        result = runner.run(['invalid..hostname'])
        assert not result.success, "Hostname with double dots should fail"
        assert "invalid hostname" in result.output.lower()

    def test_invalid_hostname_special_chars(self, runner):
        """Test handling of hostname with special characters"""
        result = runner.run(['exam@ple.com'])
        assert not result.success, "Hostname with @ should fail"
        assert "invalid hostname" in result.output.lower()


class TestJSONOutput:
    """Tests for JSON output functionality"""

    def test_json_output_format(self, runner):
        """Test JSON output is valid and contains expected fields"""
        result = runner.run(['--skip-warmup', '-c', '2', '-f', '-', '-j', '-', 'google.com'],
                           stdin=b'8.8.8.8\n')
        assert result.success, f"JSON evaluation failed: {result.error}"

        # Parse JSON output
        try:
            data = json.loads(result.output)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON output: {e}\nOutput: {result.output}")

        # Verify structure
        assert 'hostname' in data, "Missing hostname field"
        assert 'data' in data, "Missing data field"
        assert data['hostname'] == 'google.com'

        # Verify data fields
        dns_data = data['data']
        expected_fields = ['hostname', 'timestamp', 'r_min', 'r_avg', 'r_max',
                          'resolver', 'r_lost_percent', 's_ttl', 'text_flags',
                          'flags', 'ednsflags', 'rcode', 'rcode_text']
        for field in expected_fields:
            assert field in dns_data, f"Missing field: {field}"

        # Verify data types
        assert isinstance(dns_data['r_avg'], float)
        assert isinstance(dns_data['flags'], int)
        assert isinstance(dns_data['ednsflags'], int)
        assert dns_data['resolver'] == '8.8.8.8'

    def test_json_output_with_dnssec(self, runner):
        """Test JSON output with DNSSEC includes EDNS flags"""
        result = runner.run(['--skip-warmup', '--dnssec', '-c', '2', '-f', '-', '-j', '-', 'google.com'],
                           stdin=b'8.8.8.8\n')
        assert result.success, f"DNSSEC JSON evaluation failed: {result.error}"

        # Parse JSON output
        data = json.loads(result.output)
        dns_data = data['data']

        # Verify EDNS flags are present
        assert 'ednsflags' in dns_data, "Missing ednsflags field"
        assert dns_data['ednsflags'] != 0, "EDNS flags should be set with --dnssec"

        # Verify DO flag in text representation
        assert 'DO' in dns_data['text_flags'], "DO flag should be in text_flags with --dnssec"

    def test_json_output_multiple_servers(self, runner):
        """Test JSON output with multiple servers produces multiple JSON objects"""
        servers = '\n'.join([RESOLVERS['google'], RESOLVERS['cloudflare']])
        result = runner.run(['--skip-warmup', '-c', '2', '-f', '-', '-j', '-', 'google.com'],
                           stdin=servers.encode())
        assert result.success, f"Multi-server JSON evaluation failed: {result.error}"

        # Should contain two JSON objects (one per line or concatenated)
        # Note: dnseval currently outputs concatenated JSON objects, not a JSON array
        assert RESOLVERS['google'] in result.output
        assert RESOLVERS['cloudflare'] in result.output


pytestmark = pytest.mark.network


if __name__ == '__main__':
    pytest.main([__file__] + sys.argv[1:])
