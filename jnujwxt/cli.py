import os
import sys
import traceback
from getpass import getpass

import click
import urllib3
from prettytable import PrettyTable

path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, path)

from jnujwxt import log
from jnujwxt.config import config
from jnujwxt.engine import Jwxt
from jnujwxt.engine.course import Course
from jnujwxt.engine.error import LoginError
from jnujwxt.util import network_test


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_jwxt = Jwxt()

_cookiepath = os.path.join(config['jnujwxt']['cookies_path'], '%d.json')


def login(studentid='', resume=True):
    global _jwxt

    assert not _jwxt.is_login

    log.info('Login')
    if studentid:
        print('StudentID: ' + studentid)
    else:
        studentid = input('StudentID: ')

    resume_ok = False
    if studentid and resume:
        resume_ok = resume_cookie(studentid)

    if resume_ok:
        log.success('Login success')
    else:
        try:
            validcode_img = _jwxt.validcode_img()
            password = getpass()
            validcode_img.show()
            validcode = input('Validcode: ')
            _jwxt.login(studentid, password, validcode)
            log.success('Login success')
        except LoginError as LE:
            log.failure('Login failed: ' + str(LE))
            sys.exit(0)        


def logout(save=True):
    global _jwxt

    assert _jwxt.is_login

    studentid = _jwxt.student_id
    if save:
        save_cookie(studentid)
    else:
        _jwxt.logout()
        log.info('Logout')
        remove_cookie(studentid)


def save_cookie(studentid):
    global _jwxt
    global _cookiepath

    studentid = int(studentid)
    _jwxt.save_cookie(_cookiepath % studentid)
    log.info('Cookie saved')


def resume_cookie(studentid):
    global _jwxt
    global _cookiepath

    studentid = int(studentid)
    if os.path.exists(_cookiepath % studentid):
        _jwxt.resume_cookie(_cookiepath % studentid, studentid)
        if not _jwxt.is_login:
            log.info('Cookie expired')
            return False
        else:
            log.info('Cookie resumed')
            return True
    else:
        log.info('Cookie not stored')
        return False


def remove_cookie(studentid):
    global _cookiepath

    studentid = int(studentid)
    if os.path.exists(_cookiepath % studentid):
        os.remove(_cookiepath % studentid)
        log.info('Cookie removed')
    else:
        log.failure('Cookie not stored')


def cli():
    app(obj={})


@click.group()
@click.option('--no-color', is_flag=True, help='output with no color')
@click.option('--proxy', default=None, help='set proxy')
@click.option('--not-save', is_flag=True, help="don't save cookie")
@click.option('--not-resume', is_flag=True, help="don't resume cookie")
@click.option('--stu-id', '-u', default=None, help='student id')
@click.pass_context
def app(ctx=None, **kwargs):
    global _jwxt

    ctx.obj['SAVE'] = not kwargs.get('not_save', False)
    ctx.obj['RESUME'] = not kwargs.get('not_resume', False)
    ctx.obj['STUID'] = kwargs.get('stu_id', None)
    log.init(kwargs.get('no_color', False))
    proxy = kwargs.get('proxy', None)
    if proxy:
        log.debug('Add proxy ' + proxy)
        _jwxt.proxies = {'http': proxy, 'https': proxy}


@app.command('login')
@click.pass_context
def app_login(ctx, **kwargs):
    """do nothing but login"""

    login(ctx.obj['STUID'], ctx.obj['RESUME'])
    logout(ctx.obj['SAVE'])


@app.command('remove-cookie')
@click.option('--all', '-a', is_flag=True, help='remove all cookie')
@click.pass_context
def app_remove_cookie(ctx, **kwargs):
    """delete a cookie by student id"""

    if kwargs.get('all', False):
        global _cookiepath
        cookiedir = os.path.dirname(_cookiepath)
        count = 0
        for file in os.listdir(cookiedir):
            filename, ext = os.path.splitext(file)
            if filename.isnumeric() and ext == '.json':
                os.remove(os.path.join(cookiedir, file))
                log.debug(file + ' removed')
                count += 1
        log.info('%d cookies removed' % count)
    else:
        studentid = ctx.obj['STUID'] or input('StudentID: ')
        remove_cookie(studentid)


@app.command('best-entry')
@click.option('--thread', '-t', default=5, help='set thread')
@click.option('--timeout', default=3, help='set timeout')
@click.option('--write', '-w', is_flag=True, help='write back to settings.ini')
@click.option('--verbose', '-v', is_flag=True, help='verbose output')
def best_entry(**kwargs):
    """find the fastest entry of jwxt"""

    global _jwxt

    log.debug('best_entry start')
    with open(config['jnujwxt']['endpoint_list']) as epfile:
        endpoints = [e.strip().rstrip('/') for e in epfile.readlines()]

    with log.RunningBar('Network test'):
        best = network_test(
            endpoints,
            nt=kwargs.get('thread', 5),
            log=kwargs.get('verbose', False),
            timeout=kwargs.get('timeout', 3),
            proxies=_jwxt.proxies,
            headers={'Host': config['jnujwxt']['domain']},
            verify=False
        )

    if best:
        log.success('%s => %fs' % best)
        if kwargs.get('write', False):
            from .config import configpath
            config['jnujwxt']['endpoint'] = best[0]
            with open(configpath, 'w') as configfile:
                config.write(configfile)
            log.info('The result has been written to config/settings.ini')
        else:
            log.info('Please paste the result to config/settings.ini')
    else:
        log.failure('No available entry now, please retry later')

    log.debug('best_entry end')


@app.command('update-courses')
@click.option('--term-prefix', '-t', default=None, help='decide the term to search (default now)')
@click.option('--only-electable', '-e', is_flag=True, help='decide if jwxt only search electable courses')
@click.pass_context
def update_courses(ctx, **kwargs):
    """update the course database via online jwxt"""

    global _jwxt

    log.debug('update_courses start')
    login(ctx.obj['STUID'], ctx.obj['RESUME'])
    term_prefix = kwargs.get('term_prefix', None)
    only_electable = kwargs.get('only_electable', False)
    log.info('Update started, it might take a while')
    try:
        with log.RunningBar('Updating'):
            count = _jwxt.update_courses(term_prefix, only_electable)
    except KeyboardInterrupt as error:
        log.failure('Update stop')
    except Exception as error:
        log.critical('Update failed: ' + str(error))
        log.debug(traceback.format_exc())
    else:
        log.success('Updated %d courses' % count)
    finally:
        logout(ctx.obj['SAVE'])
        log.debug('update_courses end')


@app.command('query-courses')
@click.argument('name')
@click.option('--verbose', '-v', is_flag=True)
def query_courses(**kwargs):
    """simplely find courses by name"""

    log.debug('query_courses start')
    dbms = _jwxt.db_session
    columns = [Course.name, Course.credit, Course.schedule_id]

    if kwargs.get('verbose', False):
        columns.append(Course.teacher)
        columns.append(Course.comment)

    name = kwargs.get('name', '')
    query = dbms.query(*columns).filter(Course.name.like(name))
    table = PrettyTable(c.name for c in columns)

    with log.RunningBar('Querying'):
        for row in query.all():
            table.add_row(row)

    print(table)
    log.debug('query_courses end')


@app.command('elect-courses')
@click.argument('schedule-id', nargs=-1)
@click.pass_context
def elect_courses(ctx, **kwargs):
    """(*untested) elect courses by schedule id"""

    log.warning('This feature is untested')

    global _jwxt
    log.debug('elect_courses start')
    login(ctx.obj['STUID'], ctx.obj['RESUME'])
    xkcenter = _jwxt.xkcenter()
    if xkcenter.is_closed:
        log.failure('the xkcenter is closed')
    else:
        schedule_list = list(kwargs.get('schedule_id', ()))
        results = xkcenter.xkwar(schedule_list)
        for schedule_id, status in results:
            log.info(f'{schedule_id} => {status}')
    log.debug('elect_courses end')
    logout(ctx.obj['SAVE'])


@app.command('reset-config')
@click.option('-y', is_flag=True)
def reset_config(**kwargs):
    """reset configure"""

    yes = kwargs.get('y', False)
    if yes or input('Reset setting? [y/N] ').upper() in ['Y', 'YES']:
        from .config import init_default
        init_default()
        print('Reset')


if __name__ == '__main__':
    cli()
