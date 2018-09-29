# startup commands called by eVirt cloud-init script
# done once at initial boot, after cd $user and su $user

#touch 10_SETUP_AND_MOUNT_VOLUMES
#sudo sh -c "mkdir /volumes >> 10_SETUP_AND_MOUNT_VOLUMES 2>&1"
#ls -l / >> 10_SETUP_AND_MOUNT_VOLUMES 2>&1
#sudo sh -c "chown 1000:1000 /volumes >> 10_SETUP_AND_MOUNT_VOLUMES 2>&1"
#ls -l / >> 10_SETUP_AND_MOUNT_VOLUMES 2>&1
#sudo sh -c "mount -t 9p -o trans=virtio,version=9p2000.L hostshare0 /volumes >> 10_SETUP_AND_MOUNT_VOLUMES 2>&1"
#ls -l / >> 10_SETUP_AND_MOUNT_VOLUMES 2>&1
#echo DONE >> 10_SETUP_AND_MOUNT_VOLUMES

. env/bin/activate

#touch 11_SETUP_GIT_REPO_AND_VOLUMES
#git clone https://github.com/mattermost/mattermost-docker.git
#cp docker-compose.yml mattermost-docker/
#cd mattermost-docker/
##mkdir -p ./volumes/app/mattermost/{data,logs,config,plugins}
#mkdir -p /volumes/app/mattermost/{data,logs,config,plugins}
#chown -R 1000:1000 /volumes/app/mattermost/
#echo DONE >> 11_SETUP_GIT_REPO_AND_VOLUMES

touch 12_ADDING_JOE_TO_DOCKER_GROUP
sudo adduser joe docker >> 12_ADDING_JOE_TO_DOCKER_GROUP 2>&1
echo DONE >> 12_ADDING_JOE_TO_DOCKER_GROUP

touch 13_SETTING_UP_RC_LOCAL
sudo sh -c 'cat >/etc/rc.local' <<EOF
hostmounts.sh >> /RC_LOCAL_OUTPUT
hostmounts.sh >> RC_LOCAL_OUTPUT
sudo -u joe sh -c "cd /home/joe && . env/bin/activate && cd mattermost-docker && docker-compose up --build"
EOF
chmod +x /etc/rc.local
echo DONE >> 13_SETTING_UP_RC_LOCAL

touch REBOOTING
sudo reboot

