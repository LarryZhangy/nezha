from oslo.config import cfg

from nezha.openstack.common.gettextutils import _
from nezha.openstack.common import rpc
from nezha.openstack.common.rpc import proxy
from nezha.openstack.common import log as logging


LOG = logging.getLogger(__name__)


rpc_opts = [
    cfg.StrOpt('handle_topic',
               default="handle",
               help='The topic for handle.'),
    ]

CONF = cfg.CONF
CONF.register_opts(rpc_opts)


def _make_topic(topic, host):
    return '%s.%s' % (topic, host) if host else topic


class HandleRPCAPI(proxy.RpcProxy):

    BASE_VERSION = '1.0'

    def __init__(self):
        self.topic = CONF.handle_topic
        super(HandleRPCAPI, self).__init__(self.topic, self.BASE_VERSION)

    def get_all_iptables(self, ctxt, host):
        return self.call(ctxt, self.make_msg('get_all_iptables'),
                        topic=_make_topic(self.topic, host))

