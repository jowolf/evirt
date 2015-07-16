# evm_client.py Copyright (c) 2007-10 Joseph J Wolff, all rights reserved
#
## Client-related code, json-rpc server proxy, test client when run


#import sys, os
#from minitags import h1,h2,h3,div,islist

import jsonrpclib
import settings

from evm_utils import get_active_kvm_ports, addArgs, trace_import
from evm_monitor import Monitor
from evm_core import RemoteVM

trace = 0 or settings.trace

if trace: trace_import (__name__)

from xmlrpclib import ProtocolError

class SecureTransport (jsonrpclib.Transport):

    # Secure SSL - HTTPS only, py2.6 or later
    def make_connection (self, host):  # create a connection object from a host descriptor
        import httplib
        host, extra_headers, x509 = self.get_host_info(host)
        if trace: print 'HOST INFO:', host, extra_headers, x509
        x509 ['cert_file'] = settings.cert_file
        x509 ['key_file'] = settings.cert_file
        return httplib.HTTPS(host, None, **(x509 or {}))

    # Had to copy this fm xmlrpclib.Transport parent, to get at the request & response headers
    def no_request(self, host, handler, request_body, verbose=0):
        # issue XML-RPC request

        h = self.make_connection(host)
        if verbose:
            h.set_debuglevel(1)

        self.send_request(h, handler, request_body)
        self.send_host(h, host)
        h.putheader("X-evirt-Auth-Token", token_auth.next_token())  # JJW
        self.send_user_agent(h)
        self.send_content(h, request_body)

        errcode, errmsg, headers = h.getreply()

        if errcode != 200:
            raise ProtocolError(
                host + handler,
                errcode, errmsg,
                headers
                )

        if not token_auth.verify_token (headers.getheader ("X-evirt-Auth-Token")):
            raise Exception ('Security Error - invalid token')

        self.verbose = verbose

        try:
            sock = h._conn.sock
        except AttributeError:
            sock = None

        return self._parse_response(h.getfile(), sock)



import settings

if __name__ == "__main__":
    hosts = settings.hosts

    for host in hosts:
        try:
            if host.lower().startswith ('https'):  # should match settings.private_ssl on server:
                server = jsonrpclib.ServerProxy (host, transport=SecureTransport(), verbose=settings.trace)
            else:
                server = jsonrpclib.ServerProxy (host, verbose=settings.trace)

            print server, server.add (5, 6)
            print server, server.add (5123, 63465)
            #print server, server.sayHello ('Fred')

            vmlist = server.get_vm_list()
            #print 'SERVER VMLIST:', vmlist
            for vm in vmlist:
                #print vm
                vm = dict ([(str(k),v) for k,v in vm.items()])
                #print vm
                rvm = RemoteVM (server, **vm)
                print
                print rvm
                print 'Info block:'
                print rvm.monitor_command ('info block')
                print 'Screengrab:', rvm.screengrab()
                print 'Screengrab:', server.screengrab(rvm.mid)
                print 'ISOs', server.get_iso_images()
                print 'Disk images', server.get_disk_images()
                print 'Floppies', server.get_floppy_images()
                print 'Scripts', server.get_scripts()

        except Exception, e:
            print e, host
            #print jsonrpclib.history.request
              #{"jsonrpc": "2.0", "params": [5, 6], "id": "gb3c9g37", "method": "add"}
            #print jsonrpclib.history.response



