# evm_server.py module Copyright (c) 2007-10 Joseph J Wolff, all rights reserved

## evm_server module - KvmServer class & related for directory watching, realtime changes
# - runs on any/all vm host, does not need to be the same as the vm client
# - uses JsonRPC or RPyC to communicate
# - owns the vms dict, directories, start/stop methods, create, etc
#
# does NOT own the host list - that's to be in the evm_meta or evm_hosts module


import os
from inspect import getmembers # , ismethod, isclass, getclasstree, isfunction,
from time import sleep
from PIL import Image

from evm_utils import Config, get_active_kvm_ports, sh, ports2mid

from settings import vmbase, isobase, imgbase, flopbase, scriptbase, images_root, images_url, monBase, vncBase, ipRange, serialRange, monRange, rdpRange, vncRange, monHighRange, rdpHighRange, vncHighRange, noimagelist  #, VirtualMachine

import settings

from evm_core import LocalVM, invalid_vm


trace = 0 or settings.trace
vms = {}        # dict indexed by mid (vm machineid) - dirname, basically

if not os.path.exists (vmbase):
    raise Exception, 'settings.vmbase must point to a valid location with your VMs'



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



### module-level Kvm Server implem

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
        if trace: print pid, ports
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
    print 'MID', mid, 'TYPE', type(mid)
    assert isinstance (mid, basestring)
    if mid in vms:
        return vms [mid]
    return invalid_vm


def _get_vm_list():               # private, refreshes live vms in place, returns list
    _update_live_vms()
    return vms.values()  # sort!


def _get_files (base, exts, recursive=True):  # private - assumes list of lowercase exts starting with "."
    lst = []

    for path, dirs, files in os.walk (base):
        if not recursive:
            dirs [:] = []  # can't just set to [], because COW kicks in...

        print dirs

        for dir in dirs:
            if dir in ['old', 'nfg', 'not', 'scripts', 'test', 'hidden']:
                dirs.remove (dir)

        for name in files:
            #if trace: print name, name [-4:].lower(), name [-4:].lower() in exts
            noext, ext = os.path.splitext (name)
            if ext.lower() in exts:
                lst += [(name, os.path.join (path, name))]

    return lst


def _screengrab (vm):
    path = vm.path
    if trace: print 'In _screengrab:', path, vm.monport, vm.up

    if not vm.up or not vm.monport:
        return

    grab = os.path.join (images_root, vm.mid, 'screen.ppm')

    try: os.makedirs (os.path.join (images_root, vm.mid))
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


def _do_command (mid, cmd):
    vm = _get_vm (mid)
    rslt,ret = sh (cmd, cwd=vm.path)
    return (rslt, ret)


### KVM Server

class KvmServerUnknownMethodException (Exception):
    pass


class KvmServer (object):
    def __init__ (self):
        self.exports = dict ([(k,v) for k,v in getmembers (self) if not k.startswith ('_')])

    def _dispatch (self, name, args):
        if trace: print name, args

        if not name in self.exports:
            raise KvmServerUnknownMethodException, (name, `args`)

        fn = self.exports [name]
        auth_required = getattr (fn, 'auth_required', False)

        if auth_required:
            tok = self._verify_token_before_call (args)

        rslt = fn (*args)
        if trace: print rslt

        if auth_required:
            self._gen_next_token_after_call (tok)

        return rslt


    ## vm methods - require mid, typically called from RemoteVM

    def get_vm (self, mid):  # public vm access - via rpc, returns dict of base_fields to rpc caller to build remote vm
        return _get_vm (mid).get_base_fields()


    def monitor_command (self, mid, cmd):   # public - talk to monitor on localhost, also via rpc
        if '\n' in cmd:
            cmd = cmd.splitlines()

        if isinstance (cmd, (list, tuple)):
            return _get_vm (mid).monitor.command_list (cmd)

        return _get_vm (mid).monitor.command (cmd)


    #def control_command (self, mid, cmd):        # public - start, stop, etc, also via rpc
    #    return _get_vm (mid).control_command (cmd)


    def screengrab (self, mid):
        vm = _get_vm (mid)
        return _screengrab (vm)


    def control_command (self, mid, cmd, parms=''):
        if parms: parms = '"%s"' % parms
        vm = _get_vm (mid)
        os.chdir (vm.path)

        #print vm.path, os.getcwd()  # /home/vm shows up as getcwd :(

        if vm.path != os.getcwd():
            raise Exception, 'Unable to change directory to: %s' % vm.path

        command = 'bash %s/%s.sh %s' % (scriptbase, cmd, parms)
        print command
        rslt,ret = _do_command (mid , command)  # 'bash %s/%s.sh %s' % (scriptbase, cmd, parms))

        #print rslt, ret

        if cmd == 'status':
            vm.up = (int (ret) == 0)
        elif cmd == 'stop':        # kluge
            vm.up = False

        return rslt


    ## Derived & compound commands - someday these could be pure python or use bash templates

    def start (self, mid):
        #vm = _get_vm (mid)
        return self.control_command (mid, 'start')
        return 'Started'  # should ret 'func_result' class - w/'succeeded' bool, str, rslt code, etc

    def hard_stop (self, mid):
        #vm = _get_vm (mid)
        self.control_command (mid, 'stop')  # could use templates for these..
        return 'Hard stop'

    def graceful_stop (self, mid):
        vm = _get_vm (mid)

        for s in ['ctrl_alt_del', 'acpi 1', 'acpi 2',  'hard']:  # 'acpi 3', 'acpi 4',
            if s == 'ctrl_alt_del':
                print 'Sending ctrl-alt-del...'
                vm.monitor.command ('sendkey ctrl-alt-delete')
                if vm.monitor.is_up:
                    print 'Pausing 10 seconds...'
                    sleep (10)
            elif s.startswith ('acpi'):
                print 'Sending ACPI system_powerdown...'
                vm.monitor.command ('system_powerdown')  # send_acpi_powerdown()
                if vm.monitor.is_up:
                    print 'Pausing 5 seconds...'
                    sleep (5)
            else:
                print 'Doing hard stop.'
                self.hard_stop (mid)

            if not vm.monitor.is_up:   # vm.is_still_up()
                break

        return 'Graceful shutdown: ' + s

    def restart (self, mid):
        vm = _get_vm (mid)

        s = self.graceful_stop()
        s += ', ' + self.start()


    ## server-wide methods

    def get_vm_list (self):  # calls private version, returns list of base_fields dicts, public
        return [vm.get_base_fields() for vm in _get_vm_list()]


    def screengrab_all (self):
        for vm in vms.values():
            _screengrab (vm)


    def get_iso_images(self):
        return _get_files (isobase, ['.iso'])


    def get_disk_images(self):
        return _get_files (imgbase, ['.qc2', '.img', '.hdd', '.raw', '.qcow2', '.vmdk'])


    def get_floppy_images(self):
        return _get_files (flopbase, ['.qc2', '.img', '.hdd', '.raw', '.qcow2', '.vmdk', '.flop', '.floppy'])


    def get_scripts (self, fold='', scriptbase=scriptbase, recursive=False):
        #print scriptbase, fold
        return _get_files (os.path.join (scriptbase, fold), ['.sh', '.py', 'rb'], recursive)  #, ''])  # '' matches anything


    def get_available_ips (self):  # available IPs
        ips = set (ipRange)

        used_ips = set ([vm.ip for vm in vms.values() if vm.ip])
        return list (ips - used_ips)


    def get_available_rdp_ports (self):
        rdps = set (rdpRange)

        used_rdps = set ([vm.rdpport for vm in vms.values() if vm.rdpport])
        return list (rdps - used_rdps)


    def setup (self):
        'Set up directories, permissions, images - ensure present with proper user/group, perms, etc - must be run from root'

        if os.geteuid():
            raise Exception, "'Setup' option must be run from root"

        try:
            os.makedirs (settings.vmbase)
            os.makedirs (settings.images_root)
        except Exception, e:
            print '(%s)' % `e`

        print 
        print 'Setting permissions'
        rslt,ret = sh ('chown -R %s:%s *' % (settings.web_user, settings.web_group), cwd=settings.vmbase)
        print rslt, ret
        rslt,ret = sh ('chown -R %s:%s *' % (settings.web_user, settings.web_group), cwd=settings.images_root)
        print rslt, ret
        rslt,ret = sh ('chown -R %s:%s *' % (settings.web_user, settings.web_group), cwd=settings.project_root)
        print rslt, ret
        # scriptbase, too?
        #rslt,ret = sh ('chmod - %s:%s *' % (settings.web_user, settings.web_group), cwd=settings.images_root)
        #print rslt, ret
        #what about touch output.log? into ensure?


    deploy_methods = ('copy','link','move')

    def deploy (self, ip, mid, mname, rdpport=None, hda='disk0.qcow2', hdb=None, cdrom=None, m=256, permanent=0, sandbox=0, daemon=1, **parms):
        'Set up new virtual machine & dirs, copy files & images - must be run from root'

        if os.geteuid():
            raise Exception, "'Deploy' option must be run from root"

        try:
            os.makedirs (os.path.join (settings.vmbase, mid))
            os.makedirs (os.path.join (settings.images_root, mid))
        except Exception, e:
            print '(%s)' % `e`

        ip = int(ip)
        assert ip or mid
        #assert rdpport in rdpRange - set accordingly
        assert ip in ipRange, `ipRange`

        rslt,ret = sh ('chown -R %s:%s .' % (settings.web_user, settings.web_group), cwd=settings.vmbase)
        if ret: return rslt

        rslt,ret = sh ('chown -R %s:%s .' % (settings.web_user, settings.web_group), cwd=settings.images_root)
        if ret: return rslt

        rslt,ret = sh ('rsync -av %s %s' % (os.path.join (settings.project_root, 'images', 'noimage*.png'), settings.images_root))
        if ret: return rslt

        '''
        copy template
        copy/link/move vm
        read & rewrite template with new values
        t copy noimages
        n touch output, bak? not nbeeded if parms are set right
        '''


### Exported convenience singletons

kvm_server = KvmServer()
mynotify = MyNotify()


## Do module init:

_init_vms()



# # # # # OLD:

### KvmServer class - one per host, handles vm lists, updates, paths, watches, statuses, etc -
# also accessed via rpc fm web controller

class KvmOldServer:

  # These last 4: HERE 4/27/10 JJW
  # only 3 left JW 7/4/10 HERE

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
