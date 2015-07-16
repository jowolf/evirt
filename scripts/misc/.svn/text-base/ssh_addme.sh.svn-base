#!/usr/bin/env python
import pexpect
import getpass

def ssh_command (user, host, password, command):
    """This runs a command on the remote host. This returns a
    pexpect.spawn object. This handles the case when you try
    to connect to a new host and ssh asks you if you want to
    accept the public key fingerprint and continue connecting.
    """
    ssh_newkey = 'Are you sure you want to continue connecting'
    child = pexpect.spawn('ssh -l %s %s %s'%(user, host, command))
    i = child.expect([pexpect.TIMEOUT, ssh_newkey, 'password: '])
    if i == 0: # Timeout
        print 'ERROR!'
        print 'SSH could not login. Here is what SSH said:'
        print child.before, child.after
        return None
    if i == 1: # SSH does not have the public key. Just accept it.
        child.sendline ('yes')
        #child.expect ('password: ')
        i = child.expect([pexpect.TIMEOUT, 'password: '])
        if i == 0: # Timeout
            print 'ERROR!'
            print 'SSH could not login. Here is what SSH said:'
            print child.before, child.after
            return None       
    child.sendline(password)
    return child

host = 'm155.librehost.com' #raw_input('Hostname: ')
user = 'sysadmin'           #raw_input('User: ')
password = getpass.getpass('Password: ')

id_rsa_pub='ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA3LLGEPMDbN91Ia5ue9dgXc0tvAMNxhbhSPatVTkdVxjdUPEXlyi763G5IKg5amp+UwUuXm+PRCgoXCY5qVdhgIIlE2QhNN6WhMXP1WO0nYHAeUuFuZVhj8f/MAtweMTQcvst6xO0Q1ned4e1/C1Vxgk3K4DNkjvmmZKCVLhQq3yVugURMKoRaUbylcTSd644sv4s0uHCvgwoqeo1mbs6B78tt8l9NgcRMCqHbS6Fr9FeOPOBh2AM74M4GbOTmDNsPlIKTU1QbuUWTtZhl+PyJ9s7f7YCARczz2T1zqeW9TX+g6LUcvliDcXvAPctpLQtDR0saFlrvv43ZLGnp0JO2Q== root_and_joe@ubuntustudio'

child = ssh_command (user, host, password, "mkdir .ssh; echo '%s' >>.ssh/authorized_keys" % id_rsa_pub)
child.expect(pexpect.EOF)
print child.before
