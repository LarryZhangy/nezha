"""Database setup and migration commands."""

from nezha import utils


IMPL = utils.LazyPluggable('backend',
                           config_group='database',
                           sqlalchemy='nezha.db.sqlalchemy.migration')

INIT_VERSION = 0


def db_sync(version=None):
    """Migrate the database to `version` or the most recent version."""
    return IMPL.db_sync(version=version)


def db_version():
    """Display the current database version."""
    return IMPL.db_version()
