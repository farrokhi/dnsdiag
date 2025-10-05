# Type Hints Guide for dnsdiag

## Quick Start

### 1. Install mypy
```bash
pip install mypy
```

### 2. Run mypy
```bash
# Check specific files
mypy dnsping.py dnseval.py dnstraceroute.py

# Check entire project
mypy .

# Check with HTML report
mypy . --html-report mypy-report
```

### 3. Configuration
The `mypy.ini` file controls mypy behavior. Start lenient and gradually enable stricter checks.

## Incremental Typing Strategy

### Phase 1: Fix Syntax Errors (Current Priority)
Fix existing type annotation syntax errors:

```python
# BAD - Old tuple syntax
def asn_lookup(ip, whois_cache) -> (str, dict):

# GOOD - Use Tuple from typing
from typing import Tuple, Optional, Any

def asn_lookup(ip: str, whois_cache: dict) -> Tuple[Optional[Any], dict]:
```

Add missing annotations:
```python
# BAD - No annotation
whois_cache = {}

# GOOD - Annotated
whois_cache: dict[str, Any] = {}
```

### Phase 2: Add Function Signatures
Start with public API functions:

```python
# Before
def ping(qname, server, dst_port, rdtype, timeout, count, proto, src_ip,
         use_edns=False, force_miss=False, want_dnssec=False, socket_ttl=None):

# After
def ping(qname: str, server: str, dst_port: int, rdtype: str,
         timeout: float, count: int, proto: int, src_ip: Optional[str],
         use_edns: bool = False, force_miss: bool = False,
         want_dnssec: bool = False, socket_ttl: Optional[int] = None) -> PingResponse:
```

### Phase 3: Add Variable Annotations
For module-level and class variables:

```python
# Before
response_times = []
shutdown = False

# After
response_times: list[float] = []
shutdown: bool = False
```

### Phase 4: Enable Strict Checks
Gradually uncomment options in `mypy.ini`:

1. `check_untyped_defs = True` - Type-check function bodies
2. `disallow_untyped_defs = True` - Require all functions have types
3. `warn_return_any = True` - Warn when returning Any
4. `strict = True` - Enable all strict checks

## Common Patterns for dnsdiag

### DNS Protocol Constants
```python
# Type alias for clarity
ProtoType = int

PROTO_UDP: ProtoType = 0
PROTO_TCP: ProtoType = 1
```

### Optional Parameters
```python
from typing import Optional

def resolve_hostname(hostname: str, af: Optional[int] = None) -> str:
    if af is None:
        af = socket.AF_INET
    # ...
```

### Lists and Dicts
```python
# Python 3.9+
servers: list[str] = ['8.8.8.8', '1.1.1.1']
cache: dict[str, tuple[Any, float]] = {}

# Or using typing module (works in 3.7+)
from typing import List, Dict, Tuple, Any

servers: List[str] = ['8.8.8.8', '1.1.1.1']
cache: Dict[str, Tuple[Any, float]] = {}
```

### Return Types for Complex Functions
```python
from typing import Union, Optional
from dataclasses import dataclass

@dataclass
class DNSResponse:
    rcode: int
    answer: Optional[list]
    flags: int

def query_dns(server: str) -> Union[DNSResponse, None]:
    # ...
```

### Type Aliases
```python
from typing import TypeAlias

# For readability
IPAddress: TypeAlias = str
Hostname: TypeAlias = str
WhoisCache: TypeAlias = dict[str, tuple[Any, float]]

def lookup(ip: IPAddress, cache: WhoisCache) -> tuple[Optional[Any], WhoisCache]:
    # ...
```

## Handling Third-Party Libraries

For libraries without type stubs (cymruwhois, dnspython):

```python
# Option 1: Use Any for their types
from typing import Any

def process_whois(result: Any) -> str:
    return result.owner

# Option 2: Create stub files (advanced)
# Create cymruwhois.pyi with type stubs

# Option 3: Ignore in mypy.ini
[mypy-cymruwhois]
ignore_missing_imports = True
```

## Running mypy in CI/CD

### GitHub Actions Example
```yaml
- name: Type check with mypy
  run: |
    pip install mypy
    mypy dnsping.py dnseval.py dnstraceroute.py
```

### Pre-commit Hook
```bash
# .git/hooks/pre-commit
#!/bin/bash
mypy --quiet dnsping.py dnseval.py dnstraceroute.py || exit 1
```

## Best Practices

1. **Start small**: Add types to new code first
2. **Be pragmatic**: Use `Any` when third-party types are unclear
3. **Document intent**: Type hints serve as inline documentation
4. **Run regularly**: Include mypy in CI/CD
5. **Avoid over-typing**: Don't type internal implementation details unless helpful
6. **Use # type: ignore sparingly**: Only when mypy is wrong

## Common mypy Errors and Fixes

### Error: "Need type annotation for X"
```python
# Before
cache = {}

# After
from typing import Any
cache: dict[str, Any] = {}
```

### Error: "Syntax error in type annotation"
```python
# Before
def func() -> (str, int):

# After
from typing import Tuple
def func() -> Tuple[str, int]:
```

### Error: "Incompatible return value type"
```python
# Before
def get_port() -> int:
    return None  # Error!

# After
from typing import Optional
def get_port() -> Optional[int]:
    return None  # OK
```

### Error: "Argument has incompatible type"
```python
# Fix by adjusting type annotations to match actual usage
def process(data: str) -> None:  # Says str
    pass

process(123)  # Error: int is not str

# Fix: Either change annotation or convert
def process(data: str | int) -> None:  # Accept both
    pass
```

## Tools

- **mypy**: Static type checker
- **pyright**: Alternative type checker (faster)
- **pyre**: Facebook's type checker
- **VSCode**: Built-in type checking with Pylance
- **PyCharm**: Built-in type checking

## Resources

- [mypy documentation](https://mypy.readthedocs.io/)
- [Python typing module](https://docs.python.org/3/library/typing.html)
- [PEP 484](https://www.python.org/dev/peps/pep-0484/) - Type Hints
- [Real Python typing guide](https://realpython.com/python-type-checking/)
