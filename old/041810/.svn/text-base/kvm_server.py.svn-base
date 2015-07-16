#! /usr/bin/env python
#
# kvm_server.py Copyright (c) 2007-10 Joseph J Wolff, all rights reserved


## KvmServer - runs on any/all vm host, does not need to be the same as the vm client
# uses JsonRPC or RPyC to communicate
# owns the vmList, directories, start/stop methods, create, etc
#
# does NOT own the host list - that's to be in the kvm_meta module


import os, hashlib

from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer

from utils import Config, get_active_kvm_ports
from settings import vmbase, scriptbase, monBase, vncBase, ipRange, serialRange, monRange, rdpRange, vncRange, monHighRange, rdpHighRange, vncHighRange, noimagelist  #, VirtualMachine

from kvm_core import LocalVM as VirtualMachine


trace = 0


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





### KvmServer class - one per host, handles vm lists, updates, paths, watches, statuses, etc -
# also accessed via rpc fm web controller

class KvmServer:
  trace = 0

  def __init__(self):
    self.vms = {}	# dict indexed by mid (machineid) - dirname, basically
    #self.vmsLock = RLock()  # fubar for multistack / multiprocess apache
    #self.init()

    self._walkVms()

    #vms = [VirtualMachine (pid=pid, ports=ports) for pid, ports in dct.iteritems()]
    self.vms = dict ([(vm.mid, vm) for vm in self.vmlist]) # by_mid
    # by_sid? by_wd? by_mname? by_pid is for live vms only - is it needed?

    self._updateLiveVms()


  #def init (self):
  #  # In an earlier implem, start all the vms
  #  self.refreshVms()


  def vmRead (self, path):      # load static vm from disk parms
    args = Config (path, 'parms.sh').get()
    if trace: print 'vmRead:', path, args
    if args:
      return VirtualMachine (**args)


  def _walkVms (self):	# sets and returns self.vmlist only - convert to dict of your choice - internal use
    vmlist = []

    for path, dirs, files in os.walk (vmbase):
      #if trace: print path, dirs, files
      for dir in dirs:
        if dir in ['old', 'templates', 'boot', 'mnt', 'tmp', 'scripts', 'pykvm']: dirs.remove (dir)

      vm = self.vmRead (path)
      if vm: vmlist += [vm]

    if self.trace: print '_walkVms:', vmlist  # time this diskVms fn!
    self.vmlist = vmlist
    return vmlist


  def _updateLiveVms (self):  # updates and returns self.vms dict - internal use
    dct = get_active_kvm_ports()  # returns pid / ports dict

    for pid, ports in dct.iteritems():
        mid = ports2mid (ports)
        if mid: assert isinstance (mid, basestring), type(mid)
        try:
            #print self.vms, mid, `mid`
            self.vms [mid].update (pid, ports)
        except Exception, e:
            print 'WARNING: Running VM not declared, pid: %s, ports: %s (%s)' % (pid, ports, e) #, mid

    if self.trace: print '_updateLiveVms:', self.vms
    return self.vms


  def getVmList (self):  # refreshes live vms in place, returns list, public use
    self._updateLiveVms()
    return self.vmlist


  def getVmListForRemote (self):
      return [vm.get_base_fields() for vm in self.getVmList()]
      #return [vm.__dict__ for vm in self.getVmList()]


  # deprecated
  def getVms (self, srt='mid'):  # None):  # refreshes live vms only, returns list, public use
    live_vms = dict ((vm.mid, vm) for vm in self.liveVms(False)) 

    if trace: print 'in getVms, grabbing vmsLock'

    with self.vmsLock:
      # update vm.up for live - assumes ports are the same!
      for mid, vm in self.vms.iteritems():
        if self.trace: print 'getVms:', mid, mid in live_vms, vm.up, 
	vm.up = mid in live_vms
	if self.trace: print vm.up

      # add new, if any
      for mid, vm in live_vms.iteritems():
	if mid not in self.vms:
	  self.vms [mid] = vm

    if trace: print "in getVms, after 'with' (released vmsLock)"

    lst = self.vms.values()
    if srt: lst.sort (key=lambda x: getattr (x,srt))  # need to fix for upper/lower on mname
    return lst


  # deprecated
  def refreshVms (self):  # refreshes both disk and live vms, builds new, keeps stuff fm old
    #live_vms = [(vm.mid, vm) for vm in self.liveVms()]
    #disk_vms = [(vm.mid, vm) for vm in self.diskVms()]  # new copy in the making
    live_vms = dict ((vm.mid, vm) for vm in self.liveVms())
    disk_vms = dict ((vm.mid, vm) for vm in self.diskVms())  # new copy in the making
    added = []
    deleted = []

    # check for new
    for mid, vm in disk_vms.iteritems():
      if mid not in self.vms:
	added += [mid]  	# no need to add self.vms [mid] = vm

    # delete old (upd delted list)
    for mid, vm in self.vms:
      if mid not in disk_vms:
	deleted += [mid] 	# no need to del self.vms [mid]

    # update for live
    for mid, vm in live_vms.iteritems():
      if not mid in disk_vms:  # check for deleted out from under the still-running vm!
        continue

      disk_vms [mid].up = True		# ports / pid?

      # carry forward info - md5, imgsz, etc
      if mid in self.vms:
        disk_vms [mid].imagemd5 = self.vms [mid].imagemd5
        disk_vms [mid].imagesz  = self.vms [mid].imagesz
        disk_vms [mid].images   = self.vms [mid].images

    with self.vmsLock:
      self.vms = disk_vms  # swap it out quickly, protected by thread lock

    if self.trace: print 'added: %s deleted: %s' % (added, deleted)
    return self.vms


  def getVm (self, mid):		# public vm access - is this still needed? perhaps as module/rpc fn?
    assert isinstance (mid, basestring)
    if mid in self.vms: return self.vms [mid]
    # assert above means this is no longer needed:
    # mid = str (mid)
    # #if self.trace: print mid, self.vms, mid in self.vms, self.vms [mid]
    # if mid in self.vms: return self.vms [mid]


  # deprecated
  def getLiveVm (self, thepid, getargs = True):		# deprecated
    if thepid:
      #dct = self.getLivePorts()
      dct = get_active_kvm_ports()
      if dct: 
        vm = VirtualMachine (pid=thepid, ports=dct [thepid])
        if getargs: vm.init (meta.get (os.path.join (vmbase, vm.dirname), 'parms.sh'))
        return vm


  # deprecated
  def getLiveVmByPort (self, theport, getargs = True):
    lst = Cmd_netstat()()
    if not lst: return None
    #if self.trace: print 'getLiveVmByPort:', theport, lst

    for port, pid in lst:
      # will return a flawed VM, with only this port showing, but this will work for now
      if port == int (theport): 
        #if self.trace: print 'getLiveVmByPort 2:', port, pid
	#return VirtualMachine (pid=pid, ports=[port])
        vm = VirtualMachine (pid=pid, ports=[port])
        if getargs: vm.init (meta.get (os.path.join (vmbase, vm.dirname), 'parms.sh'))
        return vm


  def getIps (self):  # available IPs
    ips = set (ipRange)     # ips = kvm.server.availableIPs()
    # old: return ['None', 'Pool'] + ips       # list of avail IPs incl none-needed, and alloc-from-pool

    used_ips = set ([vm.ip for vm in self.diskVms() if vm.ip])
    return list (ips - used_ips)


  # deprecated
  def getRdpPorts (self):
    rdps = [i for i in rdpRange]	# should really subtract out the alloced ones
    return ['None'] + rdps


  def getFiles (self, base, exts):  # assumes list of lowercase exts with "."
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


  def getIsos (self):
    return self.getFiles (isobase, ['.iso'])


  def getImgs (self):
    newdisks = [('New 2G disk', '2G'), ('New 4G disk', '4G'), ('New 8G disk', '8G'), ('New 20G Disk', '20G')]
    return newdisks + self.getFiles (imgbase, ['.qc2', '.img', '.hdd', '.raw'])


  def getFloppies (self):
    # nope - for some reason, kvm doesn't like 2 dir levels
    #return self.getFiles (imgbase + '/floppy', ['.qc2', '.img', '.hdd', '.raw'])
    return self.getFiles ('/floppy', ['.qc2', '.img', '.hdd', '.raw'])


  def getScripts (self, fold='', scriptbase=scriptbase):
    return self.getFiles (scriptbase + '/' + fold, ['.sh', '.py', 'rb']) #, ''])  # '' matches anything


  def screengrab (self, vm):   # assumes it's a live vm pid>0?
    path = self.vmPath (vm)
    if self.trace: print 'in screengrab:', path, vm.monport

    if not vm.up or not vm.monport:   # also maybe doing native vnc monitoring?
      return self.vmImageSize (vm)
      #return 0,0

    grab = path + '/screen.ppm'

    try:
      r = vm.send ('screendump ' + grab)
    except Exception, e:
      print 'In screengrab: ', e

    if self.trace: print 'screengrab:', r
    thm  = path + '/thumb.png'
    sml  = path + '/small.png'
    med  = path + '/medium.png'
    ful  = path + '/screen.png'

    if not os.access (grab, os.R_OK):  # F_OK for presence, R for read
      # Not running yet, or other problem, return 'noimg'es
      return self.vmImageSize (vm)
      #vm.images = noimagelist
      #vm.imagesz = (640,480)
      #return vm.imagesz

    try:
      img = Image.open (grab)
      md5 = hashlib.md5 (img.tostring()).digest()
    except Exception, e:
      print 'Screengrab PIL Open or tostring error:', e
      #return 0,0 old asof 5/8/9 JJW
      return self.vmImageSize (vm)
      #vm.images = noimagelist
      #vm.imagesz = (640,480)
      #return vm.imagesz

    if hasattr (vm, 'imagemd5') and vm.imagemd5 == md5:
      assert vm.imagesz == img.size
      vm.imagegrabbed = False
      return vm.imagesz   # only useful if vm is kept alive / persistent :-(
    else:
      vm.imagegrabbed = True

    vm.imagemd5 = md5
    smlimg = img.copy()
    medimg  = img.copy()
    vm.imagesz = img.size
    img.save (ful)
    img.thumbnail ((180,180), Image.ANTIALIAS)
    img.save (thm)
    smlimg.thumbnail ((400,400), Image.ANTIALIAS)
    smlimg.save (sml)
    medimg.thumbnail ((600,600), Image.ANTIALIAS)
    medimg.save (med)
    vm.images = thm, sml, med, ful
    if self.trace: print vm.images
    return vm.imagesz


  #def send (self, vm, msg):
  #  if not vm.monport: raise 'No monitor port!'
  #
  #  m=Monitor()
  #  if self.trace: print 'after Monitor create', `m`
  #
  #  m.connect (port=vm.monport)
  #  rslt = m.send (msg)
  #  m.disconnect()
  #  return rslt

  def vmPath (self, vm):
    #if trace: print 'in vmPath:', vm.dirname, os.path.join (vmbase, vm.dirname), vm.up
    return os.path.join (vmbase, vm.dirname)


  # deprecated
  def vmImagePaths (self, vm):  # this is old; should migrate to vm.images
    #if self.trace:
    #  print 'in vmImagePaths:', vm.dirname, os.path.join (vmbase, vm.dirname), vm.up

    path = os.path.join (vmbase, vm.dirname)

    thm  = path + '/thumb.png'
    sml  = path + '/small.png'
    med  = path + '/medium.png'
    ful = path + '/screen.png'

    return (thm, sml, med)


  def vmImagePresent (self, vm, imgpath):
    return os.access (imgpath, os.R_OK)  # F_OK for presence, R for read

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
    elif cmd == 'stop':	# kluge
      vm.up = False

    return rslt


### global module instances

server = KvmServer()


later='''
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

'''




temp='''
### PyINotify stuff - into it's own module, perhaps?

#from pyinotify import IN_MODIFY, ProcessEvent
import pyinotify

class FileEventHandler (pyinotify.ProcessEvent):
    def process_IN_MODIFY (self, event):
        print "File Modified:", event.pathname

    def process_IN_CREATE (self, event):
        print "File Created:", event.pathname

    def process_IN_DELETE (self, event):
        print "File Deleted:", event.pathname

wm = pyinotify.WatchManager()  # Watch manager stores watches and provides operations on them

notifier = pyinotify.Notifier (wm, FileEventHandler(), timeout=10)

filelist = [
    '/home/joe/Projects/evirt/test.sh',
    '/home/joe/Projects/evirt/blah/test.sh',
    '/home/joe/Projects/evirt/parms.sh',
    '/home/joe/Projects/evirt/blah/parms.sh',
]

wdd = wm.add_watch (filelist, pyinotify.IN_MODIFY | pyinotify.IN_CREATE | pyinotify.IN_DELETE)  #, rec=True) only works for dirs
'''


### Main, for non-module-import test/debugging

if __name__ == '__main__':
  print 'KVM Libre Hosting kvm_server standalone module (c)2007-10 Joseph J Wolff & The Libre Group'

  print server.vmlist

  class MySimpleJSONRPCServer (SimpleJSONRPCServer):
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

        pass
        #print 'Timeout!'
        # straight from http://trac.dbzteam.org/pyinotify/wiki/Tutorial
        temp='''
        assert notifier._timeout is not None, 'Notifier must be constructed with a short timeout'
        notifier.process_events()
        while notifier.check_events():  #loop in case more events appear while we are processing
            notifier.read_events()
            notifier.process_events()
            '''


    def handle_periodic_maintenance (self):  # currently 5 mins or so - JJW 4/18/10
        print 'Periodic maintenance - grab screens, etc'


  json_server = MySimpleJSONRPCServer(('localhost', 16861))
  json_server.register_function(pow)
  json_server.register_function (lambda x,y: x+y, 'add')
  json_server.register_function (lambda x: x, 'ping')
  json_server.register_function (server.getVmListForRemote, 'getVmList')
  json_server.register_function (lambda mid, s: server.getVm (mid).monitor.command (s), 'monitor_command')
  
  json_server.my_serve_forever()









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
