. parms.sh

#rslt=
#set -m 
#eval daemon --running --verbose -n $mname

echo PWD: `pwd`
echo MNAME: $mname

echo Running: "daemon --running --verbose -n $mname -P /vm/"
daemon --running --verbose -n $mname -P /vm/
rslt=$?
echo rslt: $rslt

echo
echo Recent output:
tail output.log

exit $rslt