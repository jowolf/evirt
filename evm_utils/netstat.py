# netstat.py (C) 2008-2010 Joseph J Wolff and The Libre Group, All Rights Reserved
#
# Replacement for the netstat cmd that reads the "/proc" tree directly, and does not require root privileges

import os, re

socket_regex = re.compile ('^socket:\[(.*)\]$')

trace = 0

def get_active_kvm_ports():

  pids = {}
  inodes = {}

  for pid in [d for d in os.listdir ('/proc/') if d.isdigit()]:
    try:
      nam = os.readlink ('/proc/%s/exe' % pid)
      if not nam.endswith ('kvm') and not nam.endswith ('qemu-system-x86_64'):
        continue
    except:
      continue

    proc_d = '/proc/%s/fd/' % pid
    if trace: print proc_d
    pids [pid] = []
    for f in os.listdir (proc_d):
      try:
        match = socket_regex.match (os.readlink (proc_d + f))
        if match:
          inode = match.group(1)
          pids [pid] += [inode]
          inodes [inode] = pid
      except e:
        if trace: print 'Exception:', e

  if trace: print pids
  if trace: print inodes

  ports = {}
  f = file('/proc/net/tcp')

  lines = f.readlines()
  header = lines [0].split()

  assert header [1] == 'local_address'
  assert header [11] == 'inode'

  for l in lines [1:]:
    toks = l.split()
    port = int (toks[1].split(':') [1],16)
    inode = toks [9]

    if inode in inodes:
      pid = inodes [inode]
      if pid in ports:
        ports [pid] += [port]
      else:
        ports [pid] = [port]

  if trace: print ports

  return ports


if __name__ == "__main__":
    #trace = 1
    print get_active_kvm_ports()