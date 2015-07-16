echo Reading parms...
. parms.sh

telnet="telnet 216.218.243.$ip 23$ip"


echo Halting $mname via telnet/monitor...
#echo sendkey ctrl-u | $telnet
#echo sendkey h-a-l-t-ret | $telnet
#echo sendkey alt-d-d | $telnet
echo sendkey ctrl-alt-delete | $telnet
echo system-reset | $telnet

echo waiting 5 seconds...
sleep 5

echo Done with $0 $mname