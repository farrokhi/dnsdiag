#!/usr/bin/env python3
#
# Copyright (c) 2016-2024, Babak Farrokhi
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

import pickle
import time

import cymruwhois

WHOIS_CACHE_FILE = 'whois.cache'


def asn_lookup(ip, whois_cache) -> (str, dict):
    """
    Look up an ASN given teh IP address from cache. If not in cache, lookup from a whois server and update the cache
    :param ip: IP Address (str)
    :param whois_cache: whois data cache (dict)
    :return: AS Number (str), Updated whois cache (dict)
    """
    asn = None
    try:
        currenttime = time.time()
        if ip in whois_cache:
            asn, ts = whois_cache[ip]
        else:
            ts = 0
        if (currenttime - ts) > 36000:
            c = cymruwhois.Client()
            asn = c.lookup(ip)
            whois_cache[ip] = (asn, currenttime)
    except Exception:
        pass
    return asn, whois_cache


def restore() -> dict:
    """
    Loads whois cache data from a file
    :return: whois data dict
    """
    try:
        pkl_file = open(WHOIS_CACHE_FILE, 'rb')
        try:
            whois = pickle.load(pkl_file)
            pkl_file.close()
        except Exception:
            whois = {}
    except IOError:
        whois = {}
    return whois


def save(whois_data: dict):
    """
    Saves whois cache data to a file
    :param whois_data: whois data (dict)
    :return: None
    """
    pkl_file = open(WHOIS_CACHE_FILE, 'wb')
    pickle.dump(whois_data, pkl_file)
    pkl_file.close()
