
class ShowVersion(object):
    def __init__(self):
        pass

    def __call__(self, environ, start_response):
        start_response("200 OK", [("Content-Type", "text/plain")])
        return ["Version: 0.0.1",]

    @classmethod
    def factory(cls, global_conf, **kwargs):
        print "in showversion", global_conf, kwargs
        return ShowVersion()
