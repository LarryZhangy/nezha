import sys
import ssl
import os.path
import socket

import eventlet
import eventlet.wsgi
import greenlet
import webob.dec
import webob.exc
import routes.middleware
from paste import deploy

from oslo.config import cfg

from nezha import exception
from nezha.openstack.common import excutils
from nezha.openstack.common.gettextutils import _
from nezha.openstack.common import log as logging

# Raise the default from 8192 to accommodate large tokens
eventlet.wsgi.MAX_HEADER_LINE = 16384

wsgi_opts = [
    cfg.StrOpt('api_paste_config',
               default="api-paste.ini",
               help='File name for the paste.deploy config for nezha-api'),
    cfg.StrOpt('wsgi_log_format',
            default='%(client_ip)s "%(request_line)s" status: %(status_code)s'
                    ' len: %(body_length)s time: %(wall_seconds).7f',
            help='A python format string that is used as the template to '
                 'generate log lines. The following values can be formatted '
                 'into it: client_ip, date_time, request_line, status_code, '
                 'body_length, wall_seconds.'),
    cfg.StrOpt('ssl_ca_file',
               help="CA certificate file to use to verify "
                    "connecting clients"),
    cfg.StrOpt('ssl_cert_file',
                    help="SSL certificate of API server"),
    cfg.StrOpt('ssl_key_file',
                    help="SSL private key of API server"),
    cfg.IntOpt('tcp_keepidle',
               default=600,
               help="Sets the value of TCP_KEEPIDLE in seconds for each "
                    "server socket. Not supported on OS X.")
    ]
CONF = cfg.CONF
CONF.register_opts(wsgi_opts)

LOG = logging.getLogger(__name__)


class Server(object):
    """Server class to manage a WSGI server, serving a WSGI application."""

    default_pool_size = 1000

    def __init__(self, name, app, host='0.0.0.0', port=0, pool_size=None,
                       protocol=eventlet.wsgi.HttpProtocol, backlog=128,
                       use_ssl=False, max_url_len=None):
        """Initialize, but do not start, a WSGI server.

        :param name: Pretty name for logging.
        :param app: The WSGI application to serve.
        :param host: IP address to serve the application.
        :param port: Port number to server the application.
        :param pool_size: Maximum number of eventlets to spawn concurrently.
        :param backlog: Maximum number of queued connections.
        :param max_url_len: Maximum length of permitted URLs.
        :returns: None
        :raises: nezha.exception.InvalidInput
        """
        self.name = name
        self.app = app
        self._server = None
        self._protocol = protocol
        self._pool = eventlet.GreenPool(pool_size or self.default_pool_size)
        self._logger = logging.getLogger("nezha.%s.wsgi.server" % self.name)
        self._wsgi_logger = logging.WritableLogger(self._logger)
        self._use_ssl = use_ssl
        self._max_url_len = max_url_len

        if backlog < 1:
            raise exception.InvalidInput(
                    reason='The backlog must be more than 1')

        bind_addr = (host, port)
        # TODO(dims): eventlet's green dns/socket module does not actually
        # support IPv6 in getaddrinfo(). We need to get around this in the
        # future or monitor upstream for a fix
        try:
            info = socket.getaddrinfo(bind_addr[0],
                                      bind_addr[1],
                                      socket.AF_UNSPEC,
                                      socket.SOCK_STREAM)[0]
            family = info[0]
            bind_addr = info[-1]
        except Exception:
            family = socket.AF_INET

        self._socket = eventlet.listen(bind_addr, family, backlog=backlog)
        (self.host, self.port) = self._socket.getsockname()[0:2]
        LOG.info(_("%(name)s listening on %(host)s:%(port)s") % self.__dict__)

    def start(self):
        """Start serving a WSGI application.

        :returns: None
        """
        if self._use_ssl:
            try:
                ca_file = CONF.ssl_ca_file
                cert_file = CONF.ssl_cert_file
                key_file = CONF.ssl_key_file

                if cert_file and not os.path.exists(cert_file):
                    raise RuntimeError(
                          _("Unable to find cert_file : %s") % cert_file)

                if ca_file and not os.path.exists(ca_file):
                    raise RuntimeError(
                          _("Unable to find ca_file : %s") % ca_file)

                if key_file and not os.path.exists(key_file):
                    raise RuntimeError(
                          _("Unable to find key_file : %s") % key_file)

                if self._use_ssl and (not cert_file or not key_file):
                    raise RuntimeError(
                          _("When running server in SSL mode, you must "
                            "specify both a cert_file and key_file "
                            "option value in your configuration file"))
                ssl_kwargs = {
                    'server_side': True,
                    'certfile': cert_file,
                    'keyfile': key_file,
                    'cert_reqs': ssl.CERT_NONE,
                }

                if CONF.ssl_ca_file:
                    ssl_kwargs['ca_certs'] = ca_file
                    ssl_kwargs['cert_reqs'] = ssl.CERT_REQUIRED

                self._socket = eventlet.wrap_ssl(self._socket,
                                                 **ssl_kwargs)

                self._socket.setsockopt(socket.SOL_SOCKET,
                                        socket.SO_REUSEADDR, 1)
                # sockets can hang around forever without keepalive
                self._socket.setsockopt(socket.SOL_SOCKET,
                                        socket.SO_KEEPALIVE, 1)

                # This option isn't available in the OS X version of eventlet
                if hasattr(socket, 'TCP_KEEPIDLE'):
                    self._socket.setsockopt(socket.IPPROTO_TCP,
                                    socket.TCP_KEEPIDLE,
                                    CONF.tcp_keepidle)

            except Exception:
                with excutils.save_and_reraise_exception():
                    LOG.error(_("Failed to start %(name)s on %(host)s"
                                ":%(port)s with SSL support") % self.__dict__)

        wsgi_kwargs = {
            'func': eventlet.wsgi.server,
            'sock': self._socket,
            'site': self.app,
            'protocol': self._protocol,
            'custom_pool': self._pool,
            'log': self._wsgi_logger,
            'log_format': CONF.wsgi_log_format
            }

        if self._max_url_len:
            wsgi_kwargs['url_length_limit'] = self._max_url_len

        self._server = eventlet.spawn(**wsgi_kwargs)

    def stop(self):
        """Stop this server.

        This is not a very nice action, as currently the method by which a
        server is stopped is by killing its eventlet.
        
        :returns: None
        
        """
        LOG.info(_("Stopping WSGI server."))

        if self._server is not None:
            # Resize pool to stop new requests from being processed
            self._pool.resize(0)
            self._server.kill()

    def wait(self):
        """Block, until the server has stopped.

        Waits on the server's eventlet to finish, then returns.
        
        :returns: None
        
        """
        try:
            self._server.wait()
        except greenlet.GreenletExit:
            LOG.info(_("WSGI server has stopped."))

class Middleware(object):
    """
    Base WSGI middleware wrapper. These classes require an application to be
    initialized that will be called next.  By default the middleware will
    simply call its wrapped app, or you can override __call__ to customize its
    behavior.
    """

    @classmethod
    def factory(cls, global_config, **local_config):
        """Used for paste app factories in paste.deploy config files.

        Any local configuration (that is, values under the [filter:APPNAME]
        section of the paste config) will be passed into the `__init__` method
        as kwargs.
        
        A hypothetical configuration would look like:
        
        [filter:analytics]
        redis_host = 127.0.0.1
        paste.filter_factory = nezha.api.analytics:Analytics.factory
        
        which would result in a call to the `Analytics` class as
        
        import nezha.api.analytics
        analytics.Analytics(app_from_paste, redis_host='127.0.0.1')
        
        You could of course re-implement the `factory` method in subclasses,
        but using the kwarg passing it shouldn't be necessary.
        
        """
        def _factory(app):
            return cls(app, **local_config)
        return _factory

    def __init__(self, application):
        self.application = application

    def process_request(self, req):
        """
        Called on each request.

        If this returns None, the next application down the stack will be
        executed. If it returns a response then that response will be returned
        and execution will stop here.

        """
        return None

    def process_response(self, response):
        """Do whatever you'd like to the response."""
        return response

    @webob.dec.wsgify
    def __call__(self, req):
        response = self.process_request(req)
        if response:
            return response
        response = req.get_response(self.application)
        return self.process_response(response)


class Loader(object):
    """Used to load WSGI applications from paste configurations."""

    def __init__(self, config_path=None):
        """Initialize the loader, and attempt to find the config.

        :param config_path: Full or relative path to the paste config.
        :returns: None
        
        """
        config_path = config_path or CONF.api_paste_config
        if os.path.exists(config_path):
            self.config_path = config_path
        else:
            self.config_path = CONF.find_file(config_path)
        if not self.config_path:
            raise exception.ConfigNotFound(path=config_path)

    def load_app(self, name):
        """Return the paste URLMap wrapped WSGI application.

        :param name: Name of the application to load.
        :returns: Paste URLMap object wrapping the requested application.
        :raises: `nezha.exception.PasteAppNotFound`
        
        """
        try:
            LOG.debug(_("Loading app %(name)s from %(path)s") %
                      {'name': name, 'path': self.config_path})
            return deploy.loadapp("config:%s" % self.config_path, name=name)
        except LookupError as err:
            LOG.error(err)
            raise exception.PasteAppNotFound(name=name, path=self.config_path)

class APIMapper(routes.Mapper):
    """
    Handle route matching when url is '' because routes.Mapper returns
    an error in this case.     
    """
      
    def routematch(self, url=None, environ=None): 
        if url is "":          
            result = self._match("", environ)
            return result[0], result[1] 
        return routes.Mapper.routematch(self, url, environ)


class Request(webob.Request):
    pass

class Router(object):
    """WSGI middleware that maps incoming requests to WSGI apps."""

    def __init__(self, mapper):
        """Create a router for the given routes.Mapper.

        Each route in `mapper` must specify a 'controller', which is a
        WSGI app to call. You'll probably want to specify an 'action' as
        well and have your controller be an object that can route
        the request to the action-specific method.
        
        Examples:
        mapper = routes.Mapper()
        sc = ServerController()
        
        # Explicit mapping of one route to a controller+action
        mapper.connect(None, '/svrlist', controller=sc, action='list')
        
        # Actions are all implicitly defined
        mapper.resource('server', 'servers', controller=sc)
        
        # Pointing to an arbitrary WSGI app. You can specify the
        # {path_info:.*} parameter so the target app can be handed just that
        # section of the URL.
        mapper.connect(None, '/v1.0/{path_info:.*}', controller=BlogApp())
        
        """
        self.map = mapper
        self._router = routes.middleware.RoutesMiddleware(self._dispatch,
                                                          self.map)

    @classmethod
    def factory(cls, global_conf, **local_conf):
        return cls(APIMapper())
    @webob.dec.wsgify(RequestClass=Request)
    def __call__(self, req):
        """Route the incoming request to a controller based on self.map.

        If no match, return a 404.
        
        """
        return self._router

    @staticmethod
    @webob.dec.wsgify(RequestClass=Request)
    def _dispatch(req):
        """Dispatch the request to the appropriate controller.

        Called by self._router after matching the incoming request to a route
        and putting the information into req.environ. Either returns 404
        or the routed WSGI app's response.
        
        """
        match = req.environ['wsgiorg.routing_args'][1]
        if not match:
            return webob.exc.HTTPNotFound()
        app = match['controller']
        return app
