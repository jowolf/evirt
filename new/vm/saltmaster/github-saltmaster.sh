# salt-master cloud-init spinup script
# includes github keyscan, jjw salt deployment key, symlink into place, auto-key accept

# spinup scripts are run as (admin) user, from the user's home dir

# keyscan to add github to known hosts to prevent ask
ssh-keyscan -H github.com >>.ssh/known_hosts

echo sudo chmod 600 $git_repo_key
sudo chmod 600 $git_repo_key

echo sudo chown $user:$user $git_repo_key
sudo chown $user:$user $git_repo_key

sudo -u joe ssh-agent bash <<EOF
ssh-add /home/joe/.ssh/id_rsa_jjw-salt-deploy
git clone -q git@github.com:jowolf/jjw-salt-master.git
EOF

sudo rmdir /srv
sudo ln -sf ~/jjw-salt-master /srv

wget https://bootstrap.saltstack.com -O bootstrap-salt.sh
sudo sh bootstrap-salt.sh -UPMA desqhost.com -i saltmaster

date
echo sleep 360
sleep 360
date

sudo salt-key -Ay
sudo salt -v "*" test.ping

