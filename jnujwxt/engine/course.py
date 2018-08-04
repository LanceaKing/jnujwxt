import re
from datetime import datetime
from html import unescape

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

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
        return 'Course(name={}, credit={}, schedule_id={}, ...)'.format(
            repr(self.name),
            repr(self.credit),
            repr(self.schedule_id)
        )


def parser(html):
    glb_ptn = re.compile(r'''
        ItemStyle">\s*<td>
        (?P<course_id>[^<]*)</td><td>
        (?P<name>[^<]*)</td><td>
        (?P<capacity>[^<]*)</td><td>
        (?P<elected>[^<]*)</td><td>
        (?P<teacher>[^<]*)</td><td>
        (?P<major>[^<]*)</td><td>
        (?P<credit>[^<]*)</td><td>
        (\s*<span[^>]*>)?(\s*<font[^>]*>)? # group 8 & group 9
        (?P<location>[^<]*)(?(9)</font>\s*)(?(8)</span>\s*)</td><td>
        (\s*<span[^>]*>)?(\s*<font[^>]*>)? # group 11 & group 12
        (?P<schedule>[^<]*)(?(12)</font>\s*)(?(11)</span>\s*)</td><td>
        (?P<schedule_id>[^<]*)</td><td>
        (?P<enroll>[^<]*)</td><td>
        (?P<exam_date>[^<]*)</td><td>
        (?P<comment>[^<]*)</td><td>
        (?P<exam_typ>[^<]*)
    ''', re.X | re.S)
    loc_ptn = re.compile(r'(?<=[①②③④⑤⑥⑦⑧⑨⑩])[^,]+', re.S)
    sch_ptn = re.compile(r'(?<=[①②③④⑤⑥⑦⑧⑨⑩])[^①②③④⑤⑥⑦⑧⑨⑩]+', re.S)
    date_ptn = re.compile(
        r'(\d{2,4})\D(\d{1,2})\D(\d{1,2})\s+(\d{1,2}):(\d{1,2})')
    if 'ItemStyle">' in html:
        for mo in glb_ptn.finditer(html):
            kwargs = mo.groupdict()

            for key, value in kwargs.items():
                kwargs[key] = unescape(value).strip()

            if kwargs['elected'] == '':
                kwargs['elected'] = None

            kwargs['location'] = '$'.join(loc_ptn.findall(kwargs['location']))
            kwargs['schedule'] = '$'.join(sch_ptn.findall(kwargs['schedule']))

            if kwargs['exam_date']:
                date = date_ptn.match(kwargs['exam_date']).groups()
                dto = datetime(*(int(x) for x in date))
                kwargs['exam_date'] = dto
            else:
                kwargs['exam_date'] = None

            yield Course(**kwargs)
