import webob.exc

from nezha import exception
from nezha.api import wsgi
from nezha.api import extensions
from nezha.handles import servers
from nezha.openstack.common import log as logging

LOG= logging.getLogger(__name__)

class IpsController(object):
    def __init__(self):
        pass

    def index(self, req):
        raise webob.exc.HTTPNotImplemented()

    def show(self, req, id):
        raise webob.exc.HTTPNotImplemented()

    def create(self, req, body):
        raise webob.exc.HTTPNotImplemented()



class Ips(extensions.BaseExtension):
    name = 'ip'
    resource = 'ips'

    def __init__(self):
        self.controller = wsgi.Resource(IpsController())

