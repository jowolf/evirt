#! /bin/bash

sudo apt install 	\
    virtualenv 		\
    qemu-kvm 		\
    qemu-utils 		\
    spice-client-gtk 	\
    spice-html5 	\
    rdesktop		\
    vinagre		\
    libguestfs-tools	\
    cloud-image-utils	\

# NFG for 16.04:
#    remmina-plugin-spice \

# Also other rdp clients
# Also other vnc clients - xtightvncviewer, xvnc4viewer
# Also other remmina plugins
# Also sudo apt install qemuctl # for qt4 GUI

sudo adduser joe kvm

if ! test -d env; then {
  virtualenv --python=python3 env/
  env/bin/pip install -r requirements.txt
} fi


#sudo ln -sf $(pwd)/ev.py /usr/local/bin/evm

#echo "#! $(pwd)/env/bin/python $(pwd)/ev.py" >evm

echo -e "#! /bin/bash\n\n$(pwd)/env/bin/python $(pwd)/ev.py \$@" >evm
chmod +x evm
sudo ln -sf $(pwd)/evm /usr/local/bin/evm

echo -e "#! /bin/bash\n\n$(pwd)/env/bin/python $(pwd)/stuffit.py \$@" >stuffit
chmod +x stuffit
sudo ln -sf $(pwd)/stuffit /usr/local/bin/stuffit

sudo ln -s $(pwd)/vm /home/vm

echo DONE - REBOOT REQUIRED FOR /dev/kvm ACCESS FIRST TIME

sudo stuffit . env/bin/activate
