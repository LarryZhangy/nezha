import traceback
import webob

from nezha import exception
from nezha.openstack.common import log as logging
import nezha.openstack.common.rpc.common as rpc_common

from nezha import wsgi as base_wsgi
from nezha.api import wsgi

logger = logging.getLogger(__name__)


class Fault(object):

    def __init__(self, error):
        self.error = error

    @webob.dec.wsgify(RequestClass=wsgi.Request)
    def __call__(self, req):
        serializer = wsgi.JSONResponseSerializer()
        resp = webob.Response(request=req)
        default_webob_exc = webob.exc.HTTPInternalServerError()
        resp.status_code = self.error.get('code', default_webob_exc.code)
        serializer.default(resp, self.error)
        return resp


class FaultWrapper(base_wsgi.Middleware):
    """Replace error body with something the client can parse."""

    error_map = {
        'AttributeError': webob.exc.HTTPBadRequest,
        'ValueError': webob.exc.HTTPBadRequest,
        'StackNotFound': webob.exc.HTTPNotFound,
        'ResourceNotFound': webob.exc.HTTPNotFound,
        'ResourceTypeNotFound': webob.exc.HTTPNotFound,
        'ResourceNotAvailable': webob.exc.HTTPNotFound,
        'PhysicalResourceNotFound': webob.exc.HTTPNotFound,
        'InvalidTenant': webob.exc.HTTPForbidden,
        'StackExists': webob.exc.HTTPConflict,
        'StackValidationFailed': webob.exc.HTTPBadRequest,
        'InvalidTemplateReference': webob.exc.HTTPBadRequest,
        'UnknownUserParameter': webob.exc.HTTPBadRequest,
        'RevertFailed': webob.exc.HTTPInternalServerError,
        'ServerBuildFailed': webob.exc.HTTPInternalServerError,
        'NotSupported': webob.exc.HTTPBadRequest,
        'MissingCredentialError': webob.exc.HTTPBadRequest,
        'UserParameterMissing': webob.exc.HTTPBadRequest,
    }

    def _error(self, ex):

        trace = None
        webob_exc = None

        ex_type = ex.__class__.__name__

        if ex_type.endswith(rpc_common._REMOTE_POSTFIX):
            ex_type = ex_type[:-len(rpc_common._REMOTE_POSTFIX)]

        message = str(ex.message)

        if not trace:
            trace = str(ex)
            if trace.find('\n') > -1:
                unused, trace = trace.split('\n', 1)
            else:
                trace = traceback.format_exc()

        if not webob_exc:
            webob_exc = self.error_map.get(ex_type,
                                           webob.exc.HTTPInternalServerError)

        error = {
            'code': webob_exc.code,
            'title': webob_exc.title,
            'explanation': webob_exc.explanation,
            'error': {
                'message': message,
                'type': ex_type,
                'traceback': trace,
            }
        }

        return error

    def process_request(self, req):
        try:
            return req.get_response(self.application)
        except Exception as exc:
            return req.get_response(Fault(self._error(exc)))
