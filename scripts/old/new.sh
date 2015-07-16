# vmnew.sh - create a new VM using Joe's vHosting framework for KVM, etc copyright (c) 2007-8 Joseph J Wolff

#sudo -u www-data -s <<EOF
#su www-data <<EOF

usage() {
 echo
 echo "Usage: new.sh ip cdrompath mname [ram] [hd]"
 echo notes:
 echo "  ip can be a (unique!) port address, such as 3390"
 echo "  cdrompath is the absolute path"
 echo "  mname should not contain spaces - use underscores, they will be displayed as spaces"
 echo "  ram is in MB (default 256), hd is in GB (default 25)"
 echo
 echo parms: $1 $2 $3
 exit 1
}

ip=$1
cdpth=$2
cdnam=`basename $cdpth`
mname=$3
hda=$3.qc2
if [[ $4 ]]; then ram=$4; else ram="256"; fi
if [[ $5 ]]; then hd=$5;  else hd="25"; fi

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
fi

echo
echo Destination: /vm/$ip
echo vMachine Name: $mname
echo CD/DVD image path: $cdpth
echo cdrom link: $cdnam
echo ram: $ram
echo hd: $hd
echo

#exit 0

echo Creating directory and copying template files...
#rsync -av /vm/templates/new /vm/$ip
su www-data -c "mkdir /vm/$ip"
cp -dpi /vm/templates/new/* /vm/$ip/
cd /vm/$ip

echo Tailoring parms template...
sed -i s/{{ip}}/$ip/ 	parms.sh
sed -i s/{{mname}}/$mname/ parms.sh
sed -i s/{{cdrom}}/$cdnam/ parms.sh
sed -i s/{{ram}}/$ram/ parms.sh

echo Creating symlinks...
ln -s $cdpth $cdnam

echo Creating HD Images...
echo creating: $hda
qemu-img create -f qcow2 $hda ${hd}G
#echo creating: $mname.swap
#qemu-img create -f qcow2 $mname.swap 2G

echo Setting permissions...
chown www-data:kvm *

echo Done.