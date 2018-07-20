import re
from urllib.parse import urlencode

from .errors import CoursesError, LoginError, alertable


class ViewState(dict):

    form = {}
    pattern = re.compile(r'<input type="hidden" name="(?P<key>__[A-Z]+)"'
                         r' id="(?P=key)" value="(?P<value>.*?)" />')
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64;'
                       ' rv:62.0) Gecko/20100101 Firefox/62.0')
    }

    def __init__(self, session, response):
        dict.__init__(self)

        self.session = session
        self.response = response

        self['__EVENTTARGET'] = ''
        self['__EVENTARGUMENT'] = ''
        self['__LASTFOCUS'] = ''
        self['__VIEWSTATE'] = ''
        self['__VIEWSTATEGENERATOR'] = ''
        self['__EVENTVALIDATION'] = ''

        for mo in self.pattern.finditer(response.text):
            self[mo.group('key')] = mo.group('value')

        if self.form:
            self.update(self.form)

    @property
    def urldata(self) -> str:
        return urlencode(self, encoding=self.response.encoding)

    def submit(self, action=None):
        action = action or self.response.url
        response = self.session.post(
            action,
            data=self.urldata,
            headers=self.headers
        )
        return response

    def postback(self, target, action=None):
        old_target = self['__EVENTTARGET']
        self['__EVENTTARGET'] = target
        response = self.submit(action)
        self['__EVENTTARGET'] = old_target
        return response

    def copy(self):
        new_vs = type(self)(self.session, self.response)
        new_vs.update(dict.copy(self))
        return new_vs

    def __repr__(self):
        return '{}(session={}, response={}, {})'.format(
            type(self).__name__,
            repr(self.session),
            repr(self.response),
            dict.__repr__(self)[:64])


class LoginVS(ViewState):

    form = {
        'txtYHBS': '',
        'txtYHMM': '',
        'txtFJM': '',
        'btnLogin': '登    录'
    }

    def fill(self, studentid, password, validcode):
        self['txtYHBS'] = studentid
        self['txtYHMM'] = password
        self['txtFJM'] = validcode

    @alertable(LoginError)
    def submit(self):
        return ViewState.submit(self)


class HitVS(ViewState):

    form = {
        'dlstSsfw': '',
        'dlstKclb': '',
        'txtXf': '',
        'txtKcmc': '',
        'txtNj': '',
        'txtKcbh': '',
        'txtSkDz': '',
        'txtPkbh': '',
        'txtBzxx': '',
        'txtZjjs': '',
        'btnSearch': '查询'
    }

    def fill(self, class_id, summer=False):
        self['dlstSsfw'] = '可选全部课程' if not summer else '暑期班选课'
        self['txtPkbh'] = class_id

    @alertable(CoursesError)
    def submit(self):
        return ViewState.submit(self)


class XKCenterVS(ViewState):

    selections = {
        HitVS: ('btnKkLb', '开课列表'),
        #'btnWdXk': ('btnWdXk', '我的选课'),
        #'btnExport': ('btnExport', '导出课程表'),
        #'btnExport0': ('btnExport0', '导出考试安排表')
    }

    def get(self, target):
        assert target in self.selections

        key = self.selections[target][0]
        value = self.selections[target][1]
        self[key] = value

        response = self.submit()

        del self[key]
        return target(self.session, response)


class SearchVS(ViewState):

    form = {
        'chkWxk': '',
        'lbtnSearch': '查询'
    }

    def fill(self, term_prefix=None, only_electable=False):
        self['chkWxk'] = 'on' if not only_electable else ''
        if term_prefix:
            self['txtPkbh'] = str(term_prefix)

    def submit(self):
        init = ViewState.submit(self)
        rp = re.compile(r"共\d+页(\d+)行")
        count = rp.search(init.text).group(1)
        all_result_vs = ViewState(self.session, init)
        all_result_vs['txtRows'] = count
        return all_result_vs.submit()
