#! /usr/bin/env python
#
# kvm.py Copyright (c) 2007-9 Joseph J Wolff, all rights reserved

from __future__ import with_statement # for thread locks

#import sentry
#sentry.check()

import sys, os, hashlib #, re, telnetlib, hashlib #, ANSI  #, tty
#from telnetlib import DO, DONT, WILL, WONT, theNULL, TTYPE, IAC, SB, SE, ECHO
from glob import glob
from time import sleep, ctime # strftime
from threading import Thread, RLock  # Semaphore
from socket import error as socket_exception
from string import uppercase, lower
from PIL import Image

#from minitags import h1,h2,h3,div,islist
#import hosting.meta as meta
#import meta

from utils import get_active_kvm_ports, addArgs, trace_import

trace = 0

if trace: trace_import (__name__)


# this doesn't work - importing just the name apprently kicks in the COW semantics
#from sys import stderr, stdout
#
# so do the regular "import sys", and set sys.stderr and sys.stdout:

#nope, cur nfg too - trace = open ('/var/log/apache2/kvm.log','a')
#works: trace = open ('/tmp/kvm.log','a')
#raise Exception, os.getlogin() # environ - 'APACHE_RUN_USER'


#user = os.getenv ('APACHE_RUN_USER', os.getenv ('LOGNAME', '') + '-debug')
#trace = 0 # open ('/var/log/libre/%s_kvm.log' % user, 'a')

# yuk - can't we just do the wsgi trick:
if os.getenv ('APACHE_RUN_USER', None):  # if true, apache is running
    sys.stdout = sys.stderr


vmbase = '/vm'
imgbase = '/img'
isobase = '/iso'
scriptbase = vmbase + '/scripts'
ipbase = '216.218.243.'

noimagelist = ('/images/noimage180.png',
  '/images/noimage400.png',
  '/images/noimage600.png',
  '/images/noimage640.png',
)

#if trace:
  #sys.stdout = trace
  #sys.stderr = trace
#  print >>trace, '='*80, '\n', ctime(), ': trace ON, vmbase:', vmbase, ', user:', user


### Consts, const objs, defs

monBase     = 23000
rdpBase     = 33000
serialBase  = 43000
vncJavaBase = 58000
vncBase     = 59000

ipRange      = xrange (2, 255)
vncRange     = xrange (5900, 6000)
vncHighRange = xrange (vncBase, vncBase + 1000)
vncJavaRange = xrange (vncJavaBase, vncJavaBase + 1000)
rdpRange     = xrange (3389,  3489)
rdpHighRange = xrange (rdpBase, rdpBase + 1000)
monRange     = xrange (2300, 2400)
monHighRange = xrange (monBase, monBase + 1000)
serialRange  = xrange (serialBase, serialBase + 1000)



### Classes

## Cmd - wraps command, parse of returned results, errors, etc
# - pass in a parser and command, or subclassable for customer parsers

from commands import getstatusoutput

class Cmd (object): # wraps system command and parser
  default = 'ps ax'

  def __init__ (self, c=None):
    self.command = c or self.default

  def parse (self):  # meant to be subclassed
    return [line.split() for line in self.lines]

  def __call__ (self, arg='', **kw):
    self.arg = arg
    try: self.command %= arg
    except: pass;
    self.command += ' '.join (['-%s %s' % (k,v)  for k,v in kw.iteritems()])
    #if trace: print self.command
    self.stat, self.rslt = getstatusoutput (self.command)
    #if trace: print self.stat, self.rslt
    self.lines = self.rslt.split ('\n')
    if self.stat != 0: return
    return self.parse()


## Cmd_netstat - tailored Cmd subclass for finding ports used by kvm instances
# Note that YOU HAVE TO BE ROOT to use netstat - FIXME

class Cmd_netstat (Cmd):
  #default = 'netstat -antp | grep -i LISTEN | grep kvm' 
  # This works, but causes downstream permissions errors on the image files.  sigh.
  # need to un kvm as, well, kvm (!). FIXME.
  default = 'sudo netstat -antp | grep -i LISTEN | grep kvm' 

  def parse (self):
    return [(int (re.findall (r':([0-9]+)', line) [0]), int (re.findall (r'([0-9]+)/kvm', line) [0])) for line in self.lines]



## VirtualMachine - the running (or ondisk, configured) vm
# - instantiatable either way

sid0 = hashlib.md5 ('0').digest()	# effectively a const

class VirtualMachine:
  trace = 0

  def __init__ (self, args={}, pid=0, ports=[]):  # , server=None):
    self.args  = args
    self.ports = ports
    self.pid   = pid	# program id
    self.mid   = 0	# machine id - dirname: ip, 'external' rdp, vnc, telnet port, etc
    self.sid   = sid0	# secure id - hash of mid
    self.up    = False
    self.rdpport = 0
    self.serport = 0
    self.monport = 0
    self.vncport = 0
    self.ip      = 0
    self.m       = 128
    self.mname   = ''
    self.images  = noimagelist
    self.imagesz = (0,0)
    self.w       = 640  # provide fallback defaults to avoid exceptions
    self.h       = 480
    self.sandbox = 0    # sandbox behavior, run w/'snapshot', restart every n minutes (via cron).
    self.permanent = 0  # permanent behavior, run at startup and try to always keep running (semantics on fault TBD).
    self.run     = 0    # run this vm at bootup / restart
    self.admin   = ''   # link to web admin or dev admin to show in vPanel for this vm
    self.dev     = ''   # link to dev instance to show in vPanel for this vm
    self.links   = ''   # add'l link or csv list of links to show in vPanel for this vm
    self.init (args, pid, ports)


  def init (self, args={}, pid=0, ports=[]):
    from kvm_monitor import Monitor  # import loop kluge
    if self.trace: print 'VM init:', pid, ports, self.up, args,

    if args:  # its from the args - either running or not
      addArgs (self, args, False)
    else:   # it's a live instance, init fm the pid/ports
      self.up = True

      for p in ports:
        if p in serialRange: self.serport = p
        if p in monRange or p in monHighRange: self.monport = p
        if p in vncRange or p in vncHighRange: self.vncport = p
        if p in rdpRange or p in rdpHighRange: self.rdpport = p
        # assert no overlap!

        if p > 20000:   # then it's an ip-based variable port, so extract ip
          self.ip = p % 1000

    if self.ip:
      self.ip = int (self.ip)  # normalize
      self.dirname = `self.ip`
      if not self.up:
        if not self.monport: self.monport = self.ip + monBase
        if not self.vncport: self.vncport = self.ip + vncBase
    elif self.rdpport:
      self.rdpport = int (self.rdpport)
      self.dirname = `self.rdpport`
    elif self.vncport:
      self.vncport = int (self.vncport)
      self.dirname = `self.vncport`
    elif self.mname:
      self.dirname=self.mname
    else:
      raise 'Unknown vm dirname / mid!' + `self.ports`

    self.mid   = self.dirname                           # may cause probs with mname..
    self.sid   = hashlib.md5 (self.mid).digest()        # secure id - hash of mid

    if self.monport: self.monitor = Monitor()
    if self.trace: print 'end:', self.up, self.mid, self.mname

  def __unicode__ (self):
    return '%s (%s)' % (self.mname, self.mid)

  def __repr__ (self):
    return u'VirtualMachine instance: ' + self.__unicode__()

  def screengrab (self):
    #if self.up: 
    w,h = server.screengrab (self)  # now handles down/noimg 5/8/9 jjw
    #else: 
    #  w,h = 0,0
    self.w = w
    self.h = h
    return w,h


  def send (self, msg):
    m = self.monitor.connect (port=self.monport)
    if self.trace: print 'vm.send:', m, self.monport, msg

    if m:
      rslt = m.sendandclean (msg)
      if self.trace: print 'vm send rslt:', len (rslt), rslt
      m.disconnect()
    else:
      rslt = 'VM Monitor is DOWN.'

    return rslt


  def msend (self, msgs):  # multiple send / return lists
    m = self.monitor.connect (port=self.monport)
    if self.trace: print 'vm msend:', m, self.monport, msgs
    rslt = []

    if m:
      for msg in msgs:
        rslt += [m.sendandclean (msg)]
      m.disconnect()
    else:
      for msg in msgs:
        rslt += ['VM Monitor is DOWN.']

    if self.trace: print 'vm msend rslt:', len (rslt), rslt
    return rslt


  def sendguest (self, s):
    m = self.monitor.connect (port=self.monport)
    if self.trace: print 'vm.sendguest:', m, self.monport, s, self.monitor.is_connected()

    if m:
      for line in s.splitlines():
        if line:
          if line.startswith ('sendkey'):  # allow sending of indiv chars to prep for script lines
            m.sendandclean (line)
          else:
            m.sendinstance (line)
        else:
          sleep (1) # pause on blank line!

      rslt = 'Sent to %s' % self.mname
      m.disconnect()
      #m.set_debuglevel(0)
    else:
      rslt = 'VM Monitor is DOWN.'

    return rslt


  def sendguestfile (self, fname):
    if not fname: return 'No File to send'
    f = open (fname)
    s = f.read()
    return self.sendguest (s)


  def asHtml (self):
    return server.asHtml (self.pid)


  def asDict (self):  #  asObject? asAttrs?
    return self.__dict__


  # shouldn't this be called 'render'?!  jjw 12/22/07
  def mergeTemplate (self, template):  # for rdp_link, vnc_link, etc
    return template % self.asDict()


manana='''

class vmStorage:
  name   = None
  file   = None
  type   = None
  drv    = None
  ro     = None
  locked = None
  removable = None
  attrs = ['name','file','type','drv','ro','locked','removable']

  def __init__ (self, line):  # takes line of monitor 'info block' results
    name,toks = line.split (':')   # for line in r.splitlines()]:
    self.name = name
    for tok in toks.split():
      pair = tok.split ('=')
      if len (pair) > 1:
        key, val = pair
        if key in self.attrs:
          self.__dict__ [key] = int (val) if val.isdigit() else val

  @property
  def fname (self):
    return self.file if self.file else 'No media present'

  @property
  def header (self):
    fixed = 'Removable' if self.removable else 'Fixed'
    typ = 'sd' if self.name [:2] == 'sd' else self.type
    return '%s %s: %s' % (fixed, typ, self.name)

  def as_html (self):
    s = h3 (self.type + ': ' + self.name)
    s += div (self.file + '(' + self.drv + ')')
    flags = [b for b in self.attrs [-3] if getattr (self,b,None)]
    s += ', '.join (flags)
    return div (s, cls='vmstorage')


class vmStorageList (list):
  def __init__ (self, rslt):  # takes monitor 'info block' results, a list
    if not islist (rslt):
      rslt = [rslt]

    for r in rslt:
      if r:
        self += [vmStorage (line) for line in r.splitlines()]
        #lines += r.splitlines()






### global module instances

server = KvmServer()


### thread methods

from gc import collect as garbage_collect

def worker():
  if trace: print >>trace, 'Thread worker: starting..', 'I am', os.getpid(), 'of', os.getppid()
  vms = server.getVms()
  count = 0
  if trace: print >>trace, 'Thread worker: Got vms..', 'I am', os.getpid(), 'of', os.getppid()

  while 1:
    #OK, for future ref: 
	# 1) do getports, save result, compare for changes - only up list iff changed
	# 2) reread dirs once a minute or so, maybe 5 minutes
    	# store as list, with dicts for byPath, byPid, byPort, byIp, byMd5, etc
    # for now, just re-getting copy means no thread issues!  More expensive, but still saves on images.

   try:
    grabbed = []
    count += 1
    for vm in vms:
      if vm.up:
        vm.screengrab()
        if vm.imagegrabbed: 
          grabbed += [vm.mname]

    if (count % 12) == 0: 
      collected = garbage_collect()
      if trace: print >>trace, 'Tick+lint:', count, collected, grabbed, 'I am', os.getpid(), 'of', os.getppid()
      trace.flush()
    else: 
      if trace: print >>trace, 'Tick:', count, grabbed, 'I am', os.getpid(), 'of', os.getppid()

   # FIXME - refresh vms HERE every 60 or so

   except Exception, e:
    print 'Worker loop exception:', e

   sleep (20)


#def createThread():
t = Thread (target=worker)
#t.name = 'PyKvmWorkerThread'
#if trace: print >>trace, t.getName(), 'Alive:', t.isAlive(), 'Daemon:', t.isDaemon()
if trace: print >>trace, t, 'Alive:', t.isAlive(), 'Daemon:', t.isDaemon()

def startThread():
  if trace: print >>trace, t, 'Starting Thread.. I am', os.getpid(), 'of', os.getppid()
  t.start() 
  if trace: print >>trace, t, 'startThread: Alive:', t.isAlive(), 'Daemon:', t.isDaemon(), \
      'I am', os.getpid(), 'of', os.getppid()
def stopThread():
  t.stop()



### Main, for non-module-import test/debugging

if __name__ == '__main__':
  print 'KVM Libre Hosting vMachine utility module (c)2007-8 The Libre Group'

  from optparse import OptionParser

  parser = OptionParser()
  #parser.add_option("-l", "--log", dest="logfile",
  #                help="log to FILE", metavar="FILE")
  #parser.add_option("-q", "--quiet",
  #                action="store_false", dest="verbose", default=True,
  #                help="don't print status messages to stdout")
  parser.add_option ("-p", "--perm", dest="perm", action='store_true',
                     help="Start all VMs marked as 'Permanent'")
  parser.add_option ("-d", "--down", dest="down", action='store_true',
                     help="Shut Down all running VMs with 'system_powerdown'")
  parser.add_option ("-s", "--screengrab", dest="scrall", action='store_true',
                     help="Perform screengrab on all running VMs")
  parser.add_option ("-x", "--sandboxes", dest="sbx", action='store_true',
                     help="Start / cycle all marked sandbox VMs")
#  parser.add_option ("-r", "--run", dest="runall", action='store_true',
#                     help="Run all VMs so marked (NYI)")
#  parser.add_option ("-k", "--kill", dest="killall", action='store_true',
#                     help="Shutdown/kill all running VMs (NYI)")

  (options, args) = parser.parse_args()

  if trace:
    print options, args

  vms = server.getVms()

  print
  print 'DOWN VMs:'

  for vm in vms:
    if not vm.up: print vm.mname

  print
  print 'UP VMs:'

  for vm in vms:
    #if vm.up: print vm.mname, vm.screengrab(), 'done.'
    if vm.up: print vm.mname

  print
  print 'Sandbox VMs:'

  for vm in vms:
    if vm.sandbox: print vm.mname, int(vm.up)*'(Up)'

  print
  print 'Permanent VMs:'

  for vm in vms:
    if vm.permanent: print vm.mname, int(vm.up)*'(Up)'

  if options.scrall:
    print
    print 'Screengrabbing up VMs:'

    for vm in vms:
      if vm.up: print vm.mname, ':', vm.screengrab(), 'done.'

  if options.sbx:
    print
    print 'Restarting / cycling running sandbox VMs:'

    for vm in vms:
      if vm.up and vm.sandbox: 
        print 'Running', vm.mname
        print server.vmScript (vm, 'restart')
        print 'Done.'
        print

  if options.perm:
    print
    print "Starting all (non-running) permanent VMs:"

    for vm in vms:
      if vm.permanent and not vm.up: 
        print 'Running:', vm.mname
        print server.vmScript (vm, 'restart')
        print 'Done.'
        print

  if options.down:
    print
    print "Shutting Down all running VMs with 'system_powerdown':"

    for vm in vms:
      if vm.up:
        print 'Stopping:', vm.mname
        print vm.send ('system_powerdown')

else:  # not main, imported as a module
  pass
  #s = '/tmp/kvm-pid-' + `os.getpid()`
  #print s
  #f = file (s, 'w')
  #f.write (s)
  #f.close()
'''



import jsonrpclib

# from kvm_server import VirtualMachine as LocalVM


#class RemoteVM (LocalVM):
#    def __init__ (self):
#        pass  # load from jsonrpc dict??

#from utils import Config, Result
import settings

if __name__ == "__main__":
    hosts = settings.hosts
    port = settings.port  # could just append to host(s)

    print hosts, port

    for host in hosts:
        server = jsonrpclib.Server(host)
        print server.add (5, 6)
        try:
            vmlist = server.getVmList()
        except:
            print jsonrpclib.history.request
            #{"jsonrpc": "2.0", "params": [5, 6], "id": "gb3c9g37", "method": "add"}
            print jsonrpclib.history.response

        print vmlist
