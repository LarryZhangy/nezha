import fixtures
from oslo.config import cfg

from nezha import paths
from nezha import config


CONF = cfg.CONF
CONF.import_opt('api_paste_config', 'nezha.wsgi')
CONF.import_opt('rpc_backend', 'nezha.openstack.common.rpc')


class ConfFixture(fixtures.Fixture):
    """Fixture to manage global conf settings."""

    def __init__(self, conf):
        self.conf = conf

    def setUp(self):
        super(ConfFixture, self).setUp()

        self.conf.set_default('api_paste_config',
                              paths.state_path_def('etc/api-paste.ini'))
        self.conf.set_default('rpc_backend',
                              'nezha.openstack.common.rpc.impl_fake')
        self.conf.set_default('rpc_cast_timeout', 5)
        self.conf.set_default('rpc_response_timeout', 5)
        self.conf.set_default('verbose', True)
        config.parse_args([], default_config_files=[])
        self.addCleanup(self.conf.reset)
