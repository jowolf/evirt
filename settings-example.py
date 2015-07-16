# eVirt settings.py Copyright (c) 2010 Joseph J Wolff & The Libre Group, all rights reserved
#
# save a copy and customize to fit your local host or web controller

from os.path import dirname, join

project_root = dirname (__file__)

hosts = (
    #"https://localhost:8000",
    "https://localhost:16861/",  # trailing slash loses the '/RPC2'
    #"http://desqhost.com:16861",
    )

listen_host_port = ('localhost', 16861)

private_ssl = True   # True => use SSL & private, secure certs w/own CA
cert_file = join (project_root, 'cert.pem')

web_user = 'www-data'   # filesystem / linux user of web server process(es)
web_group = 'kvm'       # filesystem / linux group accessing /vm/* files

vmbase = '/vm'
imgbase = '/img'  # vm disk images, that is :)
isobase = '/iso'
flopbase = '/floppy'
#scriptbase = vmbase + '/scripts'
scriptbase = join (project_root, 'scripts')
#ipbase = '216.218.243.'
ipbase = '184.105.215.'

noimagelist = (
    '/images/noimage180.png',
    '/images/noimage400.png',
    '/images/noimage600.png',
    '/images/noimage640.png',
    )

images_url = '/images'              # retrieval url, from the client's perspective
images_root = '/var/www/images'     # filesystem location, from the server's perspective

trace = 0  # should we use a django-style DEBUG, too, or instead?


# could use a self-describing Ports class, here, with choices, etc

monBase     = 23000
rdpBase     = 33000
serialBase  = 43000
vncJavaBase = 58000
vncBase     = 59000

ipRange      = xrange (2, 255)
vncRange     = xrange (5900, 6000)
vncHighRange = xrange (vncBase, vncBase + 1000)
vncJavaRange = xrange (vncJavaBase, vncJavaBase + 1000)
rdpRange     = xrange (3389,  3489)
rdpHighRange = xrange (rdpBase, rdpBase + 1000)
monRange     = xrange (2300, 2400)
monHighRange = xrange (monBase, monBase + 1000)
serialRange  = xrange (serialBase, serialBase + 1000)

