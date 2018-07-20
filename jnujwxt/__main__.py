import sys
from os.path import abspath, dirname

path = dirname(dirname(abspath(__file__)))
sys.path.insert(0, path)

from jnujwxt.cli import main

if __name__ == '__main__':
    main()
