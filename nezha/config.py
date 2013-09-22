from oslo.config import cfg

from nezha import version


def parse_args(argv, default_config_files=None):
    cfg.CONF(argv[1:],
             project='nezha',
             version=version.version_string(),
             default_config_files=default_config_files)
