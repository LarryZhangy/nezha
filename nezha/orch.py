import time
import eventlet
import greenlet
import contextlib

from taskflow.patterns import graph_flow as gf
from taskflow.patterns import linear_flow as lf

from taskflow.openstack.common import uuidutils

from taskflow import engines
from taskflow import exceptions as exc
from taskflow import task

from taskflow.persistence import backends
from taskflow.utils import eventlet_utils as e_utils
from taskflow.utils import persistence_utils as p_utils

from nezha.openstack.common import log as logging
from nezha.openstack.common.gettextutils import _


LOG = logging.getLogger(__name__)


class Server(object):
    def __init__(self, master):
        self.master = master

    def _run(self):
        while True:
            self.master.run_for_master()
            if self.master.is_leader:
                LOG.info("I'm the leader!")
                self._resume_flow()
                time.sleep(10)
                break
            else:
                LOG.info("Someone else is the leader!")

    def _resume_flow(self):
        LOG.info("Resume all suspend flows.")

        backend = _get_backend()

        engine_conf = {
            'engine': 'parallel',
        }
        if e_utils.EVENTLET_AVAILABLE:
            engine_conf['executor'] = e_utils.GreenExecutor(5)
        # Get all logbook and it's flows
        with contextlib.closing(backend.get_connection()) as conn:
            for book in conn.get_logbooks():
                for flow_detail in book:
                    if flow_detail.state == 'SUCCESS':
                        continue

                    LOG.info("Resume flow:%s"%flow_detail.name)
                    engine = engines.load_from_detail(flow_detail,
                                                      backend=backend,
                                                      engine_conf=engine_conf)
                    engine.run()

    def start(self):
        tf_kwargs = {
            'func': self._run
        }
        self._server = eventlet.spawn(**tf_kwargs)

    def stop(self):
        if self._server is not None:
            self._server.kill()

    def wait(self):
        try:
            self._server.wait()
        except greenlet.GreenletExit:
            LOG.info(_("WSGI server has stopped."))

def _get_backend():
    backend_uri = 'sqlite:////tmp/nezha.db'

    backend = backends.fetch({'connection': backend_uri})
    backend.get_connection().upgrade()
    return backend
