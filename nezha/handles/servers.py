from oslo.config import cfg

from nezha import db
from nezha import exception
from nezha.openstack.common.db import exception as db_exc
from nezha.openstack.common import gettextutils as _
from nezha.openstack.common import log as logging

def get_server(server_id, ctxt=None):
    return db.server_get(ctxt, server_id)

def create_server(values, ctxt=None):
    return db.server_create(ctxt, values)
    

