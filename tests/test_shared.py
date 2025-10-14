#!/usr/bin/env python3

"""
Test suite for shared module functions
"""

import pytest
from dnsdiag.shared import valid_hostname


class TestHostnameValidation:
    """Test hostname validation function"""

    @pytest.mark.parametrize("hostname", [
        # Simple hostnames
        'localhost',
        'server1',
        'my-server',
        'web01',
        # FQDNs
        'example.com',
        'www.example.com',
        'mail.example.com',
        'sub.domain.example.com',
        # With trailing dot (FQDN notation)
        'example.com.',
        'www.example.com.',
        # Internationalized domain names (ASCII encoding)
        'xn--e1afmkfd.xn--p1ai',
        # Numeric in labels (allowed)
        'server123.example.com',
        '123server.example.com',
        # Single character labels
        'a.b.c',
        # Long but valid labels
        'very-long-subdomain-name-that-is-still-valid.example.com',
    ])
    def test_valid_hostnames(self, hostname):
        """Test valid hostnames are accepted"""
        assert valid_hostname(hostname), f"Should be valid: {hostname}"

    @pytest.mark.parametrize("hostname", [
        # Empty or whitespace
        '',
        '   ',
        # Starting with hyphen
        '-invalid.com',
        'example.-invalid.com',
        # Ending with hyphen
        'invalid-.com',
        'example.invalid-.com',
        # Starting with dot
        '.example.com',
        # Double dots
        'example..com',
        # Special characters
        'exam_ple.com',
        'exam ple.com',
        'exam@ple.com',
        'exam#ple.com',
        'exam$ple.com',
        # Trailing hyphen in label
        'example.com-',
    ])
    def test_invalid_hostnames(self, hostname):
        """Test invalid hostnames are rejected"""
        assert not valid_hostname(hostname), f"Should be invalid: {hostname}"

    def test_none_hostname(self):
        """Test None is rejected"""
        assert not valid_hostname(None)

    def test_non_string_hostname(self):
        """Test non-string types are rejected"""
        assert not valid_hostname(123)
        assert not valid_hostname(['example.com'])
        assert not valid_hostname({'hostname': 'example.com'})

    def test_max_label_length(self):
        """Test label length limit (63 characters)"""
        # Exactly 63 characters - should be valid
        assert valid_hostname('a' * 63 + '.com')

        # 64 characters - should be invalid
        assert not valid_hostname('a' * 64 + '.com')

    def test_max_total_length(self):
        """Test total hostname length limit (253 characters)"""
        # Exactly 253 characters - should be valid
        # 63 + 1(.) + 63 + 1(.) + 63 + 1(.) + 61 = 253
        hostname_253 = 'a' * 63 + '.' + 'b' * 63 + '.' + 'c' * 63 + '.' + 'd' * 61
        assert valid_hostname(hostname_253)
        assert len(hostname_253) == 253

        # 254 characters - should be invalid
        hostname_254 = 'a' * 254
        assert not valid_hostname(hostname_254)

    def test_single_character_labels(self):
        """Test single character hostnames and labels"""
        assert valid_hostname('a')
        assert valid_hostname('a.b')
        assert valid_hostname('a.b.c')

    def test_fqdn_with_trailing_dot(self):
        """Test FQDN notation with trailing dot"""
        assert valid_hostname('example.com.')
        assert valid_hostname('www.example.com.')

        # Only dot should be invalid
        assert not valid_hostname('.')
        assert not valid_hostname('..')

    def test_numeric_labels(self):
        """Test labels with numbers"""
        assert valid_hostname('server1.example.com')
        assert valid_hostname('123.example.com')
        assert valid_hostname('server123.example.com')
        assert valid_hostname('123server.example.com')

    def test_hyphen_in_middle(self):
        """Test hyphens in the middle of labels (valid)"""
        assert valid_hostname('my-server.example.com')
        assert valid_hostname('web-01.example.com')
        assert valid_hostname('a-b-c.example.com')

    def test_label_starting_rules(self):
        """Test label must start with alphanumeric"""
        assert not valid_hostname('-server.example.com')
        assert not valid_hostname('server.-sub.example.com')
        assert valid_hostname('server.1sub.example.com')
        assert valid_hostname('1server.example.com')

    def test_label_ending_rules(self):
        """Test label must end with alphanumeric"""
        assert not valid_hostname('server-.example.com')
        assert not valid_hostname('server.sub-.example.com')
        assert valid_hostname('server.sub1.example.com')
        assert valid_hostname('server1.example.com')

    def test_underscore_strict_mode(self):
        """Test underscores are rejected in strict mode (default)"""
        assert not valid_hostname('_dmarc.example.com')
        assert not valid_hostname('_acme-challenge.example.com')
        assert not valid_hostname('example_test.com')
        assert not valid_hostname('_service._proto.example.com')

    def test_underscore_dns_mode(self):
        """Test underscores are allowed with allow_underscore=True"""
        assert valid_hostname('_dmarc.example.com', allow_underscore=True)
        assert valid_hostname('_acme-challenge.example.com', allow_underscore=True)
        assert valid_hostname('_service._proto.example.com', allow_underscore=True)
        assert valid_hostname('_domainkey.example.com', allow_underscore=True)

        # Underscores can be at start but not end
        assert not valid_hostname('test_.example.com', allow_underscore=True)

        # Mixed with other valid chars
        assert valid_hostname('_test-123.example.com', allow_underscore=True)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
