#! env/bin/python

#/usr/bin/python

import datetime, os
# does not preserve order, nor formatting: import yaml
# not needed, use rt loader - import yamlordereddictloader

#from ruamel import yaml
from ruamel.yaml import YAML
from pprint import pformat
from sh import cloud_localds
from string import Template
#from collections import OrderedDict
import clg


## Globals

trace = 0  # 1:misc 2:docs/decls; 4:actions/sections; 8:commands/args, 16:update dict; 32:inherit

declarations = {}  # loaded dynamically

installpath = os.path.dirname (__file__)


## Classes

class Section (object):
    _sections = []
    _commands = dict (
        description = 'Command & control for Linux KVM (Kernel Virtual Machine) VMs as defined in ev.yaml',
        help        = 'Command & control for Linux KVM (Kernel Virtual Machine) VMs as defined in ev.yaml',
        subparsers = {},
    )
    if trace & 8: print ('COMMANDS', _commands)

    def __init__ (self, data):
        # This must be first before other vars are declared :-)
        self.actions = [ a for a in dir (self) if not a.startswith ('_') ] # should be a class init
        self.data = data
        self.name = data.pop ('section')
        self.action = data.pop ('action')
        self._sections += [self]
        if trace & 4:
            print ('ACTIONS', self.actions)
            print ('ACTION', self.action)
            print ('SECTIONS', self._sections)

    # class function
    def _parse():
        cmd  = clg.CommandLine (Section._commands)
        args = cmd.parse()
        if trace & 8: print ('ARGS:', args)
        return args

    def _match (self, args):
        cmd_name = self.name.split ('.') [0]
        if trace & 8: print ('COMMAND', args.command0, cmd_name)  #os.path.basename(self.name))
        return args.command0 == cmd_name

    def _content (self):
        content = self.data ['content'] if 'content' in self.data else yaml.dump (self.data, Dumper=yaml.RoundTripDumper)
        content = Template (content).safe_substitute (declarations)
        return content

    def _process (self):
        fn, parm = list (self.action.items()) [0]
        assert fn in self.actions
        fn = self.__getattribute__(fn)
        if trace & 4: print ('FUNCTION', fn)
        fn (parm)

    def _parms (self, decls):
        '''
        Build parms from declarations for start, stop, monitor, etc - ports, etc -
        Could break out into sep module or inh class for bsx rules
        '''
        def trailing_number(s):  # could split out vmname as well, with or without '.'
            return int (s [len (s.rstrip ('0123456789')):] or '0')

        if trace & 2: print ('DECLS:', decls)

        #-drive file=boot-disk.img,if=virtio
        #-drive file=seed.iso,if=virtio

        # Note: the 'or' sntx does not allow for blank decls, while the 'get' sntx does

        vmname  = decls.get ('vmname') or os.path.basename (os.getcwd())
        workdir = decls.get ('workdir') or '.evirt'
        ext     = decls.get ('ext', 'qc2')
        user    = decls.get ('user', os.environ.get ('USER'))

        hda     = decls.get ('hda') or '%s.%s' % (vmname, ext)
        #hdb    = decls.get ('hdb') or "-hdb %s" % os.path.join (workdir, 'cloudinit.qc2')
        hdb     = decls.get ('hdb', os.path.join (workdir, 'cloudinit.qc2'))
        hdc     = decls.get ('hdc')
        hdd     = decls.get ('hdd')

        drives  = decls.get ('drives', "-drive file=%s,if=virtio " % hda)
        if hdb: drives += "-drive file=%s,if=virtio " % hdb
        if hdc: drives += "-drive file=%s,if=virtio " % hdc
        if hdd: drives += "-drive file=%s,if=virtio " % hdd

        vmdir   = decls.get ('vmdir') or os.getcwd()
        ipbase  = decls.get ('ipbase', '216.172.133')
        iplast  = decls.get ('iplast', trailing_number (os.path.basename (os.getcwd())))  # last tumbler of IP4 address
        fullip  = decls.get ('fullip', '%s.%s' % (ipbase, iplast) if iplast else '')
        #tapif  = decls.get ('tapif', 'tap-%s' % (iplast or vmname))
        tapif   = decls.get ('tapif', 'tap-%s' % vmname)
        macaddr = decls.get ('macaddr', "de:ad:be:ef:%02d:%02d" % ((iplast / 100), (iplast % 100)))
        net     = decls.get ('net', "-net tap,ifname=%s,script=no,downscript=no -net nic,model=virtio,macaddr=%s" % (tapif,macaddr))

        # note: this should be generically done for the whole decls dict:
        net = Template (net).safe_substitute (decls)

        vncport = decls.get ('vncport', (59000 + iplast - 5900))
        monport = decls.get ('monport', (23000 + iplast))
        mon     = decls.get ('mon', "-monitor telnet:127.0.0.1:%s,server,nowait,nodelay" % monport)
        vnc     = decls.get ('vnc', "-vnc :%s" % vncport)
        rdpport = decls.get ('rdpport', (39000 + iplast))
        parms   = decls.get ('parms', '')

        # configure hostdirs / passthru folder(s)

        hostdirs = decls.get ('hostdirs', [])
        for n,path in enumerate (hostdirs):
          path = Template (path).safe_substitute (decls)
          if os.access (path, os.R_OK):
            #parms += "-fsdev local,security_model=none,id=fsdev%i,path=%s -device virtio-9p-pci,id=fs%i,fsdev=fsdev%i,mount_tag=hostshare%i " % (n,path,n,n,n)
            parms += "-virtfs local,security_model=mapped-xattr,id=fs%i,path=%s,mount_tag=hostshare%i " % (n,path,n)
          else:
            print ("Warning - path not found: %s - creating" % path)
            os.makedirs (path)

        # configure spinup commands

        spinup = decls.get ('spinup', [])
        for n,path in enumerate (spinup):
          path = Template (path).safe_substitute (decls)
          if not os.access (path, os.R_OK):
            print ("Warning - spinup script not found: %s" % path)
          else:
            spinup [n] = path

        # update locals back to decls dict

        ud = dict (
            installdir = installpath,
            vmname  = vmname,
            workdir = workdir,
            ext     = ext,
            hda     = hda,
            hdb     = hdb,
            hdc     = hdc,
            hdd     = hdd,
            drives  = drives,
            vmdir   = vmdir,
            iplast  = iplast,
            ipbase  = ipbase,
            fullip  = fullip,
            tapif   = tapif,
            macaddr = macaddr,
            net     = net,
            vncport = vncport,
            monport = monport,
            mon     = mon,
            vnc     = vnc,
            rdpport = rdpport,
            parms   = parms,
            hostshares = ' '.join (hostdirs),
            spinup_command_names = ' '.join (spinup),
            #date    = datetime.date.today().isoformat(),
            date    = datetime.datetime.today().ctime(),

            # could do touch here, or python symlink: ln -s /vm/$ip /vm/$mname >& /dev/null
            #  or ln -s /vm/$ip /vm/$ip/$mname >& /dev/null
            # same for rdpport, vncport, spiceport, ?
        )

        if trace & 16: print ('UPDATE', ud)
        decls.update (ud)

        # Note: this should be generically done for the whole decls dict:
        decls ['net'] = Template (net).safe_substitute (decls)

        # add files list

        decls ['file1'] = ''
        decls ['file2'] = ''
        decls ['file3'] = ''
        decls ['file4'] = ''
        decls ['file5'] = ''
        decls ['file6'] = ''
        decls ['file7'] = ''
        decls ['file8'] = ''

        if decls.get ('files'):
          #print (decls ['files'])
          for n,f in enumerate (decls ['files']):
            #print ('FILES')
            #print (f)
            #print ('file%d' % (n+1))
            f = Template (f).safe_substitute (decls)
            if os.access (f, os.R_OK):
              decls ['file%d' % (n+1)] =   \
                ("- path: %s\n" % (f if f.startswith('/') else os.path.join ('/home', user, f)))  + \
                 "    content: |\n"     + \
                 ''.join ([('      ' + Template (lin).safe_substitute (decls)) for lin in open(f)])
                # owner nfg: cloud-init can't find joe
                # ("    owner: %s\n" % user) + \
                # "    permissions: '0770'\n" + \
                #
                # so that the embedded dest in the existing yaml looks like this, with a current indent of 4:
                #$file1
                # ...
            else:
              print ("Warning - file not found: %s - skipping" % f)

        return decls

    def save (self, reldir):
        assert '..' not in reldir
        assert not reldir.startswith ('/')
        assert 'workdir' in declarations
        reldir = Template (reldir).safe_substitute (declarations)
        path = os.path.join (reldir, self.name)
        if trace: print ('Saving', path)
        os.makedirs (reldir, exist_ok=True)
        open (path, 'w').write (self._content())

    def load (self, var):
        assert var == 'declarations'
        #globals() [var] = self.data
        declarations.update (self.data)  # allow multiple updates
        self._parms (declarations)

    def _do (self, shell='bash'):
        assert shell == 'bash'
        from sh import bash
        cmd = shell + ' -c ' + self._content()
        if trace: print ('RUNNING:', cmd)
        #'sh ('-c', 'echo "RUNNING" %s &&' % ))
        print (bash ('-c', self._content()))

    def command (self, more):
        "Save file & add command to argparse list"
        self.save (declarations ['workdir'])
        self._commands ['subparsers'].update (more)

    def inherit (self, flist):
        if trace & 32: print (flist)
        for fname in flist:
            if trace & 32: print ('inheriting', fname)
            # Read & apply sections from named yaml from <install dir>/templates
            if os.access (fname, os.R_OK):  # check cwd first
                if trace & 32: print ('reading', fname)
                readYaml (fname)
            elif os.access (os.path.join (installpath, 'templates', fname), os.R_OK):  # then check templates
                if trace & 32: print ('reading', os.path.join (installpath, 'templates', fname))
                readYaml (os.path.join (installpath, 'templates', fname))
            else:
                raise Exception ('File not found: ' + fname)


## Functions

def stuffit (s):
    import sys, fcntl, termios  #, os

    # see:
    # http://stackoverflow.com/questions/29614264/unable-to-fake-terminal-input-with-termios-tiocsti
    # http://stackoverflow.com/questions/6191009/python-finding-stdin-filepath-on-linux

    tty = os.ttyname(sys.stdin.fileno())

    s += "\n"

    with open(tty, 'w') as fd:
        for c in ' '.join (sys.argv [1:]):
            fcntl.ioctl(fd, termios.TIOCSTI, c)

    #fcntl.ioctl(fd, termios.TIOCSTI, '\n')


def readYaml (pth):
    yaml = YAML (typ='rt')  # rt gives ordered dicts - nope: yaml.loader = yamlordereddictloader.SafeLoader
    g = yaml.load_all (open (pth))

    #old:
    #g = yaml.safe_load_all (open ('ev.yaml'))  # , Loader=yaml.CLoader)

    # g is a generator object, make list (then zip into a list of tuples)
    #docs = [OrderedDict (d) for d in g]
    docs = [d for d in g]

    if trace & 2:
        for d in docs:
            print ('DOC:', pformat (d))
            print ('DOCS LEN', len (docs))

    for d in docs:
        Section (d)._process()


## Main

evyaml = "ev.yaml"

if not os.access (evyaml, os.R_OK):  # start w/Base, look for args
  # readYaml ('base.yaml')
  # Ask, then copy the repo version as a starting point
  if input ("No ev.yaml found - copy starter template? [y/n]").lower() == 'y':
    from sh import cp
    if trace: print ('Copying %s starter file' % evyaml)
    cp (os.path.join (installpath, evyaml), evyaml)
  else:
    import sys
    sys.exit()


readYaml (evyaml)


args = Section._parse()

# use dict here
for s in Section._sections:
    if s._match (args):
        s._do()
