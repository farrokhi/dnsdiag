from setuptools import setup, find_packages
setup(
    name = "dnsdiag",
    version = "1.3.4",
	packages = find_packages(),
    scripts = ['dnsping.py', 'dnstraceroute.py', 'dnseval.py'],
    classifiers=[
        "Topic :: System :: Networking",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        'Programming Language :: Python :: 3.4',
        "Development Status :: 5 - Production/Stable",
        "Operating System :: OS Independent",
    ],

    author = "Babak Farrokhi",
    author_email = "babak@farrokhi.net",
    description = "DNS Diagnostics and measurement tools (ping, traceroute)",
    long_description = """
DNSDiag provides a handful of tools to measure and diagnose your DNS
performance and integrity. Using dnsping, dnstraceroute and dnseval tools
you can measure your DNS response quality from delay and loss perspective
as well as tracing the path your DNS query takes to get to DNS server.
""",
    license = "BSD",
    keywords = "dns traceroute ping",
    url = "https://dnsdiag.org/",
)
