import sys
from os.path import dirname

path = dirname(dirname(__file__))
sys.path.insert(0, path)

from jnujwxt.cli import main

if __name__ == '__main__':
    main()
