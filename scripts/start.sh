if [[ $EUID -ne 0 ]]; then
  echo Best to run this script under www-data - 
  echo ..or at least a non-root user with kvm group permissions.
  exit 0
fi

echo Reading params...
. parms.sh

if [[ $1 ]]; then
  echo Evaluating params: $1
  eval $1
fi

echo Normalizing params...

if [[ $ip ]]; then
  if ! [[ $vncport ]]; then vncport=$((59000+$ip-5900)); fi
  macaddr=de:ad:be:ef:`printf '%02d:%02d' $(($ip / 100)) $(($ip % 100))`
  if ! [[ $mon ]]; then mon="-monitor telnet:127.0.0.1:$((23000+$ip)),server,nowait,nodelay"; fi
  if ! [[ $net ]]; then net="-net nic,macaddr=$macaddr -net tap,ifname=tap-$ip,script=no,downscript=no"; fi
  ln -s /vm/$ip /vm/$mname >& /dev/null
  ln -s /vm/$ip /vm/$ip/$mname >& /dev/null
  vmdir=$ip
elif [[ $rdpport ]]; then
  ln -s /vm/$rdpport /vm/$mname
  ln -s /vm/$rdpport /vm/$rdpport/$mname
  vmdir=$rdpport
elif [[ $vncport ]]; then
  ln -s /vm/$vncport /vm/$mname
  ln -s /vm/$vncport /vm/$vncport/$mname
  vmdir=$vncport
else
  echo Error: no ip, rdp, or vnc port!
  exit 1
fi

if ! [[ $vnc ]]; then
  if [[ $vncport ]]; then vnc="-vnc :$vncport"; fi
fi

if [[ $monport ]]; then mon="-monitor telnet:127.0.0.1:$monport,server,nowait,nodelay"; fi

if [[ $sandbox ]]; then snapshot=1; fi

if ! [[ $k ]];   then k=en-us; fi
parms="$parms -k $k"

if [[ $tablet ]];   then parms="$parms -usbdevice tablet"; fi
if [[ $snapshot ]]; then parms="$parms -snapshot"; fi
if [[ $boot ]];     then parms="$parms -boot $boot"; fi
if [[ $cdrom ]];    then parms="$parms -cdrom $cdrom"; fi
if [[ $hdb ]];      then parms="$parms -hdb $hdb"; fi
if [[ $hdc ]];      then parms="$parms -hdc $hdc"; fi
if [[ $hdd ]];      then parms="$parms -hdd $hdd"; fi
if [[ $m ]];        then parms="$parms -m $m"; fi


if [[ $respawn ]];  then respawn="-r"; fi

if [[ $daemon ]]; then 
 log=output.log
 daemon="daemon -D /vm/$vmdir/ -P /vm/ -n $mname $respawn -o $log -l $log --verbose -- "
fi

command="$daemon kvm $parms $vnc $mon $net $hda"

if [[ $ip ]]; then
  echo Removing placeholder ip br0:$ip..
  sudo ifconfig br0:$ip down
  echo Pre-adding tap-$ip
  echo sudo tunctl -u `whoami` -g kvm -t tap-$ip
  sudo tunctl -u `whoami` -g kvm -t tap-$ip
  echo sudo ifconfig tap-$ip up
  sudo ifconfig tap-$ip up
  echo sudo brctl addif br0 tap-$ip
  sudo brctl addif br0 tap-$ip
fi

rm -f output.bak
mv output.log output.bak
echo Started `date` > output.log
echo Running as user `id` >> output.log
echo >> output.log
echo Running: $command
echo Running: $command >> output.log
$command

#if [[ $sandbox ]]; then
#  bash sentry.sh
#  #echo Starting sandbox sentry...
#  #sh -c "sleep 60; daemon --restart -D /vm/$vmdir/ -n $mname" && echo Restarted: `date` >>output.log & echo Done starting sandbox sentry process.
#fi
