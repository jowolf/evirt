# spinup scripts are run in the VM as (admin) user, from the user's home dir

send_telegram() {
  m="$(hostname -s)_$1"
  wget -O ~/$m "https://api.telegram.org/bot827690020:AAH4_YiCp9W5KEE1hxMMQfh1UXAG8D4ENoE/sendMessage?chat_id=116010224&text=$m"
}


echo keyscan to add github to known hosts to prevent ask
ssh-keyscan -H gitlab.com >>.ssh/known_hosts


echo "ensure correct perms & ownership of key files (need enh to cloudinit files!)"

echo sudo chmod 600 /home/joe/.ssh/id_rsa_eracks-deploy
sudo chmod 600 /home/joe/.ssh/id_rsa_eracks-deploy

echo sudo chown $user:$user /home/joe/.ssh/id_rsa_eracks-deploy
sudo chown $user:$user /home/joe/.ssh/id_rsa_eracks-deploy

#echo sudo chmod 600 /home/joe/.ssh/id_rsa_gitlab
#sudo chmod 600 /home/joe/.ssh/id_rsa_gitlab

#echo sudo chown $user:$user /home/joe/.ssh/id_rsa_gitlab
#sudo chown $user:$user /home/joe/.ssh/id_rsa_gitlab


echo Set up git identity

git config --global user.email "joe@eracks.com"
git config --global user.name "Joseph Wolff"


echo Clone private eracks repo

sudo -u joe ssh-agent bash <<EOF
ssh-add /home/joe/.ssh/id_rsa_eracks-deploy
git clone -q git@gitlab.com:jowolf/eracks12.git
#gitlab+deploy-token-103017
#ZyDT3sdLccoxBXHccyFV
EOF

# send progress notification via telegram
#wget "https://api.telegram.org/bot827690020:AAH4_YiCp9W5KEE1hxMMQfh1UXAG8D4ENoE/sendMessage?chat_id=116010224&text=staging_eracks12_is_installed!"
send_telegram is_installed!

echo set up virtual envo
set +x
cd /home/joe/eracks12
./setup-venv.sh
. env/bin/activate
cd deploy
./deploy.sh
./setup-web-compose.sh
./restart.sh

# send progress notification via telegram
send_telegram is_up!

exit


# later 10/5/19:


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

