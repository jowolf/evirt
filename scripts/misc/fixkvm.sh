chown www-data:kvm /dev/net/tun 

exit 0


OTHER NOTES:

- prep kvm modules, both kvm and kvm-[amd,intel]

- add group kvm, set up www-data

- /etc/init.d/kvm (may be already set uyp by ubuntu)


From:  /etc/sudoers
...

# JJW 2/14/08 (VDay!) for libre website to access netstat, sh, etc - 
# also, don't forget to: chown www-data:kvm /dev/net/tun 
www-data ALL = NOPASSWD: /bin/netstat, /sbin/ifconfig, /usr/sbin/brctl, /usr/sbin/tunctl
# /var/www/cgi-bin/auth, /sbin/pfctl, /var/www/htdocs/pfw/bin/*
# no need for python, it's in apache's conf: /usr/local/bin/*



From: /etc/udev/rules.d/45-kvm.rules

KERNEL=="kvm", NAME="%k", GROUP="kvm", MODE="0660"
