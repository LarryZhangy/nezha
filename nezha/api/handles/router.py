from nezha import wsgi
from nezha.api.handles import servers


class API(wsgi.Router):
    
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

        super(API, self).__init__(mapper)
