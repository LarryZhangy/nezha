from oslo.config import cfg

from nezha import exception
from nezha.openstack.common.db import api as db_api
from nezha.openstack.common.gettextutils import _
from nezha.openstack.common import log as logging


_BACKEND_MAPPING = {'sqlalchemy': 'nezha.db.sqlalchemy.api'}


IMPL = db_api.DBAPI(backend_mapping=_BACKEND_MAPPING)
LOG = logging.getLogger(__name__)


#######################


def server_get(context, server_id):
    """Get a service or raise if it does not exist."""
    return IMPL.server_get(context, server_id)

