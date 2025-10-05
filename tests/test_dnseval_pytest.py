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
        cmd = ['python3', self.dnseval_path] + args
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
        assert 'Invalid record type' in result.output


pytestmark = pytest.mark.network


if __name__ == '__main__':
    pytest.main([__file__] + sys.argv[1:])
