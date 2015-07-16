#! /usr/bin/env python
#
# kvm_server.py Copyright (c) 2007-10 Joseph J Wolff, all rights reserved


## KvmServer - runs on any/all vm host, does not need to be the same as the vm client
# uses JsonRPC or RPyC to communicate
# owns the vms dict, directories, start/stop methods, create, etc
#
# does NOT own the host list - that's to be in the kvm_meta module


import os, hashlib, random

#from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer
#from jsonrpclib.SecureJSONRPCServer import SecureJSONRPCServer
from SecureJSONRPCServer import SecureJSONRPCServer
from PIL import Image

from utils import Config, get_active_kvm_ports
from settings import vmbase, isobase, imgbase, flopbase, scriptbase, images_root, images_url, monBase, vncBase, ipRange, serialRange, monRange, rdpRange, vncRange, monHighRange, rdpHighRange, vncHighRange, noimagelist  #, VirtualMachine

from kvm_core import LocalVM, InvalidVM

#temp:
VirtualMachine = LocalVM

trace = 1
vms = {}        # dict indexed by mid (vm machineid) - dirname, basically
auth_token = None
auth_seed  = None  # shared secret

if not os.path.exists (vmbase):
    raise Exception, 'settings.vmbase must point to a valid location with your VMs'


# Notes 1a 4/12/10 mac:
# - init vm w/args only
# - upd w/pid/ports fm live
# - need ports2mid fn org fm vm.init
# - createVm should mkdir & save kwargs - can call fm ctrlr
# - editVm can be similar


def ports2mid (ports):
    mon = rdp = vnc = ser = ip = 0

    for p in ports:
        if p in monRange: mon = p
        if p in rdpRange: rdp = p
        if p in vncRange: vnc = p

        if p in monHighRange: ip = p % 1000
        if p in rdpHighRange: ip = p % 1000
        if p in vncHighRange: ip = p % 1000
        if p in serialRange: ip = p % 1000

    if ip: return `ip`
    if rdp: return `rdp`
    if vnc: return `vnc`
    if ser: return `ser`



### MyNotify - thin iNotify wrapper using lean & mean iNotifyx module

import inotifyx 

class MyNotify:
    # tried to save the namespace, here, but got obscure error about __trunc__ in the C module..:
    #from inotifyx import init, add_watch, rm_watch, get_events, IN_CREATE, IN_DELETE, IN_MODIFY, IN_MOVE, IN_ISDIR

    def __init__ (self):
        self.fd = inotifyx.init()
        self.wd = self._add (vmbase)
        self.paths = {}

    def _add (self, path):
        return inotifyx.add_watch (self.fd, path,
                inotifyx.IN_MODIFY | inotifyx.IN_CREATE | inotifyx.IN_DELETE | inotifyx.IN_MOVE
                )

    def add (self, path):  #, mid=0):
        wd = self._add (path)
        self.paths [wd] = path

    def check (self):
        events = inotifyx.get_events (self.fd, 0)  # 0 => don't block
        for event in events:
            self.process (event)

    def close (self):
        try:
            inotifyx.rm_watch (self.fd, self.wd)
        finally:
            os.close (self.fd)

    def process (self, event):
        global vms #, vmlist
        if self.wd == event.wd:  # process vmbase events - pid files, dir creates/deletes
            print event, `event`
            if event.mask & inotifyx.IN_ISDIR and event.mask & inotifyx.IN_CREATE: 
                print 'new dir:', event.name
                self.add (os.path.join (vmbase, event.name))
                # add vm here, too, just in case
        else:  # process subdir events:
            print event, `event`, self.paths [event.wd]
            path = self.paths [event.wd]

            # NOTE: Having both CREATE and MODIFY set in the mask creates double-events -
            # create always seems to be followed my modify, unless the file is empty - can we rely on this?!

            if event.name == 'parms.sh': # and event.mask & (inotifyx.IN_MODIFY | inotifyx.IN_CREATE):
                vm = _vm_read (path)
                if vm:
                    vms [vm.mid] = vm
                    self.paths [event.wd] = path
                    print 'Vm replaced or updated:', vm, self.paths
                else:
                    print 'No vm:', vm
                    # Should we take it down if it's up?  not now, may be just editing the parms file..
                    # if path in vms_by_path:
                    #     vm = vms_by_path [path]
                    #     vm.shutdown_graceful() or vm.shutdown_hard()  # need 'stopping' status - yellow letters!
                    # vms [vm.mid]
                print vms


# decorator for floating auth_token
def auth_required (func):
    #strip off auth-token & vfy
    #..call func
    #re-hash token with auth_seed & return
    pass


### module-level Kvm Server implem

def get_auth_token (seed):
    global auth_token, auth_seed
    auth_seed = seed
    auth_token = hashlib.sha224 (seed + `random.random()`).hexdigest()
    return auth_token


def next_token (tok):
    auth_token = hashlib.sha224 (auth_seed + tok).hexdigest()
    return auth_token


def _vm_read (path):       # load static vm from disk parms
    args = Config (path, 'parms.sh').get()
    if trace: print 'vm_read:', path, args
    if args:
      return LocalVM (path, **args)


def _walk_vms():           # sets and returns vms dict - internal use
    global vms
    vms = {}

    for path, dirs, files in os.walk (vmbase):
      #if trace: print path, dirs, files
      for dir in dirs:
        if dir in ['old', 'templates', 'boot', 'mnt', 'tmp', 'scripts', 'pykvm']: dirs.remove (dir)

      vm = _vm_read (path)
      if vm: vms [vm.mid] = vm
      mynotify.add (path)

    if trace: print '_walk_vms:', vms  # time this fn!
    return vms


def _update_live_vms():    # updates and returns vms dict - internal use
    global vms
    dct = get_active_kvm_ports()  # returns pid / ports dict

    for pid, ports in dct.iteritems():
        mid = ports2mid (ports)
        print pid, ports
        if mid: assert isinstance (mid, basestring), type(mid)
        try:
            #print self.vms, mid, `mid`
            vms [mid].update (pid, ports)
        except Exception, e:
            print 'WARNING: Running VM not declared, pid: %s, ports: %s (%s)' % (pid, ports, `e`) #, mid

    if trace: print '_update_live_vms:', vms
    return vms


def _init_vms():
    _walk_vms()
    _update_live_vms()


def _get_vm (mid):                # private retriever, checks for presence, returns local vm
    assert isinstance (mid, basestring)
    if mid in vms:
        return vms [mid]
    return invalid_vm


def get_vm (mid):                 # public vm access - via rpc, returns dict of base_fields to rpc caller to build remote vm
    return _get_vm (mid).get_base_fields()


def _get_vm_list():               # private, refreshes live vms in place, returns list
    _update_live_vms()
    return vms.values()  # sort!


def get_vm_list():                # calls private version, returns list of base_fields dicts, public
    return [vm.get_base_fields() for vm in _get_vm_list()]


def monitor_command (mid, cmd):   # public - talk to monitor on localhost, also via rpc
    if '\n' in cmd:
            cmd = cmd.splitlines()

    if isinstance (cmd, (list, tuple)):
        return _get_vm (mid).monitor.command_list (cmd)

    return _get_vm (mid).monitor.command (cmd)


def control_command (mid, cmd):        # public - start, stop, etc, also via rpc
    return _get_vm (mid).control_command (cmd)


def _get_files (base, exts):  # private - assumes list of lowercase exts starting with "."
    lst = []

    for path, dirs, files in os.walk (base):
        for dir in dirs:
            if dir in ['old', 'nfg', 'not', 'scripts', 'test', 'hidden']:
                dirs.remove (dir)

        for name in files:
            #if trace: print name, name [-4:].lower(), name [-4:].lower() in exts
            noext, ext = os.path.splitext (name)
            if ext.lower() in exts:
                lst += [(name, os.path.join (path, name))]

    return lst


def get_iso_images():
    return get_files (isobase, ['.iso'])


def get_disk_images():
    #newdisks = [('New 2G disk', '2G'), ('New 4G disk', '4G'), ('New 8G disk', '8G'), ('New 20G Disk', '20G')]
    #return newdisks + self.getFiles (imgbase, ['.qc2', '.img', '.hdd', '.raw'])
    return get_files (imgbase, ['.qc2', '.img', '.hdd', '.raw', '.qcow2', '.vmdk'])


def get_floppy_images():
    # nope - for some reason, kvm doesn't like 2 dir levels
    #return self.getFiles (imgbase + '/floppy', ['.qc2', '.img', '.hdd', '.raw'])
    return get_files (flopbase, ['.qc2', '.img', '.hdd', '.raw', '.qcow2', '.vmdk', '.flop', '.floppy'])


def get_scripts (fold='', scriptbase=scriptbase):
    return get_files (os.path.join (scriptbase, fold), ['.sh', '.py', 'rb'])  #, ''])  # '' matches anything


def _screengrab (vm):
    path = vm.path
    if trace: print 'In _screengrab:', path, vm.monport, vm.up

    if not vm.up or not vm.monport:
        return

    grab = os.path.join (images_root, vm.mid, 'screen.ppm')

    try: print os.makedirs (os.path.join (images_root, vm.mid))
    except: pass

    print os.path.join (images_root, vm.mid)

    try: r = vm.monitor.command ('screendump ' + grab)
    except Exception, e:
        print 'Exception in _screengrab vm.monitor.command: ', `e`, grab

    if trace: print 'screengrab:', r
    thm  = os.path.join (images_root, vm.mid, 'thumb.png')
    sml  = os.path.join (images_root, vm.mid, 'small.png')
    med  = os.path.join (images_root, vm.mid, 'medium.png')
    ful  = os.path.join (images_root, vm.mid, 'screen.png')

    if not os.access (grab, os.R_OK):  # F_OK for presence, R_OK for read
      print 'KVM screen grab not found:', grab
      return   # Not running yet, or other problem

    try:
      img = Image.open (grab)
    except Exception, e:
      print 'Screengrab PIL Open or tostring error:', `e`, grab
      return

    smlimg = img.copy()
    medimg  = img.copy()
    vm.imagesz = img.size
    img.save (ful)
    img.thumbnail ((180,180), Image.ANTIALIAS)
    img.save (thm)
    smlimg.thumbnail ((400,400), Image.ANTIALIAS)
    smlimg.save (sml)
    medimg.thumbnail ((600,600),) # Image.ANTIALIAS)
    medimg.save (med)

    vm.images = (  # to retrieve from the client's perspective
        os.path.join (images_url, vm.mid, 'thumb.png'),
        os.path.join (images_url, vm.mid, 'small.png'),
        os.path.join (images_url, vm.mid, 'medium.png'),
        os.path.join (images_url, vm.mid, 'screen.png'),
        )

    if trace: print vm.images
    return True


def screengrab (mid):
    vm = _get_vm (mid)
    return _screengrab (vm)




## Do module init:

mynotify = MyNotify()
_init_vms()
invalid_vm = InvalidVM()  # move to core



# test kvm server for jsonrpc dispatch

class KvmServer:
    def _dispatch (name, args):
        print name, args

        tok = self.pre_call (args)
        rslt = __dict__ [name] (args)
        return (rslt, _post_call (tok))

    def getAuthToken (self):
        return 'blah'

    def _pre_call (self, args):
        print 'pre_call', args



# # # # # OLD:

### KvmServer class - one per host, handles vm lists, updates, paths, watches, statuses, etc -
# also accessed via rpc fm web controller

class KvmOldServer:

  # deleted ...

  def getIps (self):  # available IPs
    ips = set (ipRange)     # ips = kvm.server.availableIPs()
    # old: return ['None', 'Pool'] + ips       # list of avail IPs incl none-needed, and alloc-from-pool

    used_ips = set ([vm.ip for vm in self.diskVms() if vm.ip])
    return list (ips - used_ips)


  # deprecated
  def getRdpPorts (self):
    rdps = [i for i in rdpRange]        # should really subtract out the alloced ones
    return ['None'] + rdps


  # ...

  def vmImagePresent (self, vm, imgpath):
    return os.access (imgpath, os.R_OK)  # F_OK for presence, R for read


  # These last 4: HERE 4/27/10 JJW
  
  def vmImageIsBlack (self, vm, imgpath):
    img = Image.open (imgpath)
    colors = img.getcolors() or []  # getcolors returns None on overflow, hence the []
    return len (colors) == 1

  def vmImageSize (self, vm):  # , imgpath):
    if vm.imagesz [0] <= 640:
      imgpath = self.vmPath (vm) + '/screen.png'
      if self.vmImagePresent (vm, imgpath):
        img = Image.open (imgpath)
        vm.imagesz = img.size
      else:
        vm.images = noimagelist
        vm.imagesz = (640,480)

    return vm.imagesz

  def vmCommand (self, vm, cmd):
    #if trace: print 'vmCommand:', vmPath (vm), cmd
    rslt,ret = sh (cmd, cwd=self.vmPath (vm))
    #if trace: print 'result:', `rslt`
    return (rslt, ret)

  def vmScript (self, vm, cmd, parms=''):
    if parms: parms = '"%s"' % parms
    rslt,ret = self.vmCommand (vm ,'bash /vm/scripts/%s.sh %s' % (cmd, parms))

    if cmd == 'status':
      vm.up = (int (ret) == 0)
    elif cmd == 'stop':        # kluge
      vm.up = False

    return rslt



### Main, for non-module-import test/debugging

if __name__ == '__main__':
  print 'KVM Libre Hosting kvm_server standalone module (c)2007-10 Joseph J Wolff & The Libre Group'

  print vms

  #class MySimpleJSONRPCServer (SimpleJSONRPCServer):
  class MyJSONRPCServer (SecureJSONRPCServer):
    timeout = 1
    timeouts_per_period = 300  # 5 mins
    timeout_count = 0


    def my_serve_forever(self):
        """Handle one request at a time until shutdown, respecting timeout."""
        self.__serving = True
        #self.__is_shut_down.clear()
        while self.__serving:
            self.handle_request()
        #self.__is_shut_down.set()


    def handle_timeout (self):
        if self.timeout_count > self.timeouts_per_period:
            self.timeout_count = 0
            self.handle_periodic_maintenance()

        self.timeout_count += 1

        #print 'before inotify check'
        mynotify.check()
        #print 'after inotify check'


    def handle_periodic_maintenance (self):  # currently 5 mins or so - JJW 4/18/10
        print 'Periodic maintenance - grab screens, etc'
        for vm in vms.values():
            _screengrab (vm)

    uncomment_for_debug='''
    def _handle_request_noblock(self):
        """Handle one request, without blocking.

        I assume that select.select has returned that the socket is
        readable before this function was called, so there should be
        no risk of blocking in get_request().
        """
        try:
            request, client_address = self.get_request()
        except socket.error, e:
            print 'EXCEPTION', e
            return
        if self.verify_request(request, client_address):
            try:
                self.process_request(request, client_address)
            except:
                self.handle_error(request, client_address)
                self.close_request(request)
    '''


  json_server = MyJSONRPCServer(('localhost', 16861), certFile='cert.pem')
  json_server.register_function(pow)
  json_server.register_function (lambda x,y: x+y, 'add')
  json_server.register_function (lambda x: x, 'ping')
  #json_server.register_function (server.getVmListForRemote, 'getVmList')
  #json_server.register_function (lambda mid, s: server.getVm (mid).monitor.command (s), 'monitor_command')

  json_server.register_function (get_auth_token)
  json_server.register_function (next_token)

  json_server.register_function (get_vm)
  json_server.register_function (get_vm_list)
  json_server.register_function (monitor_command)
  json_server.register_function (control_command)
  json_server.register_function (get_iso_images)
  json_server.register_function (get_disk_images)
  json_server.register_function (get_floppy_images)
  json_server.register_function (get_scripts)
  json_server.register_function (screengrab)

  json_server.my_serve_forever()

  mynotify.close()







  sys.exit()



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
