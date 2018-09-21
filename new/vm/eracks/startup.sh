# startup commands called by eVirt cloud-init script
# done once at initial boot, after cd $user and su $user

. env/bin/activate

touch DOING_GIT_CLONE
git clone https://github.com/jowolf/eracks11.git
touch DOING_BUILD
cd eracks11
cp ../docker-compose.yml .
cp ../docker-compose.yaml .
docker-compose up --build
touch DONE
