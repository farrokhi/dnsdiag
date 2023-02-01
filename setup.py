from setuptools import setup, find_packages
from util.shared import __version__

setup(
    name="dnsdiag",
    version=__version__,
    packages=find_packages(),
    scripts=["dnseval.py", "dnsping.py", "dnstraceroute.py"],
    install_requires=['dnspython>=2.3.0', 'cymruwhois>=1.6', 'requests>=2.28.2', 'requests-toolbelt>=0.9.1'],

    classifiers=[
        "Topic :: System :: Networking",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Internet :: Name Service (DNS)",
        "Development Status :: 5 - Production/Stable",
        "Operating System :: OS Independent",
    ],

    author="Babak Farrokhi",
    author_email="babak@farrokhi.net",
    description="DNS Measurement, Troubleshooting and Security Auditing Toolset (ping, traceroute)",
    long_description="""
DNSDiag provides a handful of tools to measure and diagnose your DNS
performance and integrity. Using dnsping, dnstraceroute and dnseval tools
you can measure your DNS response quality from delay and loss perspective
as well as tracing the path your DNS query takes to get to DNS server.
""",
    license="BSD",
    keywords="dns traceroute ping performance",
    url="https://dnsdiag.org/",
    entry_points={
        'console_scripts': [
            'dnsping = dnsping:main',
            'dnstraceroute = dnstraceroute:main',
            'dnseval = dnseval:main',
        ]
    }
)
