7/21/16 JJW
Partial password discrepancy between make-new-vm cloudinit parms, and what made it into the /etc/shadow file:

$6$rounds=4096$9HeOrRyXEKcTYA5h           .lIiyDwRc/6hXv.7UJCH55XZbHgOOTG3yRh/3vOg5iEukKwYV8kURYtE.GuE/SGI0sUCSAqAgkS.
$6$rounds=4096$9HeOrRyXEKcTYA5h$mjWahfdV6X.lIiyDwRc/6hXv.7UJCH55XZbHgOOTG3yRh/3vOg5iEukKwYV8kURYtE.GuE/SGI0sUCSAqAgkS.


Two more examples with the same benign password:

root@saltmaster:/etc# mkpasswd --method=SHA-512 --rounds=4096
Password:
$6$rounds=4096$j.Wuz8U9.imqzmb$pXz72iXzOBn7frmx4DPbLwMXWisz4hVTF9DKjm2yrRK6CyNdOtwErHKfJbKDPdzme5iafMBlqyqOJEIIsPhLv0

root@saltmaster:/etc# mkpasswd --method=SHA-512 --rounds=4096
Password:
$6$rounds=4096$wcwZ7OfN$Eml6aPnedcqA30dyCCVCqd9SjqPmIPDgr.SiDOCZTsqVBoiJdhfCAogB7tvUCH4RYgojoD5bYTD1lc9DPASM8.
