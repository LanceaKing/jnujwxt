from argparse import ArgumentParser
from getpass import getpass

from . import DBSession, Jwxt
from .config import Config
from .courses import Course
from .utils import net_test


def best_entry():
    print('[*] The best jwxt entry is ...')
    best = net_test(Config.JWXT_NETS)
    if best:
        print('[*] {} => {}μs'.format(best[0], best[1]))
        print('[+] Please copy it to Config.JWXT')
    else:
        print('[-] No available entry now, please retry later')


def login_jwxt(jwxt):
    print('[+] Please login:')
    studentid = input('[$] StudentID > ')
    password = getpass('[$] Password > ')
    validcode_img = jwxt.validcode_img()
    validcode_img.show()
    validcode = input('[$] Validcode > ')
    jwxt.login(studentid, password, validcode)


def update_courses():
    from time import perf_counter
    jwxt = Jwxt()
    login_jwxt(jwxt)

    print('[*] Updating ...')
    start = perf_counter()
    count = jwxt.update_database()
    end = perf_counter()
    print('[*] Successfully update {} courses in {}s'
        .format(count, round(end - start, 2)))


def query_course(name):
    result = (
        DBSession()
        .query(Course)
        .filter(Course.name.like('%'+name+'%')).
        all()
    )
    for c in result:
        print(c)


def main():
    ap = ArgumentParser()

    features_gp = ap.add_mutually_exclusive_group()

    features_gp.add_argument('--best-entry', '-E',
        dest='best_entry',
        action='store_true',
        help='find the fastest entry of jwxt')

    features_gp.add_argument('--update-courses', '-U',
        dest='update_courses',
        action='store_true',
        help='update the course database via online jwxt')

    features_gp.add_argument('--query-course', '-Q',
        dest='course_name',
        action='store',
        help='simplely find the course by name')

    args = ap.parse_args()
    if args.best_entry:
        best_entry()
    elif args.update_courses:
        update_courses()
    elif args.course_name:
        query_course(args.course_name)
    else:
        ap.print_usage()
