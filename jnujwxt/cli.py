from argparse import ArgumentParser

from .config import Config
from .utils import net_test


def best_entry():
    print('[*] The best jwxt entry is ...')
    best = net_test(Config.JWXT_NETS)
    if best:
        print('[*] {} => {}μs'.format(best[0], best[1]))
        print('[*] Please copy it to Config.JWXT')
    else:
        print('[-] No available entry now, please retry later')


def main():
    ap = ArgumentParser()
    ap.add_argument('--best-entry', '-E',
        dest='command',
        action='store_const',
        const=best_entry,
        help='find the fastest entry')

    args = ap.parse_args()
    if args.command:
        args.command()
    else:
        ap.print_usage()
