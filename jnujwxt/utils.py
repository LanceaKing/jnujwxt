import re
from threading import Thread

import requests


class NetTestThread(Thread):
    def __init__(self, net, timeout=1):
        Thread.__init__(self)
        self.net = net
        self.timeout = timeout

    def run(self):
        try:
            response = requests.get(self.net,
                                    timeout=self.timeout)
            self.elapsed = response.elapsed.microseconds
        except requests.ConnectTimeout:
            self.elapsed = 'timeout'


def net_test(net_list, nt=5):
    test_result = {}
    thread_pool = []
    splited = (net_list[i:i+nt] for i in range(0, len(net_list), nt))

    for sl in splited:
        for net in sl:
            t = NetTestThread(net)
            t.start()
            thread_pool.append(t)
        for t in thread_pool:
            t.join()
            if t.elapsed != 'timeout':
                test_result[t.net] = t.elapsed
        thread_pool.clear()

    if len(test_result):
        best_net = min(test_result, key=test_result.get)
        min_elapsed = test_result[best_net]
        return (best_net, min_elapsed)
    else:
        return None

def find_alert_msg(html):
    pattern = re.compile(r"alert\('(.*?)'\)")
    result = re.search(pattern, html)
    return result and result.group(1)
