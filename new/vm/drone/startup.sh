# startup commands called by eVirt cloud-init script
# done once at initial boot, after cd $user and su $user

. env/bin/activate

touch 12_ADDING_JOE_TO_DOCKER_GROUP
sudo adduser joe docker >> 12_ADDING_JOE_TO_DOCKER_GROUP 2>&1
echo DONE >> 12_ADDING_JOE_TO_DOCKER_GROUP


touch 13_SETTING_UP_RC_LOCAL
sudo sh -c 'cat >/etc/rc.local' <<EOF 2>&1
#!/bin/bash

hostmounts.sh >> RC_LOCAL_OUTPUT
sudo -u joe sh -c "cd /home/joe && . env/bin/activate && docker-compose up --build" 
EOF

sudo chmod +x /etc/rc.local

echo DONE >> 13_SETTING_UP_RC_LOCAL


touch REBOOTING
sudo reboot

