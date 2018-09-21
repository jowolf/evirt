# startup commands called by eVirt cloud-init script
# done once at initial boot, after cd $user and su $user

. env/bin/activate

touch SETUP_GIT_REPO_AND_VOLUMES
git clone https://github.com/mattermost/mattermost-docker.git
cp docker-compose.yml mattermost-docker/
cd mattermost-docker/
mkdir -p ./volumes/app/mattermost/{data,logs,config,plugins}
chown -R 1000:1000 ./volumes/app/mattermost/
echo DONE >> SETUP_GIT_REPO_AND_VOLUMES

touch ADDING_JOE_TO_DOCKER_GROUP
sudo adduser joe docker >> ADDING_JOE_TO_DOCKER_GROUP
echo DONE >> ADDING_JOE_TO_DOCKER_GROUP

touch SETTING_UP_RC_LOCAL
sudo sh -c 'cat >/etc/rc.local' <<EOF
sudo -u joe sh -c "cd /home/joe && . env/bin/activate && cd mattermost-docker && docker-compose up --build"
EOF
echo DONE >> SETTING_UP_RC_LOCAL

touch REBOOTING
sudo reboot

