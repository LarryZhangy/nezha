from nezha.api import wsgi

class ServersController(object):
    def __init__(self):
        pass

    def index(self, req):
        return {'servers':[]}

    def show(sefl, req, server_id):
        return {'server': server_id}

def create_resource():
    deserializer = wsgi.JSONRequestDeserializer()
    serializer = wsgi.JSONResponseSerializer()
    controller = ServersController()

    return wsgi.Resource(controller, deserializer, serializer)
