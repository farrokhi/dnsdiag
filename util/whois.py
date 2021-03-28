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
    except Exception as e:
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
