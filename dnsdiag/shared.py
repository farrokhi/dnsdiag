#!/usr/bin/env python3
#
# Copyright (c) 2016-2026, Babak Farrokhi
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

import random
import string
import sys

__version__ = '2.9.2'


def random_string(min_length: int = 5, max_length: int = 10) -> str:
    char_set = string.ascii_letters + string.digits
    length = random.randint(min_length, max_length)
    return ''.join(random.choices(char_set, k=length))


def die(s: str, exit_code: int = 1) -> None:
    err(s)
    sys.exit(exit_code)


def err(s: str) -> None:
    print(s, file=sys.stderr, flush=True)


def unsupported_feature(feature: str = "") -> None:
    if feature:
        die(f"{feature} not available", exit_code=127)
    else:
        die("feature not available", exit_code=127)


def valid_hostname(hostname: str, allow_underscore: bool = False) -> bool:
    """
    Validate a hostname or FQDN.

    For strict RFC 1123/952 validation (hostnames), underscores are rejected.
    For DNS queries (allow_underscore=True), underscores are allowed to support
    special DNS records like _dmarc, _acme-challenge, etc.

    Args:
        hostname: The hostname or FQDN to validate
        allow_underscore: If True, allow underscores in labels (for DNS queries)

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

        # Label must start with alphanumeric or underscore (if allowed)
        if allow_underscore:
            if not (label[0].isalnum() or label[0] == '_'):
                return False
        else:
            if not label[0].isalnum():
                return False

        # Label must end with alphanumeric
        if not label[-1].isalnum():
            return False

        # Label can contain alphanumeric, hyphens, and optionally underscores
        allowed_chars = {'-', '_'} if allow_underscore else {'-'}
        for char in label:
            if not (char.isalnum() or char in allowed_chars):
                return False

    return True


class Colors:
    N = '\033[m'  # native
    R = '\033[31m'  # red
    G = '\033[32m'  # green
    O = '\033[33m'  # orange
    B = '\033[34m'  # blue

    def __init__(self, mode: bool) -> None:
        if not mode:
            self.N = ''
            self.R = ''
            self.G = ''
            self.O = ''
            self.B = ''
