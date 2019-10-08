# salt-minion cloud-init spinup script
# includes github keyscan

# spinup scripts are run as (admin) user, from the user's home dir

# keyscan to add github to known hosts to prevent ask
ssh-keyscan -H github.com >>.ssh/known_hosts

wget https://bootstrap.saltstack.com -O bootstrap-salt.sh
sudo sh bootstrap-salt.sh -UPA desqhost.com -i $host

