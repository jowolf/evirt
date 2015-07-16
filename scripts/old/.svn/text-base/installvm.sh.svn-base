# . newubu.sh $1 $2 $3 ?

#sleep 60

$ip=$1
$mname=$2

ssh 216.218.243.$ip <<EOF 2>&1 | tee -a $0.log

hostname $mname

wget scripts.osdf.com/bootstrap.sh

wget custom envo installer

add to rclocal

reboot

EOF
