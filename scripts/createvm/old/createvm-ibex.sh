mname=Unconfigured_Ibex_x86
#ip=142
mem=512
arch=i386
#dir=/vm/$ip/new
dir=new

#pw=`dd if=/dev/random bs=6 count=1 | base64`
pw=libre142857 #guest$ip

echo PASSWORD IS $pw
echo MAKE A NOTE OF IT
hname=`echo $mname | sed 's/_/-/g' | tr [:upper:] [:lower:]`

ubuntu-vm-builder kvm intrepid \
  --mem $mem -a $arch -d $dir \
  --rootsize 20480 \
  --domain librehost.com \
  --hostname $hname \
  --user sysadmin --name "Libre System Administrator" --pass $pw \
  --ssh-key /vm/scripts/createvm/id_rsa.pub \
  --components main,universe,medibuntu,partner,restricted \
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
  | tee createvm.log

#  --addpkg xubuntu-desktop \
#  --addpkg lzma \
#  --addpkg rar \

chown -R www-data:kvm $dir
mv createvm.log $dir/

echo PASSWORD IS $pw 
echo MAKE A NOTE OF IT
