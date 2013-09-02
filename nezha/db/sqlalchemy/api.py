import collections
import copy
import datetime
import functools
import sys
import time
import uuid

from oslo.config import cfg
from sqlalchemy import and_
from sqlalchemy import Boolean
from sqlalchemy.exc import DataError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import or_
from sqlalchemy.orm import contains_eager
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import joinedload_all
from sqlalchemy.orm import noload
from sqlalchemy.schema import Table
from sqlalchemy.sql.expression import asc
from sqlalchemy.sql.expression import desc
from sqlalchemy.sql.expression import select
from sqlalchemy.sql import func
from sqlalchemy import String

from nezha import db
from nezha.db.sqlalchemy import models
from nezha import exception
from nezha.openstack.common.db import exception as db_exc
from nezha.openstack.common.db.sqlalchemy import session as db_session
from nezha.openstack.common.gettextutils import _
from nezha.openstack.common import log as logging
from nezha.openstack.common import timeutils
from nezha.openstack.common import uuidutils

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

get_engine = db_session.get_engine
get_session = db_session.get_session

def get_backend():
    """The backend is this module itself."""
    return sys.modules[__name__]


def server_get(context, server_id):
    session = get_session()
    query = session.query(models.Server).filter_by(id=server_id)
    result = query.first()
    if not result:
        raise exception.ServerNotFound(server_id=server_id)

    return result

def server_create(context, values):
    server_ref = models.Server()
    server_ref.update(values)

    try:
        server_ref.save()
    except db_exc.DBDuplicateEntry:
        raise exception.ServerExists(ip=values.get('ip'))

    return server_ref
