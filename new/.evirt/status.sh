# status.sh generated 2018-06-06 by eVirt
echo Daemon log:
echo
tail daemon.log
echo
echo eVirt log:
echo
tail evirt.log
echo
echo sudo ps -axw | grep nextcloud
sudo ps -axw | grep nextcloud
