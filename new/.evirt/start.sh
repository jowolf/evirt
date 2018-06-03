# start.sh generated mm/dd/yy by eVirt
log=daemon.log
vmdir = vmname if vmname else basename (pwd)
daemon="daemon -D /vm/$vmdir/ -P /vm/ -n nextcloud $respawn -o $log -l $log --verbose -- "
command="$daemon kvm $parms -vnc :53115 -monitor telnet:127.0.0.1:23015,server,nowait,nodelay -net nic,macaddr=de:ad:be:ef:00:15 -net tap,ifname=tap-15,script=no,downscript=no $hda"
