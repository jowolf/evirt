# stop.sh generated 2018-06-06 by eVirt
echo Stopping $mname daemon...
daemon --stop --verbose -n $mname -P /vm/

echo sudo brctl delif br0 tap-$ip
sudo brctl delif br0 tap-$ip
echo sudo ifconfig tap-$ip down
sudo ifconfig tap-$ip down
echo sudo tunctl -d tap-$ip
sudo tunctl -d tap-$ip

#echo Replacing pingable IP br0:$ip...
#sudo ifconfig br0:$ip 216.218.243.$ip netmask 255.255.255.255

echo Done with $0 $mname
