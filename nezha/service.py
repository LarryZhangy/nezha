import os
import time
import random
import sys

from kazoo.client import KazooClient
from kazoo.client import KazooState
from kazoo.exceptions import ConnectionLoss
from kazoo.exceptions import NodeExistsError
from kazoo.exceptions import NoNodeError

from oslo.config import cfg

from nezha.openstack.common.gettextutils import _
from nezha.openstack.common import importutils
from nezha.openstack.common import log as logging
from nezha.openstack.common import rpc
from nezha.openstack.common import service
from nezha import wsgi
from nezha import orch

LOG = logging.getLogger(__name__)


service_opts = [
    cfg.IntOpt('report_interval',
               default=10,
               help='seconds between nodes reporting state to datastore'),
    cfg.BoolOpt('periodic_enable',
               default=True,
               help='enable periodic tasks'),
    cfg.IntOpt('periodic_fuzzy_delay',
               default=60,
               help='range of seconds to randomly delay when starting the'
                    ' periodic task scheduler to reduce stampeding.'
                    ' (Disable by setting to 0)'),
    cfg.StrOpt('nezha_listen',
               default="0.0.0.0",
               help='IP address for OpenStack API to listen'),
    cfg.IntOpt('nezha_listen_port',
               default=8774,
               help='list port for osapi compute'),
    cfg.IntOpt('nezha_workers',
               help='Number of workers for OpenStack API service'),
    ]

CONF = cfg.CONF
CONF.register_opts(service_opts)


class ZKMaster(object):
    def __init__(self):
        self.zk = KazooClient('127.0.0.1:2181')
        self.server_id = str(random.randint(1, 10))
        self.is_leader = False

    def start(self):
        self.zk.start()

    def run_for_master(self):
        while True:
            try:
                self.zk.create('/master', self.server_id, None, True)
                self.is_leader = True
                break
            except NodeExistsError:
                self.is_leader = False
                break
            except ConnectionLoss:
                pass

            if self.check_master(): break

    def check_master(self):
        while True:
            try:
                data, stat = self.zk.get('/master')
                server_id = data.decode('utf-8')
                self.is_leader = True if self.server_id == server_id else False
                return True
            except NoNodeError:
                return False
            except ConnectionLoss:
                pass

    def stop(self):
        self.zk.stop()


class TFService(object):
    def __init__(self):
        self.master = ZKMaster()
        self.server = orch.Server(self.master)

    def start(self):
        self.master.start()
        self.server.start()

    def stop(self):
        self.master.stop()
        self.server.stop()

    def wait(self):
        self.server.wait()


class WSGIService(object):
    """Provides ability to launch API from a 'paste' configuration."""

    def __init__(self, name, loader=None, use_ssl=False, max_url_len=None):
        """Initialize, but do not start the WSGI server.

        :param name: The name of the WSGI server given to the loader.
        :param loader: Loads the WSGI application using the given name.
        :returns: None
        
        """
        self.name = name
        self.manager = self._get_manager()
        self.loader = loader or wsgi.Loader()
        self.app = self.loader.load_app(name)
        self.host = getattr(CONF, '%s_listen' % name, "0.0.0.0")
        self.port = getattr(CONF, '%s_listen_port' % name, 0)
        self.workers = getattr(CONF, '%s_workers' % name, None)
        self.use_ssl = use_ssl
        self.server = wsgi.Server(name,
                                  self.app,
                                  host=self.host,
                                  port=self.port,
                                  use_ssl=self.use_ssl,
                                  max_url_len=max_url_len)
        # Pull back actual port used
        self.port = self.server.port
        self.backdoor_port = None

    def _get_manager(self):
        """Initialize a Manager object appropriate for this service.

        Use the service name to look up a Manager subclass from the
        configuration and initialize an instance. If no class name
        is configured, just return None.
        
        :returns: a Manager instance, or None.
        
        """
        fl = '%s_manager' % self.name
        if fl not in CONF:
            return None

        manager_class_name = CONF.get(fl, None)
        if not manager_class_name:
            return None

        manager_class = importutils.import_class(manager_class_name)
        return manager_class()

    def start(self):
        """Start serving this service using loaded configuration.

        Also, retrieve updated port number in case '0' was passed in, which
        indicates a random port should be used.
        
        :returns: None
        
        """
        if self.manager:
            self.manager.init_host()
            self.manager.pre_start_hook()
        if self.backdoor_port is not None:
            self.manager.backdoor_port = self.backdoor_port
        self.server.start()
        if self.manager:
            self.manager.post_start_hook()

    def stop(self):
        """Stop serving this API.

        :returns: None
        
        """
        self.server.stop()

    def wait(self):
        """Wait for the service to stop serving this API.

        :returns: None
        
        """
        self.server.wait()


def process_launcher():
    return service.ProcessLauncher()


# NOTE(vish): the global launcher is to maintain the existing
# functionality of calling service.serve +
# service.wait
_launcher = None


def serve(server, workers=None):
    global _launcher
    if _launcher:
        raise RuntimeError(_('serve() can only be called once'))

    _launcher = service.launch(server, workers=workers)


def wait():
    _launcher.wait()
