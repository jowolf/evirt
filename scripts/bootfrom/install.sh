echo Reading parms...
. parms.sh

echo Checking for hds...

if ! [[ -e $hda ]]; then
  echo hda not present, creating: $hda
  qemu-img create -f qcow2 $hda 25G
else
  echo hda is present: $hda
fi

if ! [[ -e $mname.swap ]]; then
  echo swap not present, creating: $mname.swap
  qemu-img create -f qcow2 $mname.swap 2G
else
  echo swap is present: $mname.swap
fi

boot=d

. start.sh
