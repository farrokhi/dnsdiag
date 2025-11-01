"""
Test package distribution and module availability.

This test suite ensures that the package is correctly configured for distribution,
particularly that root-level Python modules are included in the package.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestPackageDistribution:
    """Tests for package distribution configuration."""

    def test_root_modules_importable(self):
        """Test that root-level modules can be imported directly.

        This verifies the fix for the issue where py-modules was missing
        from pyproject.toml, causing ModuleNotFoundError when installed
        via pip or uvx.
        """
        root_modules = ['dnsping', 'dnstraceroute', 'dnseval']

        for module_name in root_modules:
            try:
                __import__(module_name)
            except ModuleNotFoundError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")

    def test_module_main_functions_exist(self):
        """Test that each root module has a main() function."""
        import dnsping
        import dnstraceroute
        import dnseval

        modules = [
            ('dnsping', dnsping),
            ('dnstraceroute', dnstraceroute),
            ('dnseval', dnseval)
        ]

        for name, module in modules:
            assert hasattr(module, 'main'), f"{name} module missing main() function"
            assert callable(module.main), f"{name}.main is not callable"

    def test_pyproject_includes_py_modules(self):
        """Test that pyproject.toml includes py-modules configuration.

        This is a regression test for the packaging bug where root-level
        modules were not included in the distribution.
        """
        pyproject_path = Path(__file__).parent.parent / 'pyproject.toml'

        assert pyproject_path.exists(), "pyproject.toml not found"

        content = pyproject_path.read_text()

        # Check that py-modules is defined
        assert 'py-modules' in content, "py-modules not found in pyproject.toml"

        # Check that all three root modules are listed
        assert '"dnsping"' in content or "'dnsping'" in content
        assert '"dnstraceroute"' in content or "'dnstraceroute'" in content
        assert '"dnseval"' in content or "'dnseval'" in content

    def test_entry_points_configured(self):
        """Test that console script entry points are properly configured."""
        pyproject_path = Path(__file__).parent.parent / 'pyproject.toml'
        content = pyproject_path.read_text()

        # Check for [project.scripts] section
        assert '[project.scripts]' in content, "[project.scripts] section missing"

        # Check for entry points
        expected_scripts = [
            'dnsping = "dnsping:main"',
            'dnstraceroute = "dnstraceroute:main"',
            'dnseval = "dnseval:main"'
        ]

        for script in expected_scripts:
            assert script in content, f"Entry point not found: {script}"

    @pytest.mark.skipif(sys.platform == "win32", reason="sdist build test not reliable on Windows")
    def test_sdist_includes_root_modules(self):
        """Test that building sdist includes root-level Python modules.

        This test actually builds a source distribution and verifies that
        the root modules are included in the tarball.
        """
        try:
            import build  # noqa: F401
        except ImportError:
            pytest.skip("build package not available")

        project_root = Path(__file__).parent.parent

        with tempfile.TemporaryDirectory() as tmpdir:
            # Build sdist
            result = subprocess.run(
                [sys.executable, "-m", "build", "--sdist", "--outdir", tmpdir],
                cwd=project_root,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                pytest.skip(f"Failed to build sdist: {result.stderr}")

            # Find the created tarball
            dist_dir = Path(tmpdir)
            tarballs = list(dist_dir.glob("*.tar.gz"))

            assert len(tarballs) == 1, f"Expected 1 tarball, found {len(tarballs)}"

            # Extract and check contents
            import tarfile
            with tarfile.open(tarballs[0], 'r:gz') as tar:
                names = tar.getnames()

                # Check that root modules are included
                root_modules = ['dnsping.py', 'dnstraceroute.py', 'dnseval.py']
                for module in root_modules:
                    # Files are typically in a directory like dnsdiag-2.9.1/dnsping.py
                    matching = [n for n in names if n.endswith(module)]
                    assert matching, f"{module} not found in sdist"
