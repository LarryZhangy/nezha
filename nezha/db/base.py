from oslo.config import cfg

from nezha.openstack.common import importutils

db_driver_opt = cfg.StrOpt('db_driver',
                           default='nezha.db',
                           help='driver to use for database access')

CONF = cfg.CONF
CONF.register_opt(db_driver_opt)


class Base(object):
    """DB driver is injected in the init method."""

    def __init__(self, db_driver=None):
        if not db_driver:
            db_driver = CONF.db_driver
        self.db = importutils.import_module(db_driver) 
