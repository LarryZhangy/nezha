from nezha.openstack.common.gettextutils import _
from nezha.handles import rpcapi as handle_rpcapi
from nezha.openstack.common import log as logging


LOG = logging.getLogger(__name__)


class API(object):
    def __init__(self):
        self.handle_rpcapi = handle_rpcapi.HandleRPCAPI()


    def get_all_iptables_by_host(self, ctxt, host):
        return self.handle_rpcapi.get_all_iptables(ctxt, host)
