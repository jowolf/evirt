if __name__ == '__main__':
  import os, sys
  sys.path.insert (0, '/home/joe/Projects/evirt')
  os.environ ['DJANGO_SETTINGS_MODULE'] = 'django_evirt.settings'

from jsonrpc import jsonrpc_method

@jsonrpc_method('myapp.sayHello')
def whats_the_time(request, name='Lester'):
  return "Hello %s" % name

@jsonrpc_method('myapp.gimmeThat', authenticated=True)
def something_special(request, secret_data):
  return {'sauce': ['authenticated', 'sauce']}


### OK let's try our own standalone Django server here:


if __name__ == '__main__':
  import ssl, socket, SocketServer
  from django.conf import settings
  from django.core.servers.basehttp import WSGIServer, WSGIRequestHandler, AdminMediaHandler, ServerHandler
  from django.core.handlers.wsgi import WSGIHandler

  class MyServerHandler (ServerHandler):
  #  pass
    def close(self):
        try:
            self.request_handler.log_request(self.status.split(' ',1)[0], self.bytes_sent)
        finally:
            try:
                if hasattr(self.result,'close'):
                    self.result.close()
            finally:
                #self.result = self.headers = self.status = self.environ = None
                #self.bytes_sent = 0;
                self.headers_sent = False

    def finish_response(self):
        """
        Send any iterable data, then close self and the iterable

        Subclasses intended for use in asynchronous servers will want to
        redefine this method, such that it sets up callbacks in the event loop
        to iterate over the data, and to call 'self.close()' once the response
        is finished.
        """
        if not self.result_is_file() or not self.sendfile():
            for data in self.result:
                self.write(data)
                print 'DATA', data
            self.finish_content()
        self.close()

    def send_headers(self):
        """Transmit headers to the client, via self._write()"""
        self.cleanup_headers()
        print 'SEND HEADERS', self.headers
        self.headers_sent = True
        if not self.origin_server or self.client_is_modern():
            self.send_preamble()
            self._write(str(self.headers))

    def set_content_length(self):
        """Compute Content-Length or switch to chunked encoding if possible"""
        try:
            blocks = len(self.result if isinstance (self.result, list) else [self.result])
        except (TypeError, AttributeError, NotImplementedError), e:
            print 'EXCEPTION', e
        else:
            if blocks==1:
                self.headers['Content-Length'] = str(self.bytes_sent)
                print 'CONTENT LENGTH', self.headers['Content-Length']
                return
        # XXX Try for chunked encoding if origin server and client is 1.1

    def cleanup_headers(self):
        """Make any necessary header changes or defaults

        Subclasses can extend this to add other defaults.
        """
        if 'Content-Length' not in self.headers:
            print 'CLEANUP HEADERS'
            self.set_content_length()


  class MyWSGIRequestHandler (WSGIRequestHandler):
    def handle (self):
        #WSGIRequestHandler.handle (self)

        self.raw_requestline = self.rfile.readline()
        if not self.parse_request(): # An error code has been sent, just exit
            return
        handler = MyServerHandler(self.rfile, self.wfile, self.get_stderr(), self.get_environ())
        handler.request_handler = self      # backpointer for logging
        handler.run(self.server.get_app())
        print
        print 'HEADERS', handler.headers
        print 'RESULT', handler.result
        print 'STATUS', handler.status
        print 'ENVIRON', handler.environ
        print 'BYTES SENT', handler.bytes_sent
        print 'HEADERS SENT', handler.headers_sent
        #print 'ENV', self.get_environ()

  class MySecureServer (WSGIServer):
    timeout = 5

    def __init__(self, addr, RequestHandlerClass, certFile=None, keyFile=None,
            cert_reqs=ssl.CERT_NONE, ssl_protocol=ssl.PROTOCOL_SSLv23):
        """Initialize this class and its base classes."""

        SocketServer.BaseServer.__init__(self, addr, RequestHandlerClass)

        sock = socket.socket(self.address_family, self.socket_type)
        print 'BEFORE',self.address_family, self.socket_type, sock
        self.socket = ssl.wrap_socket(sock,
                keyfile=keyFile,
                certfile=certFile,
                server_side=True,
                cert_reqs=cert_reqs,
                ca_certs=keyFile,
                ssl_version=ssl_protocol)
        print 'AFTER', self.socket
        self.server_bind()
        self.server_activate()
        print 'AFTER ACTIVATE', self.server_name, self.server_port

    def my_serve_forever(self):
        """Handle one request at a time until shutdown, respecting timeout."""
        self.__serving = True
        #self.__is_shut_down.clear()
        while self.__serving:
            #print 'REQ'
            self.handle_request()
        #self.__is_shut_down.set()

    #uncomment_for_debug='''
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

    # uncomment_for_debug='''
    def handle_request(self):
        import select
        """Handle one request, possibly blocking.

        Respects self.timeout.
        """
        # Support people who used socket.settimeout() to escape
        # handle_request before self.timeout was available.
        timeout = self.socket.gettimeout()
        if timeout is None:
            timeout = self.timeout
        elif self.timeout is not None:
            timeout = min(timeout, self.timeout)
        fd_sets = select.select([self], [], [], timeout)
        print 'HANDLE_REQUEST:', fd_sets
        if not fd_sets[0]:
            self.handle_timeout()
            return
        self._handle_request_noblock()

    # uncomment_for_debug='''
    def _handle_request_noblock(self):
        """Handle one request, without blocking.

        I assume that select.select has returned that the socket is
        readable before this function was called, so there should be
        no risk of blocking in get_request().
        """
        try:
            print 'HANDLE_REQUEST_NOBLOCK:',
            request, client_address = self.get_request()
            print 'DONE:', request, client_address
        except socket.error, e:
            print 'EXCEPTION', e
            return
        if self.verify_request(request, client_address):
            try:
                print 'PROCESS REQUEST:', 
                print self.process_request(request, client_address)
                #print self.close_request(request)  # JJW
                print 'DONE.'
            except Exception, e:
                print 'EXCEPTION', e
                self.handle_error(request, client_address)
                self.close_request(request)

    def handle_timeout (self):
        print '.',  # 'TIMEOUT', self.base_environ

  print 'INIT', settings.CERT_FILE, os.path.exists (settings.CERT_FILE)
  server = MySecureServer ( ('localhost',8000), MyWSGIRequestHandler, certFile=settings.CERT_FILE)
  admin_media_path = settings.ADMIN_MEDIA_PREFIX
  print 'SET_APP'
  handler = AdminMediaHandler (WSGIHandler(), admin_media_path)
  server.set_app (handler)
  print 'SERVE'
  #server.serve_forever()
  server.my_serve_forever()
