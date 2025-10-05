# dnsdiag Test Suite

Comprehensive pytest-based test suites for dnsdiag tools.

## Overview

This directory contains automated tests for:
- **dnsping** - DNS latency and response testing
- **dnstraceroute** - DNS path tracing with IPv4/IPv6 support

## Quick Start

```bash
# Install dependencies
pip install -r tests/test-requirements.txt

# Run all tests
pytest tests/

# Run specific tool tests
pytest tests/test_dnsping_pytest.py
pytest tests/test_dnstraceroute_pytest.py

# Run with verbose output
pytest tests/ -v
```

## Installation

```bash
# Install pytest (required)
pip install pytest

# Install all test dependencies
pip install -r tests/test-requirements.txt
```

## Test Suites

### dnsping Tests (`test_dnsping_pytest.py`)

Tests DNS ping functionality across multiple resolvers and protocols.

**Test Classes:**
- `TestBasicFunctionality` - Basic UDP queries and response validation
- `TestProtocols` - UDP, TCP, TLS, DoH, HTTP3 protocol support
- `TestRecordTypes` - A, AAAA, MX, TXT record queries
- `TestEDNSFeatures` - NSID, ECS, DNS Cookies, DNSSEC
- `TestHostnameConsistency` - IP vs hostname equivalence
- `TestErrorHandling` - Invalid inputs and error conditions
- `TestRegressionBugs` - Specific bug fixes validation
- `TestPerformance` - Response time validation

**Examples:**
```bash
# Run all dnsping tests
pytest tests/test_dnsping_pytest.py

# Run specific test class
pytest tests/test_dnsping_pytest.py::TestProtocols

# Test specific resolver
pytest tests/test_dnsping_pytest.py -k "google"

# Test specific protocol
pytest tests/test_dnsping_pytest.py -k "doh"
```

### dnstraceroute Tests (`test_dnstraceroute_pytest.py`)

Tests DNS traceroute functionality with IPv4/IPv6 support.

**Test Classes:**
- `TestBasicFunctionality` - Basic IPv4 and IPv6 traceroute
- `TestAddressFamilyHandling` - IPv4/IPv6 auto-detection and flags
- `TestCLIOptions` - Command-line options (-n, -c, -q, etc.)
- `TestSourceIPValidation` - Source IP address family validation
- `TestErrorHandling` - Invalid inputs and error conditions
- `TestRegressionBugs` - IPv6 support (issue #45) and other fixes

**Examples:**
```bash
# Run all dnstraceroute tests
pytest tests/test_dnstraceroute_pytest.py

# Test IPv6 support
pytest tests/test_dnstraceroute_pytest.py -k "ipv6"

# Test address family handling
pytest tests/test_dnstraceroute_pytest.py::TestAddressFamilyHandling
```

## Common Usage Patterns

### Run Tests by Pattern

```bash
# All tests containing "ipv6"
pytest tests/ -k "ipv6"

# All tests for Google resolver
pytest tests/ -k "google"

# All basic functionality tests
pytest tests/ -k "basic"

# Exclude slow tests
pytest tests/ -k "not slow"
```

### Output Control

```bash
# Verbose output
pytest tests/ -v

# Quiet mode (show only dots)
pytest tests/ -q

# Show test durations
pytest tests/ --durations=10

# Short traceback
pytest tests/ --tb=short

# No traceback
pytest tests/ --tb=no
```

### Test Execution Control

```bash
# Stop on first failure
pytest tests/ -x

# Run specific number of tests
pytest tests/ --maxfail=5

# Run tests in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest tests/ -n auto
```

### Test Discovery

```bash
# List all tests without running
pytest --collect-only tests/

# Show test names
pytest --collect-only tests/ -q
```

## Test Reports

### HTML Report

```bash
pip install pytest-html
pytest tests/ --html=report.html --self-contained-html
```

### JSON Report

```bash
pip install pytest-json-report
pytest tests/ --json-report --json-report-file=report.json
```

### JUnit XML (for CI/CD)

```bash
pytest tests/ --junitxml=test-results.xml
```

## Code Coverage

```bash
pip install pytest-cov

# Generate coverage report
pytest tests/ --cov=. --cov-report=html

# View coverage in browser
open htmlcov/index.html
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        pip install -r tests/test-requirements.txt
    - name: Run tests
      run: pytest tests/ -v --junitxml=test-results.xml
    - name: Upload results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: test-results
        path: test-results.xml
```

## Test Configuration

Test configuration is in `tests/pytest.ini`:
- Test discovery patterns
- Default markers
- Output formatting
- Timeout settings

## Troubleshooting

### Network Issues

If tests fail due to network connectivity:
```bash
# Test with specific resolver only
pytest tests/test_dnsping_pytest.py -k "cloudflare"

# Increase timeout (via pytest-timeout)
pip install pytest-timeout
pytest tests/ --timeout=60
```

### Permission Issues

dnstraceroute tests may require elevated privileges for ICMP:
```bash
# Some tests might fail without root - this is expected
pytest tests/test_dnstraceroute_pytest.py -v
```

### Slow Execution

```bash
# Run in parallel
pip install pytest-xdist
pytest tests/ -n auto

# Run subset of tests
pytest tests/ -k "basic"
```

## Writing New Tests

When adding new tests:

1. Follow pytest naming convention: `test_*.py` with `test_*()` functions
2. Use parametrization for testing multiple inputs
3. Add descriptive docstrings
4. Group related tests in classes
5. Use fixtures for common setup
6. Mark network-dependent tests with `@pytest.mark.network`

Example:
```python
@pytest.mark.parametrize("resolver,ip", [
    ('google', '8.8.8.8'),
    ('cloudflare', '1.1.1.1'),
])
def test_basic_query(self, runner, resolver, ip):
    """Test basic DNS query"""
    result = runner.run(['-s', ip, 'example.com'])
    assert result.success
```

## Dependencies

See `test-requirements.txt` for full list of dependencies:
- pytest - Testing framework
- pytest-timeout - Test timeout handling
- pytest-xdist - Parallel test execution (optional)
- pytest-html - HTML report generation (optional)
- pytest-cov - Code coverage (optional)

## Test Markers

- `@pytest.mark.network` - Requires network connectivity
- Custom markers can be defined in `pytest.ini`

## Best Practices

1. **Run regression tests first**: Catch known bugs early
2. **Use filtering during development**: `pytest -k "specific_feature"`
3. **Check critical paths**: Run protocol and hostname tests before releases
4. **Monitor performance**: Use `--durations=10` to identify slow tests
5. **Keep tests fast**: Mock external dependencies when possible
6. **Update tests with bugs**: Add regression test for each bug fix

## Continuous Improvement

- Add tests for new features
- Maintain test coverage above 80%
- Update tests when behavior changes
- Remove obsolete tests
- Keep documentation current
