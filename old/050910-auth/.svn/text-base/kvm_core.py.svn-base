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

# Exported convenience singleton
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

'''


from xmlrpclib import ProtocolError

class SecureTransport (jsonrpclib.Transport):

    # Secure SSL - HTTPS only, py2.6 or later
    def make_connection (self, host):  # create a connection object from a host descriptor
        import httplib
        host, extra_headers, x509 = self.get_host_info(host)
        if trace: print 'HOST INFO:', host, extra_headers, x509
        return httplib.HTTPS(host, None, **(x509 or {}))

    # Had to copy this fm xmlrpclib.Transport parent, to get at the request & response headers
    def request(self, host, handler, request_body, verbose=0):
        # issue XML-RPC request

        h = self.make_connection(host)
        if verbose:
            h.set_debuglevel(1)

        self.send_request(h, handler, request_body)
        self.send_host(h, host)
        h.putheader("X-evirt-Auth-Token", token_auth.next_token())  # JJW
        self.send_user_agent(h)
        self.send_content(h, request_body)

        errcode, errmsg, headers = h.getreply()

        if errcode != 200:
            raise ProtocolError(
                host + handler,
                errcode, errmsg,
                headers
                )

        if not token_auth.verify_token (headers.getheader ("X-evirt-Auth-Token")):
            raise Exception ('Security Error - invalid token')

        self.verbose = verbose

        try:
            sock = h._conn.sock
        except AttributeError:
            sock = None

        return self._parse_response(h.getfile(), sock)



import settings

from utils.auth import token_auth


if __name__ == "__main__":
    hosts = settings.hosts
    port = settings.port  # could just append to host(s)

    #print hosts, port

    for host, shared_secret in hosts:
        #try:
            #server = KvmServerConnection (host)
            server = jsonrpclib.Server (host, transport=SecureTransport())
            #print server, server.add (5, 6)
            #print server, server.sayHello ('Fred')
            #tok = server.getAuthToken('my seed')

            token_auth.curr_token = server.get_auth_token (hashlib.sha224 (`shared_secret`).hexdigest())
            print token_auth.curr_token
            print 'NEXT ON CLIENT:', token_auth.get_next_token()
            print 'NEXT ON SERVER:', server.next_token(tok)
            print token_auth.curr_token
            print 'NEXT:', hashlib.sha224 (`shared_secret` + tok).hexdigest()
            tok = server.next_token(tok)
            print tok
            print 'NEXT:', hashlib.sha224 (`shared_secret` + tok).hexdigest()
            tok = server.next_token(tok)
            print tok

            print server, server.add (5, 6)

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



