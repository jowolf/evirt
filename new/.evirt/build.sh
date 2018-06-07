# copy or download image & save as nextcloud.img
if ( ls -l nextcloud.img ); then
  echo IMAGE PRESENT - NOT DOWNLOADING!
else
  wget -O nextcloud.img https://cloud-images.ubuntu.com/releases/18.04/release/ubuntu-18.04-server-cloudimg-amd64.img
  # copy from image location:
  #cp `basename https://cloud-images.ubuntu.com/releases/18.04/release/ubuntu-18.04-server-cloudimg-amd64.img` nextcloud.img
fi

qemu-img resize nextcloud.img 20G

cloud-localds cloudinit.img userdata.yaml metadata.yaml
