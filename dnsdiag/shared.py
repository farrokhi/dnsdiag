#!/usr/bin/env python3
#
# Copyright (c) 2016-2025, Babak Farrokhi
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


__version__ = '2.8.1'


def valid_hostname(hostname):
    """
    Validate a hostname or FQDN according to RFC 1123 and RFC 952.

    Accepts:
    - Simple hostnames (e.g., 'localhost', 'server1')
    - Fully qualified domain names (e.g., 'example.com', 'www.example.com')
    - Internationalized domain names in ASCII-compatible encoding (e.g., 'xn--...')

    Returns:
        bool: True if hostname is valid, False otherwise
    """
    if not hostname or not isinstance(hostname, str):
        return False

    # Remove trailing dot if present (FQDN notation)
    if hostname.endswith('.'):
        hostname = hostname[:-1]

    # Check overall length (max 253 characters for FQDN)
    if len(hostname) > 253:
        return False

    # Empty after removing trailing dot
    if not hostname:
        return False

    # Split into labels
    labels = hostname.split('.')

    # Each label must be 1-63 characters
    for label in labels:
        if not label or len(label) > 63:
            return False

        # Label must start with alphanumeric
        if not label[0].isalnum():
            return False

        # Label must end with alphanumeric
        if not label[-1].isalnum():
            return False

        # Label can only contain alphanumeric and hyphens
        for char in label:
            if not (char.isalnum() or char == '-'):
                return False

    return True


class Colors(object):
    N = '\033[m'  # native
    R = '\033[31m'  # red
    G = '\033[32m'  # green
    O = '\033[33m'  # orange
    B = '\033[34m'  # blue

    def __init__(self, mode):
        if not mode:
            self.N = ''
            self.R = ''
            self.G = ''
            self.O = ''
            self.B = ''
