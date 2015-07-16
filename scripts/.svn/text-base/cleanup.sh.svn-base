if ! [[ $EUID -eq 0 ]]; then
  echo "This script ($0) must be run as root "
  exit 0
fi

echo Normalizing directory...
if ! [[ -e output.log ]]; then touch output.log; fi
if ! [[ -e output.bak ]]; then touch output.bak; fi
chmod +w output.log
chmod +w output.bak
chmod g+w output.log
chmod g+w output.bak
chown :kvm output.log
chown :kvm output.bak
chmod g+w .

# should really use the settings, here, for vm_path
chmod g+w ..

# should really read the parms, here
chmod g+w *.qcow2
chmod g+w parms.sh

rm *.png
rm *.ppm

if [[ -L start.sh ]]; then rm start.sh; fi
if [[ -L restart.sh ]]; then rm restart.sh; fi
if [[ -L status.sh ]]; then rm status.sh; fi
if [[ -L stop.sh ]]; then rm stop.sh; fi

