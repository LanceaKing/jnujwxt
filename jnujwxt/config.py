import os
from configparser import ConfigParser, ExtendedInterpolation

basedir = os.path.dirname(os.path.abspath(__file__))

configpath = os.path.join(basedir, 'settings.ini')


def init_default():
    from mako.template import Template
    tpl_path = os.path.join(basedir, 'doc', 'settings.ini.mako')
    tpl = Template(filename=tpl_path)
    with open(configpath, 'w') as configfile:
        configfile.write(tpl.render(basedir=basedir))


if not os.path.exists(configpath):
    init_default()

config = ConfigParser(interpolation=ExtendedInterpolation())
config.read(configpath)
