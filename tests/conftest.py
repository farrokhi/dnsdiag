import sys
from pathlib import Path

# Add parent directory to path so tests can import dnsdiag module
tests_dir = Path(__file__).parent
project_root = tests_dir.parent
sys.path.insert(0, str(project_root))
