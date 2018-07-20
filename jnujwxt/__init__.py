from io import BytesIO

import sqlalchemy as sa
from PIL import Image
from requests import Session

from .config import Config
from .courses import Course, parser
from .viewstate import LoginVS, SearchVS, ViewState
from .xkcenter import XKCenter

db_engine = sa.create_engine(Config.DATABASE_URI)
DBSession = sa.orm.sessionmaker(bind=db_engine)


class Jwxt(Session):

    urls = Config.JWXT_URLS

    @property
    def netloc(self):
        return self.urls['root']

    def __init__(self):
        Session.__init__(self)
        self.studentid = ''
        self.is_login = False
        self.db_session = DBSession()

    def __repr__(self):
        return '<Jwxt netloc={}, id={}, is_login={})>'.format(
            repr(self.netloc),
            repr(self.studentid),
            repr(self.is_login))

    def validcode_img(self) -> Image.Image:
        validcode = self.get(self.urls['validcode'])
        assert validcode.ok
        return Image.open(BytesIO(validcode.content))

    def login(self, studentid, password, validation):
        assert not self.is_login
        login_url = self.urls['login']
        login = self.get(login_url)
        login_vs = LoginVS(self, login)
        login_vs.fill(studentid, password, validation)
        result = login_vs.submit()
        self.studentid = studentid
        self.is_login = True
        return result

    def logout(self):
        assert self.is_login
        logout_url = self.urls['logout']
        logout = self.get(logout_url)
        logout_vs = ViewState(self, logout)
        logout_vs['header$btnTC'] = '退出'
        result = logout_vs.submit()
        assert "window.open('Login.aspx','_parent')" in result.text
        self.studentid = ''
        self.is_login = False
        return result

    def xkcenter(self):
        return XKCenter(self)

    def update_database(self, only_electable=False):
        assert self.is_login
        search_url = self.urls['search']
        init = self.get(search_url)
        search_vs = SearchVS(self, init)
        search_vs.fill(only_electable)
        search_result = search_vs.submit()

        count = 0
        for kwargs in parser(search_result.text):
            new_course = Course(**kwargs)
            self.db_session.merge(new_course)
            count += 1

        self.db_session.commit()
        return count
