import itertools
import logging
import os
import threading
import time
from getpass import getpass
from logging import critical, debug, error, info, warning
from logging.handlers import TimedRotatingFileHandler

import colorlog

from .config import config

__all__ = [
    'critical',
    'debug',
    'error',
    'info',
    'warning',
    'success',
    'failure',
    'init',
    'RunningBar'
]

SUCCESS = logging.INFO + 5
FAILURE = logging.WARNING + 5

# 2 handlers: console, file
console = logging.StreamHandler()

log_file_path = os.path.join(
    config['jnujwxt']['basedir'], 'doc', 'log', 'jnujwxt.log')
file = TimedRotatingFileHandler(log_file_path, encoding='utf-8')
file.suffix += '.log'

# 3 formatters: color, no-color, verbose
color = colorlog.ColoredFormatter(
    '[%(log_color)s%(levelname)s%(reset)s] %(message)s')
color.log_colors = {
    'DEBUG': 'bold_red',
    'INFO': 'bold_blue',
    'SUCCESS': 'bold_green',
    'WARNING': 'bold_yellow',
    'FAILURE': 'bold_red',
    'ERROR': 'bg_red',
    'CRITICAL': 'bg_red'
}

no_color = logging.Formatter('[%(levelname)s] %(message)s')

verbose = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(module)s:%(lineno)s/%(process)d/%(thread)d : %(message)s')


def init(is_no_color=False):
    logging.addLevelName(SUCCESS, 'SUCCESS')
    logging.addLevelName(FAILURE, 'FAILURE')
    root_logger = logging.root
    root_logger.setLevel(logging.NOTSET)

    console.setLevel(logging.INFO)
    if is_no_color:
        console.setFormatter(no_color)
        RunningBar.move = False
    else:
        console.setFormatter(color)
    root_logger.addHandler(console)

    file.setLevel(logging.DEBUG)
    file.setFormatter(verbose)
    root_logger.addHandler(file)


def success(msg, *args, **kwargs):
    logging.log(SUCCESS, msg, *args, **kwargs)


def failure(msg, *args, **kwargs):
    logging.log(FAILURE, msg, *args, **kwargs)


class RunningBar(threading.Thread):
    move = True

    def __init__(self, msg):
        threading.Thread.__init__(self)
        self._stop_event = threading.Event()
        self._stop_event.clear()
        self.msg = msg
        s = colorlog.escape_codes['bold_blue']
        e = colorlog.escape_codes['reset']
        style = '\\|/-'
        self.anime = itertools.cycle(style)
        self.name = s + 'RUNNING' + e
        self.elapsed = 0

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, typ, value, trace):
        if typ == None:
            self.stop()
        else:
            self._stop_event.set()
            self.join()
            logging.warning(f'{self.msg} (stoped in {self.elapsed}s)')

    def run(self):
        start = time.perf_counter()
        if self.move:
            while True:
                frame = next(self.anime)
                logging._acquireLock()
                print(f'[{self.name}] {self.msg} {frame}', end='\r')
                logging._releaseLock()
                if self._stop_event.wait(0.1):
                    break
        else:
            self._stop_event.wait()
        end = time.perf_counter()
        self.elapsed = round(end - start, 2)

    def stop(self):
        self._stop_event.set()
        self.join()
        logging.info(f'{self.msg} (done in {self.elapsed}s)')
