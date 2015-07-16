import os, sys

sys.path.insert (0, '/home/joe/Projects/evirt')
os.environ ['DJANGO_SETTINGS_MODULE'] = 'django_evirt.settings'

from jsonrpc.proxy import ServiceProxy

print 'INIT'
s = ServiceProxy('https://localhost:8000/json/') # , version="2.0")

#print list(`s`)

print 'SAYHELLO'
print s.myapp.sayHello('Sam')
#  {u'error': None, u'id': u'jsonrpc', u'result': u'Hello Sam'}

print 'GIMMETHAT'
print s.myapp.gimmeThat('username', 'password', 'test data')
#  {u'error': None, u'id': u'jsonrpc', u'result': {u'sauce': [u'authenticated', u'sauce']}}

print 'DONE'

