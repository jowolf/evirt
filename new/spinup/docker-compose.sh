# spinup script to set up compose-setup

# Assumes : sudo apt-get install python-virtualenv


virtualenv -v env
#./go.sh
. env/bin/activate
pip install docker-compose

# this one requires reboot to take effect
sudo adduser $user docker

