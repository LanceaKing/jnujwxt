import json
import logging
import time

import requests
import urllib3
from PIL import Image

from ..config import config
from ..db import DBSession
from .course import Course, parser
from .viewstate import BaseViewState, LoginVS, SearchVS
from .xkcenter import XKCenter

__all__ = ['Jwxt']


class Jwxt(requests.Session):

    urls = config['jnujwxt_url']

    @property
    def netloc(self):
        return self.urls['root']

    def __init__(self):
        requests.Session.__init__(self)
        self.student_id = ''
        self.is_login = False
        self.db_session = DBSession()
        self.verify = False
        self.headers['Host'] = config['jnujwxt']['domain']

    def __repr__(self):
        return '<Jwxt netloc={}, id={}, is_login={})>'.format(
            repr(self.netloc),
            repr(self.student_id),
            repr(self.is_login))

    def validcode_img(self):
        validcode = self.get(self.urls['validcode'], stream=True)
        return Image.open(validcode.raw)

    def login(self, studentid, password, validation):
        assert not self.is_login
        login_url = self.urls['login']
        login = self.get(login_url)
        login_vs = LoginVS(self, login)
        login_vs.fill(studentid, password, validation)
        result = login_vs.submit()
        self.student_id = studentid
        self.is_login = True
        return result

    def refresh_login_status(self):
        response = self.get(self.urls['logout'])
        self.is_login = 'header_lblXM"></span>' not in response.text

    def resume_cookie(self, path, student_id=''):
        with open(path) as fp:
            cookiedict = json.load(fp)
        cookiejar = requests.utils.cookiejar_from_dict(cookiedict)
        self.cookies = cookiejar
        self.refresh_login_status()
        if self.is_login:
            self.student_id = student_id
        else:
            self.student_id = ''
            self.cookies.clear()

    def save_cookie(self, path):
        cookiejar = self.cookies
        cookiedict = requests.utils.dict_from_cookiejar(cookiejar)
        with open(path, 'w') as fp:
            json.dump(cookiedict, fp)

    def logout(self):
        assert self.is_login
        logout_url = self.urls['logout']
        logout = self.get(logout_url)
        logout_vs = BaseViewState(self, logout)
        logout_vs['header$btnTC'] = '退出'
        result = logout_vs.submit()
        assert "window.open('Login.aspx','_parent')" in result.text
        self.student_id = ''
        self.is_login = False
        return result

    def xkcenter(self):
        return XKCenter(self)

    def update_courses(self, term_prefix=None, only_electable=False):
        logging.debug(
            f'update_courses(term_prefix={term_prefix},'
            f' only_electable={only_electable})')
        assert self.is_login
        search_url = self.urls['search']
        init = self.get(search_url)
        search_vs = SearchVS(self, init)
        search_vs.fill(term_prefix, only_electable)
        search_result = search_vs.submit()

        dl_elapsed = search_result.elapsed.total_seconds()
        logging.debug(f'download courses: {dl_elapsed}s')

        count = 0
        re_start = time.perf_counter()
        try:
            for new_course in parser(search_result.text):
                self.db_session.merge(new_course)
                count += 1
        except BaseException as be:
            self.db_session.rollback()
            raise be
        self.db_session.commit()
        re_elapsed = time.perf_counter() - re_start
        logging.debug(f'regex and generate courses: {re_elapsed}s')

        return count
