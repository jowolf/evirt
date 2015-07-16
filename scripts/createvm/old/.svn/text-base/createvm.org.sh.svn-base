mname=Django1_Test_x86
ip=142
mem=512
dir=/vm/$ip/new

#pw=`dd if=/dev/random bs=6 count=1 | base64`
pw=libreguest$ip

echo PASSWORD IS $pw
echo MAKE A NOTE OF IT
hname=`echo $mname | sed 's/_/-/g' | tr [:upper:] [:lower:]`

ubuntu-vm-builder kvm hardy \
  --mem $mem -a i386 -d $dir \
  --rootsize 20480 \
  --domain $ip.librehost.com \
  --hostname $hname \
  --user sysadmin --name "Libre System Administrator" --pass $pw \
  --ssh-key /vm/scripts/createvm/id_rsa.pub \
  --components main,universe,medibuntu,partner \
  --addpkg mc \
  --addpkg curl \
  --addpkg wget \
  --addpkg mc \
  --addpkg rsync \
  --addpkg rzip \
  --addpkg p7zip-full \
  --addpkg zip \
  --addpkg lynx \
  --addpkg man-db \
  --addpkg locate \
  --exec "/vm/scripts/createvm/inguest.sh" \
  | tee createvm.log

#  --addpkg xubuntu-desktop \
#  --addpkg lzma \
#  --addpkg rar \

chown -R www-data:kvm $dir
mv createvm.log $dir/

echo PASSWORD IS $pw 
echo MAKE A NOTE OF IT

