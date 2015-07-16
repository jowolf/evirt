# kvm_utils.config - copyright (c) 2007-2010 Joseph J Wolff, all rights reserved
#
# Config getter / setter utilities:
#
# Untended at some point to support:
# - bash shell "source" (aka .) format
# - yaml
# - "ini" format
# - python (similar to shell) syntax
#
# This is a starter module, for now, for kvm_utils and bash source only
# YAML read (no write) added 4/16/10 JJW


from os.path import join, exists, splitext
from string import Template
from ConfigParser import ConfigParser

# not yet used:
try: import yaml
except: yaml = False


trace = 0

def _subst (s, d):
  return Template (s).safe_substitute (d)

class Result:
    def __init__ (self, dct={}):
        self.__dict__.update (dct)


class Config (object):
    #def __init__ (self, path=my_path, fname='parms.sh'):  # could do polymorph on filetype, .sh, .yaml, etc
    def __init__ (self, path, fname='parms.sh'):  # could do polymorph on filetype, .sh, .yaml, etc
        self.path = path
        self.fname = fname
        self.fullname = join (self.path, self.fname)

    def get (self):
        if trace: print 'Config.get:', self.fullname
        if not exists (self.fullname): return {}
        f = file (self.fullname)
        ext = splitext (self.fname) [1].lower()

        if yaml and ext in ('yml', 'yaml'):
            try:
                result = yaml.safe_load (f)
                if trace: print 'Yaml result:', result
                if result: return result
            except Exception, e:
                if trace: print e  # drop thru, it's not a yaml file
                f.seek (0)

        lines = f.readlines()
        f.close()
        result = {}

        for line in [l.strip() for l in lines if l if l.strip() if l.strip() [0] != '#']:
            toks = line.split('=', 1)
            if len (toks) == 2:   # OK
                k,v = toks
                k = k.strip()
                v =  _subst (v, result)  # allow nested references, in order
                if v.isdigit(): v = int (v)
                result [k] = v

        if trace: print 'Config result:', result
        return result


    def _getlines (self):
        if not exists (self.fullname): return []
        f = file (self.fullname)
        lines = f.readlines()
        f.close()
        return [l.strip() for l in lines if l if l.strip()]


    def set (self, **kw):  # do we really need args={}? can just do c.set (**args) in that case
        if trace: print 'Config.set:', self.f, `kw`

        lines = self._getlines()
        f = file (self.fullname, "w")
        dups = []

        for line in lines:
            if line [0] == '#':  # preserve comments
                f.write (line + '\n')
            else:
                toks = line.split('=', 1)
                if len (toks) == 2:   # OK
                    k = toks [0].strip()
                    if k in kw:
                        f.write ( ('%s=%s' % (k, kw.pop (k))) + '\n')
                        dups += [k]
                    elif not k in dups:
                        f.write (line + '\n')

        # add new ones at end
        for k,v in kw.items():
            f.write ( ('%s=%s' % (k,v)) + '\n')

        f.close()



# old: 
def get_ini (path, section='kvm', fname='.meta'):
  config = ConfigParser.ConfigParser()
  config.read (join (path, fname))
  if trace:
    print config.sections()
    for section in config.sections():
      print config.items (section)
  if config.sections():
    #config.close()
    return dict (config.items(section))

def set_ini (path, args={}, section='kvm', fname='.meta', **kw):
  config = ConfigParser.ConfigParser()
  if trace: print 'in set:', section, kw
  config.add_section (section)
  for k,v in args.iteritems(): config.set (section, k,v)
  for k,v in kw.iteritems(): config.set (section, k,v)
  f = file (join (path, fname), 'w')
  config.write (f)
  f.close()


# could instantiate settings object here..
#    path = os.path.dirname (os.path.abspath (__file__))
#    settings = Result (Config (path, 'settings.yml').get())


if __name__ == '__main__':
  print "KVM Libre Hosting kvm_utils.config module - (c)2007-2010 Joseph J Wolff & The Libre Group, all rights reserved"

  
  c = Config ('.', 'test.sh')
  c.set (kvm='kvmaha', this='is', a='test', of='the', emergency='broadcast system')
  #set (this='is', a='test', of='the', emergency='broadcast system')

  print c.get()
