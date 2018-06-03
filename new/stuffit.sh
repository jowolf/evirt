#!/usr/bin/env python 

import sys, os, fcntl, termios

# see:
# http://stackoverflow.com/questions/29614264/unable-to-fake-terminal-input-with-termios-tiocsti
# http://stackoverflow.com/questions/6191009/python-finding-stdin-filepath-on-linux

tty = os.ttyname(sys.stdin.fileno())

with open(tty, 'w') as fd:
    for c in ' '.join (sys.argv [1:]):
        fcntl.ioctl(fd, termios.TIOCSTI, c)
    
    fcntl.ioctl(fd, termios.TIOCSTI, '\n')

