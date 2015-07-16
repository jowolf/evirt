# evm_utils - copyright (c) 2007-2010 Joseph J Wolff & The Libre Group, all rights reserved

### Re-exports:

from netstat import get_active_kvm_ports
from config import Config, Result

import settings

### trace, debug, and log functions

trace = 0 or settings.trace


def trace_import (modulename):  # pass in __name__
    import os
    from inspect import stack

    print 'Importing: %s (in pid %d)' % (modulename, os.getpid())
    #print '\n'.join ([str(o[1:]) for o in stack()])
    for f in stack():
        dummy, file, line, module, code, dummy = f
        #if trace: print f[1][25:], f[2], f[3], f[4][0].strip()
        #if file.startswith ('/usr/lib/python'):
        #  file = file [32:]
        #file = file [-30:]
        if code: code = '"%s"' % code[0].strip()
        print file, line, module, code


def log (*args, **kw):
    if not trace: return
    import sys, inspect, os, pprint
    stack = inspect.stack()
    try:
        pfx = 'in %s.%s.%s:' % (os.path.basename (stack [1][1]), stack [1][3], stack [1][2]) # file, func, line
        print >> sys.__stdout__, pfx, pprint.pformat (args)
        for k,v in kw:
            print >> sys.__stdout__, pfx, k.upper() + ':', pprint.pformat (v)
    finally:
        del stack


### Decorators

## decorator to mark function as auth required -
# not used as of 5/10, all traffic has private SSL option on WAN
def requires_auth (fn):
  fn.auth_required = True
  return fn


### Utility functions

def sh (command, **kw):
  from subprocess import Popen, call, STDOUT, PIPE
  # Simplest, returns return code, but doesn't return text results:
  #   return call (command, shell=True, **kw)
  # Also simple, returns the text results, but no return code:
  #   return Popen (command, shell=True, stderr=STDOUT, stdout=PIPE, **kw).communicate()[0]
  # If you want both the test resutls and the return code:
  p = Popen (command, shell=True, stderr=STDOUT, stdout=PIPE, **kw)
  return (p.communicate()[0], p.returncode)


# Not a full slugify, just spaces:

def spacify (s):
  return s.replace ('_', ' ')

def unspacify (s):
  return s.replace (' ', '_')


# for determining mid (Machine ID) from port, after using netstat
def ports2mid (ports):
    mon = rdp = vnc = ser = ip = 0

    for p in ports:
        if p in settings.monRange: mon = p
        if p in settings.rdpRange: rdp = p
        if p in settings.vncRange: vnc = p

        if p in settings.monHighRange: ip = p % 1000
        if p in settings.rdpHighRange: ip = p % 1000
        if p in settings.vncHighRange: ip = p % 1000
        if p in settings.serialRange: ip = p % 1000

    if ip: return `ip`
    if rdp: return `rdp`
    if vnc: return `vnc`
    if ser: return `ser`


# Not used; largely dupped below in addArgs
def _zipDicts (d1, d2):  # combine the 2 dicts, assert they're the same
  for i in d1.keys():
    if i in d2: assert d2 [i] == d1 [i]
    else: d2 [i] = d1 [i]
  return d2


def addArgs (o, args, check=True):  # ensures args are attrs of object o
  #if trace: print 'addArgs:', check, `args`
  if args:
    od = o.__dict__
    od ['args'] = args
    for k,v in args.iteritems():
      if check and k in od:     # check: if it's already there, be sure it matches
        ov = od [k]
        assert str (ov) == str (v)
      else: od [k] = v


### Utility Classes - not used at the moment

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

