# start.sh generated mm/dd/yy by eVirt
log=output.log
vmdir = vmname if vmname else basename (pwd)
daemon="daemon -D /vm/$vmdir/ -P /vm/ -n nextcloud $respawn -o $log -l $log --verbose -- "
command="$daemon kvm $parms $vnc $mon $net $hda"
