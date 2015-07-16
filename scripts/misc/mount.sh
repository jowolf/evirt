. parms.sh

mkdir /mnt/$mname
echo mount -t ext3 -w -o loop,offset=32256 /vm/$mname/$hda /mnt/$mname
mount -t ext3 -w -o loop,offset=32256 /vm/$mname/$hda /mnt/$mname
