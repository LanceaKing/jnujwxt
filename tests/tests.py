import sys
import unittest
from getpass import getpass
from os.path import abspath, dirname

path = dirname(dirname(abspath(__file__)))
sys.path.insert(0, path)

from jnujwxt import Jwxt
from jnujwxt.errors import CoursesError


class JwxtCase(unittest.TestCase):

    def setUp(self):
        self.assertTrue(jwxt.is_login)

    def test_xkcenter(self):
        xkcenter = jwxt.xkcenter()
        self.assertTrue(xkcenter.is_readme)
        self.assertTrue(xkcenter.is_closed) # 2018/07/16

    def test_course_search(self):
        count = jwxt.update_database()
        self.assertGreater(count, 3000) # 2018/07/13

    @unittest.skip('it\'s too dangerous to test')
    def test_course_hit(self):
        xkcenter = jwxt.xkcenter()
        ct = xkcenter.hit('20191S028')
        ct.take()


if __name__ == '__main__':
    jwxt = Jwxt()

    try:
        from userinfo import password, studentid
    except ImportError:
        studentid = input('[$] StudentID > ')
        password = getpass('[$] Password > ')

    validcode_img = jwxt.validcode_img()
    validcode_img.show()
    validcode = input('[$] Validcode > ')

    jwxt.login(studentid, password, validcode)

    unittest.main(verbosity=2)

    jwxt.logout()
