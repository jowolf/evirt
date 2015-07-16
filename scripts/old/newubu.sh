# newubu.sh - vmnew.sh - copy a VM (created with createvm) using Joe's vHosting framework for KVM, etc
# copyright (c) 2007-8 Joseph J Wolff

#sudo -u www-data -s <<EOF
#su www-data <<EOF

# TODO: parm for swap, other partitions?


usage() {
 echo
 echo "Usage: bash $0 ip mname createvm/template_dir [ram]"
 echo Notes:
 echo "  Should be run from the /vm/scripts dir to ease createvm/ tab-completion"
 echo "  ip can also be a (unique!) port address, such as 3390, for RDP-accessed outgoing-only VMs"
 echo "  mname should not contain spaces - use underscores, they will be displayed as spaces"
 echo "  template_dir is the subdir of createvm/ containing the root.qcow2 file"
 echo "  arch is i386 (default) or amd64"
 echo "  ram is in MB (default 256)"
 echo
 echo parms: $1 $2 $3 $4
 exit 1
}

ip=$1
mname=$2
dir=$3

if [[ $4 ]]; then ram=$4; else ram=256; fi

cdpth=/iso/ubuntu-8.04-dvd-i386.iso
cdnam=`basename $cdpth`

echo
echo Destination: /vm/$ip
echo vMachine Name: $mname
echo Template dir: $dir
echo CD/DVD image path: $cdpth
echo cdrom link: $cdnam
echo Ram: $ram
echo

if ! [[ $ip ]]; then
 echo IP not specified
 usage
elif ! [[ -e $cdpth ]]; then
 echo CD/DVD image not present
 usage
elif ! [[ $mname ]]; then
 echo vMachine Name must be specified
 usage
elif [[ -e /vm/$ip ]]; then
 echo /vm/$ip already exists - aborted
 usage
elif ! [[ $dir ]]; then
 echo "directory containing root.qcow2 must be specified - createvm/<etc>"
 usage
elif ! [[ -d $dir ]]; then
 echo "template doesn't exist: $dir"
 usage
fi

echo Creating directory and copying template files...
#rsync -av /vm/templates/new /vm/$ip
su www-data -c "mkdir /vm/$ip"
cp -dpi /vm/templates/newubu/* /vm/$ip/
cp -dpi /vm/scripts/$dir/root.qcow2 /vm/$ip/
chown -R www-data:kvm /vm/$ip
cd /vm/$ip

echo Renaming Image...
mv root.qcow2 $mname.qc2

echo Tailoring parms template...
sed -i s/{{ip}}/$ip/ 	parms.sh
sed -i s/{{mname}}/$mname/ parms.sh
sed -i s/{{cdrom}}/$cdnam/ parms.sh
sed -i s/{{ram}}/$ram/ parms.sh

echo Creating symlinks...
ln -s $cdpth $cdnam

echo Setting permissions...
chown www-data:kvm *

echo Starting vm...
bash start.sh

echo Done.