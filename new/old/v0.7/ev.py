#! env/bin/python

#/usr/bin/python

import os
# does not preserve order, nor formatting: import yaml
# not needed, use rt loader - import yamlordereddictloader

#from ruamel import yaml
from ruamel.yaml import YAML
from pprint import pformat
from sh import cloud_localds
from string import Template
#from collections import OrderedDict
import clg

trace = 1
#declarations = {}  # done dynamically


## Classes

class Section (object):
    def __init__ (self, data):
        # This must be first before other vars are declared :-)
        self.actions = [ a for a in dir (self) if not a.startswith ('_') ]
        if trace: print (self.actions)

        self.data = data
        self.name = data.pop ('section')
        self.action = data.pop ('action')
        if trace: print (self.action)

    def _content (self):
        content = self.data ['content'] if 'content' in self.data else yaml.dump (self.data, Dumper=yaml.RoundTripDumper)
        content = Template (content).safe_substitute (declarations)
        return content

    def _process (self):
        fn, parm = list (self.action.items()) [0]
        assert fn in self.actions
        fn = self.__getattribute__(fn)
        if trace: print (fn)
        fn (parm)

    def _parms (self, decls):
        '''
        Build parms from declarations for start, stop, monitor, etc - ports, etc -
        Could break out into sep module or inh class for bsx rules
        '''
        print (decls)

        iplast  = decls.get ('iplast') if 'iplast' in decls else int (os.path.basename (os.getcwd()))  # last tumbler of IP4 address
        print (iplast)
        macaddr = decls.get ("de:ad:be:ef:%02d:%02d" % ((iplast / 100), (iplast % 100)))
        net     = decls.get ('net', "-net nic,macaddr=%s -net tap,ifname=tap-%s,script=no,downscript=no" % (macaddr, iplast))
        vncport = decls.get ('vncport', (59000 + iplast - 5900))
        monport = decls.get ('monport', (23000 + iplast))
        mon     = decls.get ('mon', "-monitor telnet:127.0.0.1:%s,server,nowait,nodelay" % monport)
        vnc     = decls.get ('vnc', "-vnc :%s" % vncport)
        rdpport = decls.get ('rdpport', (39000 + iplast))

        ud = dict (
            iplast  = iplast,
            macaddr = macaddr,
            net     = net,
            vncport = vncport,
            monport = monport,
            mon     = mon,
            vnc     = vnc,
            rdpport = rdpport,

            # could do touch here, or python symlink: ln -s /vm/$ip /vm/$mname >& /dev/null
            #  or ln -s /vm/$ip /vm/$ip/$mname >& /dev/null
            # same for rdpport, vncport, spiceport, ?
        )

        decls.update (ud)
        return decls

        '''
        other param examples:
        if [[ $sandbox ]]; then snapshot=1; fi

        if ! [[ $k ]];   then k=en-us; fi
        parms="$parms -k $k"

        if [[ $tablet ]];   then parms="$parms -usbdevice tablet"; fi
        if [[ $snapshot ]]; then parms="$parms -snapshot"; fi
        if [[ $boot ]];     then parms="$parms -boot $boot"; fi
        if [[ $cdrom ]];    then parms="$parms -cdrom $cdrom"; fi
        if [[ $hdb ]];      then parms="$parms -hdb $hdb"; fi
        if [[ $hdc ]];      then parms="$parms -hdc $hdc"; fi
        if [[ $hdd ]];      then parms="$parms -hdd $hdd"; fi
        if [[ $m ]];        then parms="$parms -m $m"; fi

        if [[ $respawn ]];  then respawn="-r"; fi
        '''

    def save (self, reldir):
        assert '..' not in reldir
        assert not reldir.startswith ('/')
        assert 'workdir' in declarations
        reldir = Template (reldir).safe_substitute (declarations)
        path = os.path.join (reldir, self.name)
        print ('Saving', path)
        os.makedirs (reldir, exist_ok=True)
        open (path, 'w').write (self._content())

    def load (self, var):
        assert var == 'declarations'
        globals() [var] = self.data
        self._parms (declarations)

        #globals() [var] = {}  # so 'declarations' is there now, but empty
        #for k,v in self.data.items():
        #    print (k,v)
        #    if isinstance (v, str):
        #        if v.startswith ('eval '):
        #            #declarations [k] = eval (v[5:], locals = declarations)  # sntx: no keyword agrs, despite docs saying so
        #            declarations [k] = eval (v[5:], None, declarations)
        #        else:
        #            declarations [k] = Template (v).safe_substitute (declarations)
        #    else:
        #        declarations [k] = v
        #    print (k, declarations[k])

    def do (self, shell):
        assert shell == 'sh'
        from sh import sh
        print (sh ('-c', 'echo "RUNNING" %s &&' % shell + self._content()))

    def command (self, more):
        cmd = clg.CommandLine (more)
        args = cmd.parse()
        print (args)  #, args.integers)
        print (args.command0, os.path.basename(self.name))
        if args.command0 == os.path.basename(self.name):
            self.do ('sh')

## Main

yaml = YAML (typ='rt')  # rt gives ordered dicts - nope: yaml.loader = yamlordereddictloader.SafeLoader
g = yaml.load_all (open ('ev.yaml'))

#old:
#g = yaml.safe_load_all (open ('ev.yaml'))  # , Loader=yaml.CLoader)

# g is a generator object, make list (then zip into a list of tuples)
#docs = [OrderedDict (d) for d in g]
docs = [d for d in g]

if trace & 2:
    for d in docs:
        print (pformat (d))
    print ('LEN', len (docs))

for d in docs:
  Section (d)._process()
