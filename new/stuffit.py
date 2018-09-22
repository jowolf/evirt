# - coding: UTF8 -

import sys, os, fcntl, termios

def getParentPidList():
    pid = os.getpid()
    results = []

    while not pid in [1,0]:
      results += [pid]
      #print ([l.split (':') for l in open ('/proc/%s/status' % pid).readlines() if ':' in l])
      pid = int (dict (l.split (':') for l in open ('/proc/%s/status' % pid).readlines()) ['PPid'].strip())

    #print (results)
    return results

# see:
# http://stackoverflow.com/questions/29614264/unable-to-fake-terminal-input-with-termios-tiocsti
# http://stackoverflow.com/questions/6191009/python-finding-stdin-filepath-on-linux

"""
print (sys.stdin.isatty(), sys.stdin.fileno())
print (sys.__stdin__.isatty(), sys.__stdin__.fileno())
print (os.readlink('/proc/self/fd/%s' % sys.stdin.fileno()))
print (os.readlink('/proc/self/fd/%s' % sys.__stdin__.fileno()))
print (os.ctermid())
print (os.getpid(), os.readlink('/proc/%s/fd/%s' % (os.getpid(), sys.__stdin__.fileno())))
print (os.getppid(), os.readlink('/proc/%s/fd/%s' % (os.getppid(), sys.__stdin__.fileno())))

#from sh import tty
#tty()  # not a tty

from sh import pstree
print (pstree (['-ap',]))

'''
  ├─systemd,3399 --user
  │   ├─(sd-pam),3400
  │   ├─dbus-daemon,3434 --session --address=systemd: --nofork --nopidfile...
  │   ├─dconf-service,3605
  │   │   ├─{dconf-service},3608
  │   │   └─{dconf-service},3609
  │   ├─gconfd-2,3696
  │   ├─gnome-terminal-,4732
  │   │   ├─bash,4738
  │   │   │   └─ssh,26060 -t -o StrictHostKeyChecking=no -p 2222 ...
  │   │   ├─bash,17709
  │   │   │   └─python,26211 -c...
  │   │   │       ├─{python},26213
  │   │   │       └─{python},27868
  │   │   ├─bash,26438
  │   │   │   └─mc,27960
  │   │   │       └─bash,27962 -rcfile .bashrc
  │   │   │           └─python,28040 /usr/local/bin/stuffit
  │   │   │               ├─pstree,28043 -ap
  │   │   │               └─{python},28045
'''

#import psutil, os
#print (psutil.Process(os.getpid()).ppid())
#print (psutil.Process(os.getppid()).ppid())

print (os.popen("ps -p %d -oppid=" % os.getppid()).read().strip())
pppid = os.popen("ps -p %d -oppid=" % os.getppid()).read().strip()
print (os.readlink('/proc/%s/fd/%s' % (pppid, sys.__stdin__.fileno())))

#sys.exit()

#tty = sys.argv[1]  # nope same error

try:
  tty = os.ttyname(sys.stdin.fileno())
except:
  tty = os.readlink('/proc/%s/fd/%s' % (pppid, sys.__stdin__.fileno()))
"""

for pid in getParentPidList():
  try:
    #tty = os.readlink('/proc/%s/fd/%s' % (pid, sys.__stdin__.fileno()))
    tty = os.readlink('/proc/%s/fd/%s' % (pid, 0))  # 0 seems to always be stdin
    #print (tty)
    if tty.startswith ('pipe:'):
        continue

    with open(tty, 'w') as fd:
      for c in ' '.join (sys.argv [1:]):
        fcntl.ioctl(fd, termios.TIOCSTI, c)

      fcntl.ioctl(fd, termios.TIOCSTI, '\n')
      sys.exit()  # exit on 1st success
  except Exception as e:
    print (e)


