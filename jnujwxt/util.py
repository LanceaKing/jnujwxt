import logging
import re
from concurrent.futures import ThreadPoolExecutor

import requests


def network_test(net_list, nt=5, log=False, **kwargs):

    timeout = kwargs.pop('timeout', 3)

    def single_test(net):
        try:
            response = requests.get(net, timeout=timeout, **kwargs)
            elapsed = response.elapsed.total_seconds()
            status = response.status_code
        except requests.Timeout:
            if log:
                logging.info(f'{net} => TIMEOUT')
        except Exception as E:
            if log:
                logging.error(f'{net} => {E}')
        else:
            if log:
                logging.info(f'{net} => [{status}] {elapsed}s')
            if response.ok:
                return (net, elapsed)

    net_set = set(net_list)
    with ThreadPoolExecutor(nt) as thread_pool:
        test_map = thread_pool.map(single_test, net_set)
    test_result = set(test_map)
    if None in test_result:
        test_result.remove(None)

    if len(test_result):
        return min(test_result, key=lambda x: x[1])
    else:
        return None


def find_alert_msg(html):
    pattern = re.compile(
        r"<script.*?>.*?alert\('(.*?)'\).*?</script>", re.I | re.S)
    result = re.search(pattern, html)
    return result and result.group(1)
