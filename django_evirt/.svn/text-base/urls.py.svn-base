from django.conf.urls.defaults import *

from jsonrpc import jsonrpc_site
import django_evirt.evirt_app.views  # django-jsonrpc requires that you must import the views that need connected

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^django_evirt/', include('django_evirt.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),

    # django-jsonrpc urls:
    url(r'^json/browse/', 'jsonrpc.views.browse', name="jsonrpc_browser"), # for the graphical browser/web console only, omissible
    url(r'^json/', jsonrpc_site.dispatch, name="jsonrpc_mountpoint"),
    url(r'^RPC2/', jsonrpc_site.dispatch, name="jsonrpc_mountpoint"),
    (r'^json/(?P<method>[a-zA-Z0-9.]+)$', jsonrpc_site.dispatch) # for HTTP GET only, also omissible
)
