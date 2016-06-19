# JJW Dec 2015 - copy image fm salt cache
#
# JJW Jan 5 2016 - quote pw literal, has $ in it (!)
#
# JJW Nov 2015 - create new VM from:
# - IP addr last tumbler (defaults to current dir basename)
# - hostname
# - size
#
# using templates from metadata.yaml, useredata.yaml, and make-cloudinit.sh

image=/var/cache/salt/minion/extrn_files/base/cloud-images.ubuntu.com/releases/14.04/14.04.3/ubuntu-14.04-server-cloudimg-amd64-disk1.img
iplast=$(basename `pwd`)
host=tlg
size=50G

if ( ls -l $host.img ); then
  echo IMAGE PRESENT - WOULD OVERWRITE
  exit;
fi


cat >metadata.yaml <<EOF
instance-id: $host;
network-interfaces: |
  auto eth0
  iface eth0 inet static
    address 216.172.134.$iplast
    #network 216.172.134.0
    netmask 255.255.255.128
    #broadcast 216.172.134.255
    gateway 216.172.134.1
    dns-nameservers 72.13.81.2 72.13.91.2 8.8.8.8 4.2.2.1 4.2.2.2 4.2.2.3 
local-hostname: $host.eracks.com
EOF


cat >userdata.yaml <<EOF
#cloud-config
#hostname: myubuntuhost
groups:
  - joe: [joe]
users:
  - name: joe
    gecos: joe
    shell: /bin/bash
    primary-group: joe
    groups: [users, root, kvm, sudo, adm, audio, cdrom, dialout, floppy, video, plugdev, dip, netdev]
    lock-passwd: false
    passwd: '$6$rounds=4096$9HeOrRyXEKcTYA5h$mjWahfdV6X.lIiyDwRc/6hXv.7UJCH55XZbHgOOTG3yRh/3vOg5iEukKwYV8kURYtE.GuE/SGI0sUCSAqAgkS.'
    ssh-authorized-keys:
      - ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC+xUBBvQ7+5WiKLSsBUrIbqyecadH+FFSJzrvA43hxM+z1LP5G0CnMHFVIYF68b58rzPvWurYshCRwOf6Z0ZOc0IAqyOxRQeIG6hphT5TfL+gB+h/BJ+YaWxNR0s7EJYr/2hWUP0j1xJ6EFt1EUH9p5vi4tRo1NcX7syxQUmedtkLrOgM7p5wAbcNGkjog8SmMyHyMZD5yQPt7kbkz2qUmZzf2CNR4aUZEoJnvyLoXDrz1OxZPklcjeXVUH7w91WKPIrTm+lt4xOn0XuCqmHzIlNixyHTBOrdoDuRbejhn/UOFswb3YFRMLczK6f3N+UqqpV9PAErK9QGOAyEjLRHZ root@mintstudio-maya
    sudo: ALL=(ALL) NOPASSWD:ALL
package_upgrade: true
packages:
  - mc
  - python-pip
  - unp
runcmd:
  - "curl -L https://bootstrap.saltstack.com -o install_salt.sh"
  - "sudo sh install_salt.sh -U -P -A desqhost.com -i $host.eracks.com"
EOF

cat >parms.sh <<EOF
mname=$host
hda=$host.img
hdb=cloudinit.img
ip=$iplast
m=1536
daemon=1
permanent=1
parms="-spice port=$((33000+$iplast)),password=meatballs"
EOF

# copy from image location:
cp $image $host.img

qemu-img resize $host.img $size

cloud-localds cloudinit.img userdata.yaml metadata.yaml

