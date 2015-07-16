#! /usr/bin/env python
#
# kvm.py Copyright (c) 2007-9 Joseph J Wolff, all rights reserved

from __future__ import with_statement # for thread locks - needed on py 2.5 only

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

#from jsonrpclib import Server as RpcServer

import jsonrpclib
import settings

from utils import get_active_kvm_ports, addArgs, trace_import
from kvm_monitor import Monitor

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



#class KvmServerConnection (RpcServer):
#    pass  # keep host, etc?


## VirtualMachineBase - defines the base fields common to both local & remote VMs

class VirtualMachineBase:
    trace = 0
    sid0 = hashlib.md5 ('0').hexdigest()   # effectively a const

    def __init__ (self, **kw):
        initial_dict = dict (
            args  = kw,
            ip      = kw.pop ("ip", 0),          # IP address - this or one of the following 4 ports must be nonzero and fall into the ranges
            rdpport = kw.pop ("rdpport", 0),     # specificed for each - eg, rdpport must fall into rdprange or rdphighrange
            serport = kw.pop ("serport", 0),     # 2 of 4
            monport = kw.pop ("monport", 0),     # 3 of 4
            vncport = kw.pop ("vncport", 0),     # 4 of 4
            m       = kw.pop ("m", 128),         # Memory / RAM parm to KVM
            mname   = kw.pop ("mname", ''),      # text-base machine name - displayed w/spacify, symlinked, etc
            admin   = kw.pop ("admin", ''),      # link to web admin or dev admin to show in vPanel for this vm
            dev     = kw.pop ("dev", ''),        # link to dev instance to show in vPanel for this vm
            links   = kw.pop ("links", ''),      # add'l link or csv list of links to show in vPanel for this vm
            run     = kw.pop ("run", 0),         # bool - run this vm at bootup / restart
            sandbox = kw.pop ("sandbox", 0),     # bool - sandbox behavior, run w/'snapshot', restart every n minutes (via cron).
            permanent = kw.pop ("permanent", 0), # bool - permanent behavior, run at startup and try to always keep running (semantics on fault TBD).
            #parms  = '',                        # daemon, tablet, hda, hdb, hdc, parms?
            #extra_parms = {},

            # JJW 4/17/10 These have kw.pop for the RemoteVM instance only - could move to the RemoteVM __init__...

            up      = kw.pop ("up", False),
            mid     = kw.pop ("mid", 0),    # machine id - dirname: ip, 'external' rdp, vnc, telnet port, etc
            sid     = kw.pop ("sid", self.sid0), # secure id - hash of mid - start with sid0
            images  = kw.pop ("images", settings.noimagelist),
            # imagesz!
            )

        self.__dict__.update (initial_dict)
        self.base_fields = initial_dict.keys()  # ['mid','mname','monport']  

        ports = []  # list of open ports - for live vm only! (up==True)
        pid   = 0   # program id
        wd    = 0   # watch descriptor, for iNotify changes to parms or status - only valid on server


    def get_base_fields (self):
        return dict ([(k, self.__dict__ [k]) for k in self.base_fields])
        #self.init()  # call the descendant init

    def __unicode__ (self):
        return '%s (%s%s)' % (self.mname, self.mid, ', up' if self.up else '')

    def __repr__ (self):
        return u'%s: %s' % (self.__class__.__name__, self.__unicode__())



# print VirtualMachineBase().base_fields


class InvalidVM (VirtualMachineBase):
    def __init__ (self):
 	self.base_fields = []
	self.monitor = Monitor (0)  # 0 => invalid monitor

invalid_vm = InvalidVM()  # only need one, so export it


class LocalVM (VirtualMachineBase):
    def __init__ (self, path, **kw):      # possibly pass in path, & do screengrab, etc here? replace vmImagePath?
        VirtualMachineBase.__init__ (self, **kw)
        #self.__dict__.update (kw)
        self.path = path
        self.set_mid_and_ports()

    '''
    self.imagesz = (0,0)
    self.w       = 640  # provide fallback defaults to avoid exceptions
    self.h       = 480
    self.init (args, pid, ports)

  def init (self, args={}, pid=0, ports=[]):
    if self.trace: print 'VM init:', pid, ports, self.up, args,

    if args:  # its from the args - either running or not
      addArgs (self, args, False)
    else:   # it's a live instance, init fm the pid/ports
    '''

    def update (self, pid, ports):  # it's a live vm, update accordingly
        self.up = True
        self.pid = pid
        self.ports = ports

        for p in ports:
            if p in settings.serialRange: assert self.serport == p
            if p in settings.monRange or p in settings.monHighRange: assert self.monport == p
            if p in settings.vncRange or p in settings.vncHighRange: assert self.vncport == p
            if p in settings.rdpRange or p in settings.rdpHighRange: assert self.rdpport == p
            # assert no overlap!

            if p > settings.monBase:   # It has a mon_port, so it must be an ip-based variable port, so extract the ip
                assert self.ip == p % 1000

        #self.set_mid()


    def set_mid_and_ports (self):  # called at init
        #mid = self.mid  # for assert

        if self.ip:
            self.ip = int (self.ip)  # normalize
            self.dirname = `self.ip`
            if not self.up:
                if not self.monport: self.monport = self.ip + settings.monBase
                if not self.vncport: self.vncport = self.ip + settings.vncBase
        elif self.rdpport:
            self.rdpport = int (self.rdpport)
            self.dirname = `self.rdpport`
        elif self.vncport:
            self.vncport = int (self.vncport)
            self.dirname = `self.vncport`
        #elif self.mname:
        #    self.dirname=self.mname
        else:
            raise 'Unknown vm dirname / mid!' + `self.ports`

        self.mid   = self.dirname                           # may cause probs with mname..
        self.sid   = hashlib.md5 (self.mid).hexdigest()     # secure id - hash of mid

        #self.wd = inotifyx.add_watch (nd, self.dirname, mask)
        #self.wd = inotify.add_watch (self.dirname)

        self.monitor = Monitor (self.monport if self.monport else 0)
        if not self.mname: self.mname = 'VM_ID_' + self.mid

        if self.trace: print 'end:', self.up, self.mid, self.mname

        #if mid: assert mid == self.mid  # be sure it doesn't change!


    def asHtml (self):
        return server.asHtml (self.pid)


    def asDict (self):  #  asObject? asAttrs?
        return self.__dict__


    def render (self, template):  # for rdp_link, vnc_link, etc - was "mergeTemplate" chged 4/10 JJW
        return template % self.asDict()





class RemoteVM (VirtualMachineBase):
    def __init__ (self, rpc_server, **kw):
        VirtualMachineBase.__init__ (self, **kw)
        self.rpc_server = rpc_server


    def monitor_command (self, cmd):  # kvm monitor command (or list)
        return self.rpc_server.monitor_command (self.mid, cmd)


    def control_command (self, cmd):  # shell / start / stop / etc (create?) command
        return self.rpc_server.control_command (self.mid, cmd)


    def send (self, lines='', fname=''):  # send string or file via kvm sendkeys monitor command
        if lines:
            return self.rpc_server.monitor_send_lines (self.mid, lines)

        if fname:
            return self.rpc_server.monitor_send_file (self.mid, fname)  # fname must reside on server!!
            # future: read it on client..


    def screengrab (self):
        #if self.up:
        #w,h =
        return self.rpc_server.screengrab (self.mid)
        #images = ?
        #images.is_valid?
        #get_images?

        #else:
        #  w,h = 0,0
        self.w = w
        self.h = h
        return w,h

    #def __unicode__ (self):
    #    return '%s (%s)' % (self.mname, self.mid)

    #def __repr__ (self):
    #    return u'RemoteVM instance: ' + self.__unicode__()

    # monitor_command
    # control_command? or:
    # start, stop, status, shutdown_graceful, etc


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



class SecureTransport (jsonrpclib.Transport):

    # Secure SSL - HTTPS only, py2.6 or later
    def make_connection(self, host):
        # create a HTTP connection object from a host descriptor
        import httplib
        host, extra_headers, x509 = self.get_host_info(host)
        #if self.scheme == 'http':
        #    return httplib.HTTP(host)
        #else:
            # host may be a string, or a (host, x509-dict) tuple
        print 'HOST INFO:', host, extra_headers, x509
        return httplib.HTTPS(host, None, **(x509 or {}))



# from kvm_server import VirtualMachine as LocalVM


#class RemoteVM (LocalVM):
#    def __init__ (self):
#        pass  # load from jsonrpc dict??

#from utils import Config, Result
import settings

    


if __name__ == "__main__":
    hosts = settings.hosts
    port = settings.port  # could just append to host(s)

    #print hosts, port

    for host in hosts:
        #try:
            #server = KvmServerConnection (host)
            server = jsonrpclib.Server (host, transport=SecureTransport())
            print server, server.add (5, 6)
            tok = server.get_auth_token('my seed')
            print tok
            print 'NEXT:', hashlib.sha224 ('my seed' + tok).hexdigest()
            tok = server.next_token(tok)
            print tok
            print 'NEXT:', hashlib.sha224 ('my seed' + tok).hexdigest()
            tok = server.next_token(tok)
            print tok
            print 'NEXT:', hashlib.sha224 ('my seed' + tok).hexdigest()
            tok = server.next_token(tok)
            print tok
            vmlist = server.get_vm_list()
            #print 'SERVER VMLIST:', vmlist
            for vm in vmlist:
                #print vm
                vm = dict ([(str(k),v) for k,v in vm.items()])
                #print vm
                rvm = RemoteVM (server, **vm)
                print
                print rvm
                print 'Info block:'
                print rvm.monitor_command ('info block')
                print 'Screengrab:', rvm.screengrab()

        #except Exception, e:
            print e, host
            #print jsonrpclib.history.request
              #{"jsonrpc": "2.0", "params": [5, 6], "id": "gb3c9g37", "method": "add"}
            #print jsonrpclib.history.response



