import os
import sys

from oslo.config import cfg

path_opts = [
    cfg.StrOpt('pybasedir',
               default=os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                    '../')),
               help='Directory where the nova python module is installed'),
    cfg.StrOpt('bindir',
               default=os.path.join(sys.prefix, 'local', 'bin'),
               help='Directory where nova binaries are installed'),
    cfg.StrOpt('state_path',
               default='$pybasedir',
               help="Top-level directory for maintaining nova's state"),
]

CONF = cfg.CONF
CONF.register_opts(path_opts)


def basedir_def(*args):
    """Return an uninterpolated path relative to $pybasedir."""
    return os.path.join('$pybasedir', *args)


def bindir_def(*args):
    """Return an uninterpolated path relative to $bindir."""
    return os.path.join('$bindir', *args)


def state_path_def(*args):
    """Return an uninterpolated path relative to $state_path."""
    return os.path.join('$state_path', *args)
