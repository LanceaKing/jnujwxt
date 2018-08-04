import logging
import multiprocessing
import re
import threading
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from enum import Enum
from queue import Queue

from ..util import find_alert_msg
from .error import CourseError, JwxtException, alertable
from .viewstate import BaseViewState, HitVS, XKCenterVS

Level = Enum('Level', ('NotSet', 'Crash', 'Full',
                       'Elected', 'Success', 'NoCredit'))


class XKCenter(object):

    summer_spec = '暑期班选课'
    closed_spec = '选课系统已经关闭'
    count_spec = re.compile(r'共\d+页(\d+)行')

    def __init__(self, session):
        assert session.is_login
        self.session = session
        self.url = session.urls['xkcenter']

        self.is_readme = False
        xkcenter = self.response()
        self.viewstate = XKCenterVS(session, xkcenter)

        self.text = xkcenter.text
        self.is_summer = self.summer_spec in self.text
        self.is_closed = self.closed_spec in self.text

    def __repr__(self):
        return '<XKCenter is_closed={}, session={}>'.format(
            repr(self.is_closed),
            repr(self.session))

    def response(self):
        if not self.is_readme:
            readme_url = self.session.urls['xkreadme']
            readme = self.session.get(readme_url)
            if not readme.is_redirect:
                readme_vs = BaseViewState(self.session, readme)
                readme_vs['btnYes'] = '是(Yes)'
                xkcenter = readme_vs.submit()
            else:
                xkcenter = readme
        else:
            xkcenter = self.session.get(self.url)

        self.is_readme = True
        return xkcenter

    def missile(self, schedule_id):
        if self.is_closed:
            raise CourseError(self.closed_spec)
        hit_vs = self.viewstate.get(HitVS)
        hit_vs.fill(schedule_id, self.is_summer)
        hit_one = hit_vs.submit()

        match = self.count_spec.search(hit_one.text)
        if not match:
            logging.debug(hit_one.text)
            raise JwxtException('Unknown error')
        elif match.group(1) != '1':
            raise CourseError(match.group(0))

        take_vs = BaseViewState(self.session, hit_one)
        take_vs.submit = alertable(CourseError)(take_vs.submit)
        magic = 'dgrdPk$ctl02$ctl00'
        take = take_vs.postback(magic)
        return Missile(self.session, take, schedule_id)

    def xkwar(self, schedule_id_list, np=None, nt=3, level=None):
        if self.is_closed:
            raise CourseError(self.closed_spec)

        level = level or Level.Crash

        def killer(missile):
            msg_queue = Queue()
            t_pool = []
            for _ in range(nt):
                t = Launcher(missile, msg_queue)
                t.start()
                t_pool.append(t)
            for status in msg_queue.get():
                if status.value > level.value:
                    break
            for t in t_pool:
                t.stop()
            return (missile.id, status)

        with ThreadPoolExecutor(nt) as thread_pool:
            missile_magazine = thread_pool.map(
                self.missile, set(schedule_id_list))

        with ProcessPoolExecutor(np) as process_pool:
            results = process_pool.map(killer, missile_magazine)
        return list(results)


class Launcher(threading.Thread):

    def __init__(self, missile, msgbox):
        threading.Thread.__init__(self)
        self.missile = missile
        self.msgbox = msgbox

        self._continue_event = threading.Event()
        self._continue_event.set()
        self._stop_event = threading.Event()
        self._stop_event.clear()

    def run(self):
        while self._continue_event.wait() and not self._stop_event.is_set():
            status = self.missile.launch()  # FIRE!
            self.msgbox.put(status)

    def pause(self):
        self._continue_event.clear()

    def resume(self):
        self._continue_event.set()

    def stop(self):
        self._stop_event.set()
        self._continue_event.set()
        self.join()


class Missile(BaseViewState):

    pattern = re.compile(r'<input.*?name="(?P<key>(?!btnReturnX).*?)"'
                         r'.*?value="(?P<value>.*?)".*?>')

    def __init__(self, session, response, schedule_id):
        BaseViewState.__init__(self, session, response)
        self.id = schedule_id

    def launch(self):
        response = self.submit()
        if response.ok:
            msg = find_alert_msg(response.text)
            if msg is None:  # HIT!
                return Level.Success
            elif '人数已满' in msg:
                return Level.Full
            elif '学分已满' in msg:
                return Level.NoCredit
            elif '重复' in msg:
                return Level.Elected
            else:
                raise CourseError(msg)
        else:
            return Level.Crash
