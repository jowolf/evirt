# salt-master cloud-init spinup script
# includes github keyscan, docker-compose build, more

# spinup scripts are run as (admin) user, from the user's home dir

# keyscan to add github to known hosts to prevent ask
ssh-keyscan -H github.com >>.ssh/known_hosts


# ensure correct perms & ownership of key file (need enh to files!)

echo sudo chmod 600 /home/joe/.ssh/id_rsa_eracks-deploy
sudo chmod 600 /home/joe/.ssh/id_rsa_eracks-deploy

echo sudo chown $user:$user /home/joe/.ssh/id_rsa_eracks-deploy
sudo chown $user:$user /home/joe/.ssh/id_rsa_eracks-deploy


# Set up git identity

git config --global user.email "joe@eracks.com"
git config --global user.name "Joseph Wolff"


# Clone private eracks repo

sudo -u joe ssh-agent bash <<EOF
ssh-add /home/joe/.ssh/id_rsa_eracks-deploy
git clone -q git@github.com:jowolf/eracks11.git
EOF


# assumes docker-compose.sh spinup script before this one

. env/bin/activate


# Install into rc.local and reboot: build and run

sudo sh -c 'cat >/etc/rc.local' <<EOF
#!/bin/bash

hostmounts.sh >> RC_LOCAL_OUTPUT
#sudo -u joe sh -c "cd /home/joe && . env/bin/activate && cd eracks11/conf && docker-compose up --build"
#sudo -u joe --login sh -c ". env/bin/activate && cd eracks11/conf && docker-compose up --build -f docker-compose.yml -f docker-compose-$vmname.yml" >>RC_LOCAL_OUTPUT 2>&1
sudo -u joe --login sh -c ". env/bin/activate && cd eracks11/conf && docker-compose up --build" >>RC_LOCAL_OUTPUT 2>&1
EOF

sudo chmod +x /etc/rc.local

echo $0 DONE


touch REBOOTING
sudo reboot

