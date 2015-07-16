"""
Created on 11/4/2009 by Mark Barfield

It is licensed under the Apache License, Version 2.0
(http://www.apache.org/licenses/LICENSE-2.0.html).

Downloaded from http://code.google.com/p/jsonrpclib/issues/detail?id=5
Apr/May 2010 JJW

Mods by JJW
"""

from jsonrpclib import SimpleJSONRPCServer
#import SimpleJSONRPCServer
import BaseHTTPServer
import SocketServer
import sys
import socket
import ssl

# JJW
import hashlib
import settings
from utils.auth import token_auth

class SecureJSONRPCRequestHandler(SimpleJSONRPCServer.SimpleJSONRPCRequestHandler):
    """Secure JSON-RPC Request handler class

    Idea copied from http://code.activestate.com/recipes/496786/ but made
    to work with JSON-RPC instead of XML-RPC
    """
    rpc_paths = ('/', '/RPC2', '/json')

    def setup(self):
        """Setup the connection."""
        self.connection = self.request
        #print 'SETUP', self.connection
        self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
        self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)
        #print 'AFTER', self.rfile, self.wfile

    def report_4xx (self, code):  # JJW
        # Report a 400 (4xx) error
        print 'REPORT:', code
        self.send_response(code)
        response = BaseHTTPServer.BaseHTTPRequestHandler.responses [code] [0]
        self.send_header("Content-type", "text/plain")
        self.send_header("Content-length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)
        # shut down the connection
        self.wfile.flush()
        self.connection.shutdown(0)

    def report_404 (self, code):  # overrride report_404, for connection.shutdown 0 - JJW
        return self.report_4xx (404)

    def do_POST(self):
        """Handle a POST."""
        #print 'POST'
        if not 'X-evirt-Auth-Token' in self.headers:
            return self.report_4xx (401)

        if token_auth.verify_token (self.headers ['X-evirt-Auth-Token']):  # TODO: pass caller IP here
            return self.report_4xx (403)

        SimpleJSONRPCServer.SimpleJSONRPCRequestHandler.do_POST(self)
        self.connection.shutdown(0)  # why shutdown 0 here? it's the only diff btw super - JJW


class SecureJSONRPCServer(BaseHTTPServer.HTTPServer, SimpleJSONRPCServer.SimpleJSONRPCDispatcher):
    """Secure JSON-RPC server.
    Idea copied from http://code.activestate.com/recipes/496786/ but made
    to work with JSON-RPC instead of XML-RPC
    """
    def __init__(self, addr, requestHandler=SecureJSONRPCRequestHandler,
            logRequests=True, certFile=None, keyFile=None,
            cert_reqs=ssl.CERT_NONE, ssl_protocol=ssl.PROTOCOL_SSLv23):
            #cert_reqs=ssl.CERT_REQUIRED, ssl_protocol=ssl.PROTOCOL_SSLv23):
        """Initialize this class and its base classes."""
        self.logRequests = logRequests

        SimpleJSONRPCServer.SimpleJSONRPCDispatcher.__init__(self)
        SocketServer.BaseServer.__init__(self, addr, requestHandler)

        sock = socket.socket(self.address_family, self.socket_type)
        #print 'BEFORE',self.address_family, self.socket_type, sock
        self.socket = ssl.wrap_socket(sock,
                keyfile=keyFile,
                certfile=certFile,
                server_side=True,
                cert_reqs=cert_reqs,
                ca_certs=keyFile,
                ssl_version=ssl_protocol)
        #print 'AFTER', self.socket
        self.server_bind()
        self.server_activate()
        #print 'AFTER ACTIVATE', self.server_name, self.server_port

    uncomment_for_debug='''
    def serve_forever(self, poll_interval=0.5):
        import select
        """Handle one request at a time until shutdown.

        Polls for shutdown every poll_interval seconds. Ignores
        self.timeout. If you need to do periodic tasks, do them in
        another thread.
        """
        self.__serving = True
        #self.__is_shut_down.clear()
        while self.__serving:
            # XXX: Consider using another file descriptor or
            # connecting to the socket to wake this up instead of
            # polling. Polling reduces our responsiveness to a
            # shutdown request and wastes cpu at all other times.
            r, w, e = select.select([self], [], [], poll_interval)
            print 'SERVE', r,w,e
            if r:
                self._handle_request_noblock()
        #self.__is_shut_down.set()
    '''


if __name__ == '__main__':
    print 'Running Secure JSON-RPC server on port 8000'
    server = SecureJSONRPCServer(("localhost", 8000), certFile='cert.pem')
    server.register_function(pow)
    server.register_function(lambda x,y: x+y, 'add')
    server.serve_forever()
