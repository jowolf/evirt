echo Reading parms...
. parms.sh

telnet="telnet 216.218.243.$ip 23$ip"


echo Syncing/Halting $mname via telnet/monitor...
# assumes text window, though or text mode
echo sendkey ctrl-c | $telnet
echo sendkey s-y-n-c-ret | $telnet
echo sendkey h-a-l-t-ret | $telnet
#echo sendkey alt-d-d | $telnet

echo waiting 5 seconds...
sleep 5

echo sending ctrl-alt-delete
echo sendkey ctrl-alt-delete | $telnet

echo waiting 5 seconds...
sleep 5

echo sending system-reset
echo system-reset | $telnet

echo Done with $0 $mname