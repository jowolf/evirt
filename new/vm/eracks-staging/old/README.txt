ev4 notes 

10/5/19 ofc

lose the nested yaml - config only
- set up env vars
- scripts or commands dir - default/ev4 and override in vm dir

build - exclude image setup / copy?

add bootfrom.sh or sysrescue.sh

...MOVED TO evirt4


10/4/19 Camino

- multipass NRFPT (and poorly named) - no networking, no docs, no config

- yaml-dir - see lgram/test - for basic dir-visible settings - 
    cpu, ram, disk, user, image, etc

- keys - either via files/, or pick up current user

- packages

- files - put in same place, save as same name sans 'files/'

- simple!

- firstboot/
  along with symlinks, etc

- rc.local (every boot)

- git repos (not really needed, put script in firstboot/)

- cloud-init basic template, but 

- commands/ but no .evirt (in addition to default commands)

- no more docker-compose - goes in repo init, if needed


