
import settings

if __name__ == "__main__":
    hosts = settings.hosts
    #port = settings.port  # could just append to host(s)

    for host in hosts:

        import socket, ssl, pprint

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # require a certificate from the server
        ssl_sock = ssl.wrap_socket(s,
                                keyfile=settings.cert_file,
                                certfile=settings.cert_file,
                                ca_certs=settings.cert_file,
                                do_handshake_on_connect=False,
                                cert_reqs=ssl.CERT_REQUIRED)
        print 'CONNECT'
        #ssl_sock.connect(('www.verisign.com', 443))
        ssl_sock.connect(('localhost', 16861))
        print 'GETPEERNAME'
        print repr(ssl_sock.getpeername())
        print ssl_sock.cipher()
        print pprint.pformat(ssl_sock.getpeercert())

        # Set a simple HTTP request -- use httplib in actual code.
        ssl_sock.write("""GET / HTTP/1.0\r
        Host: www.verisign.com\r\n\r\n""")

        # Read a chunk of data.  Will not necessarily
        # read all the data returned by the server.
        data = ssl_sock.read()

        # note that closing the SSLSocket will also close the underlying socket
        ssl_sock.close()

