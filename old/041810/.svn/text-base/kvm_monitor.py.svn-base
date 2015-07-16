# kvm_monitor.py Copyright (c) 2007-10 Joseph J Wolff, all rights reserved

#from __future__ import with_statement # for py2.5 - thread locks?

#import os, re,

from telnetlib import Telnet
from socket import error as SocketException

from settings import monBase

#, hashlib #, ANSI  #, tty
  #from telnetlib import DO, DONT, WILL, WONT, theNULL, TTYPE, IAC, SB, SE, ECHO
#from glob import glob
#rom subprocess import Popen, call, STDOUT, PIPE
#from time import sleep, ctime # strftime

#from threading import RLock  # won't work at all to protect cross-process apache workers. :(
# Semaphore Thread

#from string import uppercase, lower
#from PIL import Image

#import hosting.meta as meta
#import meta
#from netstat import get_active_kvm_ports
#from minitags import h1,h2,h3,div,islist

#trace = 0

# cheapo ring buffer of 100-1000 or so [(cmd, resp)] tuples..
class History (list):
    max_entries = 100

    def add (self, x):
        self += [x]
        if len (self) > self.max_entries:
            self = self [10:]  # chop off the 10 oldest

    def last (self):
        return self [-1]


class Monitor (Telnet):
  trace = 0

  def __init__ (self, port=monBase):  # 1st usable IP = monBase +2  # host='localhost', 
    Telnet.__init__(self)
    self.host = 'localhost'
    self.port = port
    self.history = History()
    #self.rlock = RLock()  # from man kvm:  "Only one TCP connection at a time is accepted"
    if self.trace: self.set_debuglevel(1)


  def _connect (self):  # , port):  # port is required
    if self.trace: print 'Monitor #', self.port, 'connecting..',
    #self.rlock.acquire()

    try: 
      r = self.open (self.host, self.port)  # 2.6 - timeout added
    except SocketException, e:
      print 'Error opening monitor:', e
      return None

    if self.trace: print 'connected,', r
    inx = -1

    while inx < 0:  # need to pass in terminating chars
      inx, match, got = self.expect (["\(qemu\)"], 1)  # prompt is the only tailored item
      if self.trace: print inx, match, got
      if self.trace and match: print match.end()
      if not match:
        if self.trace: print 'kicking..',
        r = self.read_very_eager()
        if self.trace: print r
        self.send('\n')
        inx, match, got = self.expect (["\(qemu\)"], 1)  # prompt is the only tailored item
        if inx < 0: break;

    if self.trace: print 'ready.'
    return self


  def _disconnect (self):
    self.close()
    #self.rlock.release()  # should use 'with' stmt


  @property
  def is_connected (self):
    return self.get_socket()  # isinstance (socket._socketobject)?


  # Internal "_send..." methods - assume connected

  def _send (self, s):
    if not self.port: return "No Monitor Port - Monitor is not active."

    if self.trace: print 'sending..',
    s = str (s)
    self.write (s + '\n')
    rslt = self.read_until ("(qemu)", 1)  # need to pass in prompt or terminating chars
    rslt = str (rslt)
    if rslt.endswith ('(qemu)'):
      rslt = rslt [:-6]
    self.history.add ((s,rslt))
    if self.trace: print 'Monitor send rslt:', rslt
    return rslt


  def _sendkeys (self, s):
    if self.trace: 
      print 'sendkey:', s
    return self._send ('sendkey ' + s)
    #return self


  # Substitutes, translates, segments message, & does sendkeys, allowing a basic/crude form of automation
  def _sendline (self, s):
    # note: these don't work in gui xterms
    # alts = '`~[{]}\\|;:\'"?,>'
    remap = { '\n':'ret', '-':'minus', ' ':'spc', '=':'equal', '\t':'tab' } 
    mults = { '+':'shift-equal',
              '_':'shift-minus',
              '!':'shift-1',
              '@':'shift-2',
              '#':'shift-3',
              '$':'shift-4',
              '%':'shift-5',
              '^':'shift-6',
              '&':'shift-7',
              '*':'shift-8',
              '(':'shift-9',
              ')':'shift-0',
              '/':'kp_divide',
              #'.':'shift-kp_decimal', # nfg on newer kvm 10/08 JJW
              '`':'0x29',
              '~':'shift-0x29',
              '[':'0x1a',
              '{':'shift-0x1a',
              ']':'0x1b',
              '}':'shift-0x1b',
              '\\':'0x2b',
              '|':'shift-0x2b',
              ';':'0x27',
              ':':'shift-0x27',
              "'":'0x28',
              '"':'shift-0x28',
              #'/':'0x35',
              '?':'shift-0x35',
              ',':'0x33',
              '<':'shift-0x33',
              '.':'0x34',
              '>':'shift-0x34',
            }

    # gg: keyboard scan codes
    # http://en.wikipedia.org/wiki/Scan_code
    # http://www.jimprice.com/jim-asc.shtml
    # http://www.georgehernandez.com/h/xComputers/CharacterSets/ScanCodes.asp
    # http://www.handykey.com/twiddler2scancode.pdf
    # http://msdn2.microsoft.com/en-us/library/ms894073.aspx

    def xl8 (c):
      if c in remap: return remap [c]
      return c

    if s [-1] != '\n': s += '\n'  # ensure trailing 'enter'

    for c in s:
      # Note: the alt-kp sequences do not work reliably in gui xterms
      #if c in alts:
      #  self.sendkeys ('al' + '-kp_'.join ([c for c in 't' + str (ord (c))]))
      if c in mults:
        self._sendkeys (mults [c])
      elif c in uppercase:
        self._sendkeys ('shift-' + c.lower())
      else:
        self._sendkeys (xl8 (c))
      #sleep (1)  # telnet lib timing issues - 0.01 ngfg, 0.1 nfg, 0.5nfg NO! it's a conflict issue!

    return 'Line sent'  # self


  # deprecated, use tcp kvm connection:
  def dontneed_sendandclean (self, s):
    rslt = self.send (s)
    if self.trace: print '\n\nRaw send rslt', rslt
    rslt = rslt.rsplit ('\x1B[K', 1)[-1]
    #print '\n\nrslt2', rslt
    rslt = rslt.split ('\r\n') # use splitlines?
    #print '\n\nrslt3', rslt
    #print '\n\nrslt[0]&[-1]', `rslt[0]`,`rslt[-1]`
    if rslt [0].strip() == '' and rslt [-1] == '(qemu)':
      rslt = '\n'.join (rslt [1:-1])
    if self.trace: print '\n\nCleaned rslt', rslt
    return rslt


  # public sender methods - connect, send, disconnect

  def command (self, cmd):
    self._connect()  #  (port=self.monport)
    if self.trace: print 'Monitor.command:', m, self.port, cmd

    if self.is_connected:
      rslt = self._send (cmd)
      if self.trace: print 'Monitor command send rslt:', len (rslt), rslt
      self._disconnect()
    else:
      rslt = 'VM Monitor is DOWN.'

    return rslt


  def command_list (self, cmds):  # multiple cmd send / return lists
    self._connect() #  (port=self.monport)
    if self.trace: print 'Monitor.command_list:', self.port, cmds
    rslt = []

    if self.is_connected:
      for cmd in cmds:
        rslt += [self._send (cmd)]
      self._disconnect()
    else:
      for cmd in cmds:
        rslt += ['VM Monitor is DOWN.']

    if self.trace: print 'vm msend rslt:', len (rslt), rslt
    return rslt


  def send_lines (self, s):
    self._connect()  #  (port=self.monport)
    if self.trace: print 'Monitor.send_lines:', self.is_connected, self.port, s

    if self.is_connected:
      for line in s.splitlines():
        if line:
          if line.startswith ('sendkey'):  # allow sending of indiv chars to prep for script lines
            rslt = self._send (line)
          else:
            rslt = self._sendline (line)
        else:
          sleep (1) # pause on blank line!


      self._disconnect()
      #m.set_debuglevel(0)
    else:
      rslt = 'VM Monitor is DOWN.'

    return rslt


  def send_file (self, fname):
    if not fname: return 'No File to send'
    f = open (fname)
    s = f.read()
    return self.send_lines (s)


### Main, for non-module-import test/debugging

if __name__ == '__main__':
  print 'KVM Libre Hosting monitor module (c)2007-10 Joseph Wolff & The Libre Group'

  m = Monitor()

  print m.command ('info block')
  print m.command ('help')

  m._connect()
  m.interact()
  m._disconnect()

  print m.history