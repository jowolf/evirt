# spin up nextcloud instance

# spinup scripts are run as (admin) user, from the user's home dir


git clone -q https://github.com/nextcloud/docker.git


cp docker-compose.yml docker/.examples/docker-compose/with-nginx-proxy/mariadb-cron-redis/fpm/
cp db.env docker/.examples/docker-compose/with-nginx-proxy/mariadb-cron-redis/fpm/


# Install into rc.local and reboot: build and run

sudo sh -c 'cat >/etc/rc.local' <<EOF
#!/bin/bash

hostmounts.sh >> RC_LOCAL_OUTPUT
sudo -u joe --login sh -c ". env/bin/activate && cd docker/.examples/docker-compose/with-nginx-proxy/mariadb-cron-redis/fpm/ && docker-compose up --build" >>RC_LOCAL_OUTPUT 2>&1
EOF

sudo chmod +x /etc/rc.local

echo $0 DONE


touch REBOOTING
sudo reboot

