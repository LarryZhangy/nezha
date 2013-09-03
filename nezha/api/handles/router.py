from stevedore import extension

from nezha import wsgi
from nezha.api.handles import servers
from nezha.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class API(wsgi.Router):

    mgr = extension.ExtensionManager(
        namespace='nezha.api.handles.extensions',
        invoke_on_load=True,
        invoke_args=()
        )
    
    def __init__(self, mapper):
        servers_resource = servers.create_resource()

        mapper.connect('/servers',
                       controller=servers_resource,
                       action='index',
                       conditions={'method': ['GET']})

        mapper.connect('/servers/{server_id}',
                       controller=servers_resource,
                       action='show',
                       conditions={'method': ['GET']})

        mapper.connect('/servers',
                       controller=servers_resource,
                       action='create',
                       conditions={'method': ['POST']})

        self.mgr.map(self._load_extensions, mapper)
        LOG.debug(_("List route mapper:\n%s") % str(mapper))

        super(API, self).__init__(mapper)

    def _load_extensions(self, ext, mapper):
        res = ext.obj.get_resource()
        kargs = dict(controller=res.controller)

        mapper.resource(res.name, res.resource, **kargs)
