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

trace = 4  # 1: misc 2: docs, decls, 4: actions, sections; 8: commands / args, 16: update dict

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
        if trace & 2: print ('DECLS:', decls)

        #-drive file=boot-disk.img,if=virtio \
        #-drive file=seed.iso,if=virtio

        # Note: the 'or' sntx does not allow for blank decls, while the 'get' sntx does

        vmname  = decls.get ('vmname') or os.path.basename (os.getcwdb())
        workdir = decls.get ('workdir') or '.evirt'
        ext     = decls.get ('ext', 'img')

        hda     = decls.get ('hda') or '%s.%s' % (vmname, ext)
        #hdb    = decls.get ('hdb') or "-hdb %s" % os.path.join (workdir, 'cloudinit.qc2')
        hdb     = decls.get ('hdb', os.path.join (workdir, 'cloudinit.qc2'))
        hdc     = decls.get ('hdc')
        hdd     = decls.get ('hdd')

        drives  = "-drive file=%s,if=virtio " % hda
        if hdb: drives += "-drive file=%s,if=virtio " % hdb
        if hdc: drives += "-drive file=%s,if=virtio " % hdc
        if hdd: drives += "-drive file=%s,if=virtio " % hdd

        vmdir   = decls.get ('vmdir') or os.getcwd()
        iplast  = decls.get ('iplast') if 'iplast' in decls else int (os.path.basename (os.getcwd()))  # last tumbler of IP4 address
        macaddr = decls.get ('macaddr', "de:ad:be:ef:%02d:%02d" % ((iplast / 100), (iplast % 100)))
        #net     = decls.get ('net', "-net nic,macaddr=%s -net tap,ifname=tap-%s,script=no,downscript=no" % (macaddr, iplast))
        #net     = decls.get ('net', "-net nic,macaddr=%s -net tap,ifname=tap-%s,helper=/etc/qemu-ifup,downscript=no" % (macaddr, iplast))
        #net     = decls.get ('net', "-net nic,macaddr=%s -net tap,helper=/etc/qemu-ifup" % macaddr)
        #net     = decls.get ('net')
        net     = decls.get ('net',
                             "-device virtio-net,netdev=net0,mac=%s -netdev tap,id=net0,ifname=tap-%s,script=no,downscript=no" % (macaddr, iplast))

        vncport = decls.get ('vncport', (59000 + iplast - 5900))
        monport = decls.get ('monport', (23000 + iplast))
        mon     = decls.get ('mon', "-monitor telnet:127.0.0.1:%s,server,nowait,nodelay" % monport)
        vnc     = decls.get ('vnc', "-vnc :%s" % vncport)
        rdpport = decls.get ('rdpport', (39000 + iplast))

        ud = dict (
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
            macaddr = macaddr,
            net     = net,
            vncport = vncport,
            monport = monport,
            mon     = mon,
            vnc     = vnc,
            rdpport = rdpport,
            #date    = datetime.date.today().isoformat(),
            date    = datetime.datetime.today().ctime(),

            # could do touch here, or python symlink: ln -s /vm/$ip /vm/$mname >& /dev/null
            #  or ln -s /vm/$ip /vm/$ip/$mname >& /dev/null
            # same for rdpport, vncport, spiceport, ?
        )

        if trace & 16: print ('UPDATE', ud)
        decls.update (ud)

        # add files
        decls ['file1'] = ''
        decls ['file2'] = ''
        decls ['file3'] = ''

        if decls.get ('files'):
          #print (decls ['files'])
          for n,f in enumerate (decls ['files']):
            #print ('FILES')
            #print (f)
            #print ('file%d' % (n+1))
            decls ['file%d' % (n+1)] =   \
                 ("- path: %s\n" % f)  + \
              "    content: |\n"     + \
              ''.join ([('      ' + lin) for lin in open(f)])
              # so that the embedded dest in the existing yaml looks like this, with a current indent of 4:
              #$file1
              # ...

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
        print (flist)
        for fname in flist:
            print ('inheriting', fname)
            # Read & apply sections from named yaml from <install dir>/templates
            if os.access (fname, os.R_OK):  # check cwd first
                print ('reading', fname)
                readYaml (fname)
            elif os.access (os.path.join (installpath, 'templates', fname), os.R_OK):  # then check templates
                print ('reading', os.path.join (installpath, 'templates', fname))
                readYaml (os.path.join (installpath, 'templates', fname))
            else:
                raise Exception ('File not found: ' + fname)


## Functions

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

if not os.access (evyaml, os.R_OK):  # ask then copy the repo version as a starting point
  if input ("No ev.yaml found - copy starter template? [y/n]").lower() == 'y':
    from sh import cp
    if trace: print ('Copying %s starter file' % evyaml)
    cp (os.path.join (installpath, evyaml), evyaml)
  else:
    import sys
    sys.exit()


readYaml (evyaml)


args = Section._parse()

for s in Section._sections:
    if s._match (args):
        s._do()
