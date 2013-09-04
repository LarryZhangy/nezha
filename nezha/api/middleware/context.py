import webob.dec

from nezha import wsgi
from nezha import context


class InjectContext(wsgi.Middleware):

    @webob.dec.wsgify(RequestClass=wsgi.Request)
    def __call__(self, req):
        request_id = req.headers.get('x-request_id', None)
        req.environ['context'] = context.RequestContext(request_id)

        return self.application


