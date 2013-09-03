import webob.exc

from nezha import exception
from nezha.api import wsgi
from nezha.handles import servers
from nezha.openstack.common import log as logging

LOG= logging.getLogger(__name__)

class ServersController(object):
    def __init__(self):
        pass

    def index(self, req):
        raise webob.exc.HTTPNotImplemented()

    def show(self, req, server_id):
        try:
            server = servers.get_server(server_id)
        except exception.NotFound, e:
            raise webob.exc.HTTPNotFound()

        return server.to_dict()

    def create(self, req, body):
        try:
            server = servers.create_server(body)
        except exception.Forbidden as e:
            raise webob.exc.HTTPForbidden(explanation=unicode(e))
        return dict(server)

def create_resource():
    deserializer = wsgi.JSONRequestDeserializer()
    serializer = wsgi.JSONResponseSerializer()
    controller = ServersController()

    return wsgi.Resource(controller, deserializer, serializer)
