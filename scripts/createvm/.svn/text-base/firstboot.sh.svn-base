#!/bin/sh
#cd /root/
#mkdir scripts
#cd scripts
#wget scripts.osdf.com/install_start.sh >firstboot.log 2>firstboot.err

#sh install_start.sh >install_start.log 2>install_start.err
#sh localefix.sh  >localefix.log 2>localefix.log

# re-enable root? no longer necessary - could lock it, though!

echo >> /etc/sudoers.d/sudoers-jjw
echo "# allow root for sysadmin - JJW" >> /etc/sudoers.d/sudoers-jjw
echo "sysadmin ALL=(ALL)NOPASSWD: ALL" >> /etc/sudoers.d/sudoers-jjw

#cd /home/sysadmin
#svn co http://osdf.net/librepuppet/svn/chef brewpub
#cd brewpub
#bash bootstrap.sh &>bootstrap.log
