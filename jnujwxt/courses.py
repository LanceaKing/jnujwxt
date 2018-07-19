import re
from dataclasses import dataclass

from .errors import CoursesError, alertable
from .viewstate import ViewState


@dataclass
class Course(object):

    course_id: str
    name: str
    capacity: int
    elected: int
    teacher: str
    major: str
    credit: str
    location: str
    schedule: str
    comment: str
    class_id: str # most important for electing
    enroll: str
    exam_date: str
    comment: str
    exam_typ: str

    def __post_init__(self):
        if not isinstance(self.capacity, int):
            self.capacity = int(self.capacity)
        if not isinstance(self.elected, int):
            self.elected = int(self.elected) if self.elected else 0


class CourseJar(list):

    def __repr__(self):
        return '<CourseJar{}>'.format(list.__repr__(self))


class CourseTaker(ViewState):

    pattern = re.compile(r'<input.*?name="(?P<key>(?!btnReturnX).*?)".*?value="(?P<value>.*?)".*?/>')

    @alertable(CoursesError)
    def take(self):
        return ViewState.submit(self)


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
             r'<td>(?P<class_id>[S\d]+)</td>'
             r'<td>(?P<enroll>.*?)\s*</td>'
             r'<td>(?P<exam_date>.*?)(?:&nbsp;)?</td>'
             r'<td>(?P<comment>.*?)(?:&nbsp;)?</td>'
             r'<td>(?P<exam_typ>.*?)</td>'
             r'\s*</tr>')
    pattern = re.compile(regex)
    if 'ItemStyle">' in html:
        for mo in pattern.finditer(html):
            kwargs = mo.groupdict()
            yield Course(**kwargs)
