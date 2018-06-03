#! env/bin/python

#/usr/bin/python

import os
import yaml
from pprint import pformat
from sh import cloud_localds

trace = 1

## Classes

class Section (object):
    def __init__ (self, meta, data):
        # this must be first before other vars are declared :-)
        print (dir(self))
        print (self.__dir__())
        print (self.__dict__)
        self.actions = [ a for a in dir (self) if not a.startswith ('_') and a != 'process']
        if trace: print (self.actions)

        self.meta = meta
        self.data = data
        self.name = meta.pop ('section')
        items = list (meta.items())  # a list consisting of one duple
        if trace: print (items)
        assert len (items) == 1
        items = items [0]  # one duple
        self.action = items  # the duple - fn, parm
        if trace: print (self.action)

    def process (self):
        fn, parm = self.action
        assert fn in self.actions
        fn = self.__getattribute__(fn)
        if trace: print (fn)
        fn (parm)

    def save (self, reldir):
        path = os.path.join (reldir, self.name)
        print ('Saving', path)
        open (path, 'w').write (self.data ['content'] if 'content' in self.data else yaml.dump(self.data))

    def load (self, var):  # should be 'declarations'
        locals() [var] = self.data

    def do (self, shell):  # 'should be 'sh'
        from sh import sh
        print (sh ('-c', 'echo "RUNNING" %s &&' % shell + self.data ['content']))

## Main

g = yaml.load_all (open ('ev.yaml'))  # , Loader=yaml.CLoader)

# g is a generator object, make list (then zip into a list of tuples)
docs = [d for d in g]
assert len (docs) % 2 == 0

# https://docs.python.org/3/library/functions.html#zip
#docs = zip(*[iter(l)]*2)
#docs = [i for i in zip(*[iter(g)]*2)] - nope - g is used up
docs = [i for i in zip (*[iter (docs)]*2)]

if trace:
    for d in docs:
        print (pformat (d))
    print ('LEN', len (docs))

for m,d in docs:
  Section (m, d).process()


'''
d - set up ~5 structs

- build keys subdir from keys/ subfolder, insert into dict manually before saving
  actions:
    save: .
    addkeys: ./keys/
  actions:
    save: ..
    do: sh


- mk .ev-work dir
- cd to it
- save all the files
- run make-new-vm or just cloud_localds

- mv the resultant vm, swap, and parms into the parent dir

- run/call evmanager spinup, but be sure to pass the cloudinit parms drive on 1st invocation!

I guess:
- evm create can make all the files and do cloud-localds
- evm spinup can just run parms.sh but with the extra parm(s) for the cloudinit HD
- evm start/stop is regular / normal

'''
