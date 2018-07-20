import re

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

from .errors import CoursesError, alertable
from .viewstate import ViewState
from datetime import datetime

Base = declarative_base()


class Course(Base):

    __tablename__ = 'course'

    course_id = sa.Column(sa.String(8))
    name = sa.Column(sa.String(128), index=True)
    capacity = sa.Column(sa.SmallInteger)
    elected = sa.Column(sa.SmallInteger)
    teacher = sa.Column(sa.String(64))
    major = sa.Column(sa.String(32))
    credit = sa.Column(sa.Float)
    location = sa.Column(sa.String(256))
    schedule = sa.Column(sa.String(256))
    schedule_id = sa.Column(sa.String(9), primary_key=True)
    enroll = sa.Column(sa.Enum('', '内招生', '外招生'))
    exam_date = sa.Column(sa.DateTime)
    comment = sa.Column(sa.String(256))
    exam_typ = sa.Column(sa.String(8))

    def __repr__(self):
        return 'Course(name={}, schedule_id={}, credit={})'.format(
            repr(self.name),
            repr(self.schedule_id),
            repr(self.credit)
        )


class CourseTaker(ViewState):

    pattern = re.compile(r'<input.*?name="(?P<key>(?!btnReturnX).*?)".*?value="(?P<value>.*?)".*?/>')

    @alertable(CoursesError)
    def take(self):
        return self.submit()


def parser(html):
    regex = (r'<tr class="DG(?:Alternating)?ItemStyle">\s*'
             r'<td>(?P<course_id>\d+)</td>'
             r'<td>(?P<name>.+?)\s*</td>'
             r'<td>(?P<capacity>\d+)</td>'
             r'<td>(?P<elected>\d*)(?:&nbsp;)?</td>'
             r'<td>(?P<teacher>.*?)</td>'
             r'<td>(?P<major>.*?)(?:&nbsp;)?</td>'
             r'<td>(?P<credit>\d+(?:\.\d+)?)</td>'
             r'<td>\s*<span.*?>(?P<location>.*?)</span>\s*</td>'
             r'<td>\s*<span.*?>(?P<schedule>.*?)</span>\s*</td>'
             r'<td>(?P<schedule_id>[S\d]+)</td>'
             r'<td>(?P<enroll>.*?)\s*</td>'
             r'<td>(?P<exam_date>.*?)(?:&nbsp;)?</td>'
             r'<td>(?P<comment>.*?)(?:&nbsp;)?</td>'
             r'<td>(?P<exam_typ>.*?)</td>'
             r'\s*</tr>')
    pattern = re.compile(regex)
    loc_rp = re.compile(r'(?<=[①②③④⑤⑥⑦⑧⑨⑩])[^,]*')
    sch_rp = re.compile(r'(?<=[①②③④⑤⑥⑦⑧⑨⑩])[^①②③④⑤⑥⑦⑧⑨⑩]*')
    date_rp = re.compile(r'(\d+)[-\.](\d+)[-\.](\d+)\s+(\d+):(\d+)')
    if 'ItemStyle">' in html:
        for mo in pattern.finditer(html):
            info = mo.groupdict()

            if info['elected'] == '':
                info['elected'] = None

            info['location'] = '|'.join(loc_rp.findall(info['location']))
            info['schedule'] = '|'.join(sch_rp.findall(info['schedule']))

            if info['exam_date']:
                date = date_rp.match(info['exam_date']).groups()
                dto = datetime(*[int(x) for x in date])
                info['exam_date'] = dto
            else:
                info['exam_date'] = None

            yield info
