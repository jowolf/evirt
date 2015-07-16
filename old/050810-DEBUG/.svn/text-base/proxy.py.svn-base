import urllib2, uuid, httplib, urllib
from jsonrpc._json import loads, dumps
from jsonrpc.types import *

class ServiceProxy(object):
  def __init__(self, service_url, service_name=None, version='1.0'):
    self.__version = str(version)
    self.__service_url = service_url
    self.__service_name = service_name

  def __getattr__(self, name):
    if self.__service_name != None:
      name = "%s.%s" % (self.__service_name, name)
    return ServiceProxy(self.__service_url, name, self.__version)
  
  def __repr__(self):
    return {"jsonrpc": self.__version,
            "method": self.__service_name}

  def __call__(self, *args, **kwargs):
    params = kwargs if len(kwargs) else args
    if Any.kind(params) == Object and self.__version != '2.0':
      raise Exception('Unsupport arg type for JSON-RPC 1.0 '
                     '(the default version for this client, '
                     'pass version="2.0" to use keyword arguments)')
    req = urllib2.Request(self.__service_url,
    #r = urllib.urlopen(self.__service_url,
                        data = dumps({
                          "jsonrpc": self.__version,
                          "method": self.__service_name,
                          'params': params,
                          'id': str(uuid.uuid1())})) #.read()
    #r = urllib2.urlopen(req).read()
    opener = urllib2.build_opener (urllib2.HTTPSHandler(1))
    f = opener.open (req)
    print 'READ', f, f.fp,
    print f.fp._sock, dir (f.fp._sock)
    #print req.has_data()
    #print req.get_data()
    print f.info() # same as f.fp._sock.msg - just the headers
    print f.fp._sock.status, f.fp._sock.reason, f.fp._sock.will_close, f.fp._sock.length
    print f.fp._sock.chunked, f.fp._sock.chunk_left, f.fp._sock.version
    #print f.fp._sock.read(1000)
    #print 'READ2'
    r = f.read()

    y = loads(r)
    if u'error' in y:
      try:
        from django.conf import settings
        if settings.DEBUG:
            print '%s error %r' % (self.__service_name, y)
      except:
        pass
    return y


  def dont__call__(self, *args, **kwargs):
    params = kwargs if len(kwargs) else args
    if Any.kind(params) == Object and self.__version != '2.0':
      raise Exception('Unsupport arg type for JSON-RPC 1.0 '
                     '(the default version for this client, '
                     'pass version="2.0" to use keyword arguments)')


    conn = httplib.HTTPSConnection ('localhost:8000') # self.__service_url)
    conn.request("POST", "/json/", # params, headers
            urllib.urlencode (dict (data = dumps({
                          "jsonrpc": self.__version,
                          "method": self.__service_name,
                          'params': params,
                          'id': str(uuid.uuid1())}))), {})
    response = conn.getresponse()
    print response.status, response.reason
    data = response.read()
    conn.close()

    y = loads(data)
    if u'error' in y:
      try:
        from django.conf import settings
        if settings.DEBUG:
            print '%s error %r' % (self.__service_name, y)
      except:
        pass
    return y
