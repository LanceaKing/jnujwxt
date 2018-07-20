import re

from .courses import CourseTaker
from .errors import CoursesError, alertable
from .viewstate import HitVS, ViewState, XKCenterVS


class XKCenter(object):

    summer_spec = '暑期班选课'
    closed_spec = '选课系统已经关闭'

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
                readme_vs = ViewState(self.session, readme)
                readme_vs['btnYes'] = '是(Yes)'
                xkcenter = readme_vs.submit()
            else:
                xkcenter = readme
        else:
            xkcenter = self.session.get(self.url)

        self.is_readme = True
        return xkcenter

    def hit(self, schedule_id):
        if self.is_closed:
            raise CoursesError(self.closed_spec)
        hit_vs = self.viewstate.get(HitVS)
        hit_vs.fill(schedule_id, self.is_summer)
        hit_one = hit_vs.submit()

        rp = re.compile(r"共\d+页(\d+)行")
        count = rp.search(hit_one.text).group(1)
        assert count == '1'

        take_vs = ViewState(self.session, hit_one)
        take_vs.submit = alertable(CoursesError)(take_vs.submit)
        magic = 'dgrdPk$ctl02$ctl00'
        take = take_vs.postback(magic)
        return CourseTaker(self.session, take)
