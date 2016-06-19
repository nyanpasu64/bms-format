#!/usr/bin/env python3

import sys

from plumbum import local, FG, BG
from pygments import styles

arr = sorted(styles.get_all_styles())
# mode = ['latex', 'tex']
mode = ['html']

def pygmentize(filename):
    pyg = local['pygmentize']
    # for style in arr:
    for style in ['tango']:
        cmd = '-f {2} -O full -P style={1} -P prestyles=white-space:pre-wrap;tab-size:4;-moz-tab-size:4; -o {0}.{1}.{3} {0}' \
            .format(filename, style, mode[0], mode[-1]) \
            .split()

        print(cmd)
        pyg[cmd] & FG

if __name__ == '__main__':
    pygmentize(sys.argv[1])