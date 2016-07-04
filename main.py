#!/usr/bin/env python

import sys

from formats.bms import BmsFile
from formats.bmsdump import get_tree


def main():
    argv = sys.argv

    with open(argv[1], 'rb') as f:
        data = f.read()
        tree = BmsFile(data).parse()

        print(get_tree(tree))

if __name__ == '__main__':
    main()
