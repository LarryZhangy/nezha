"""
SQLAlchemy models for nezha data.
"""

from sqlalchemy import Column, Index, Integer, BigInteger, Enum, String, schema
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey, DateTime, Boolean, Text, Float
from sqlalchemy.orm import relationship, backref, object_mapper
from oslo.config import cfg

from nezha.openstack.common.db.sqlalchemy import models
from nezha.openstack.common import timeutils

CONF = cfg.CONF
BASE = declarative_base()


def MediumText():
    return Text().with_variant(MEDIUMTEXT(), 'mysql')


class NezhaBase(models.SoftDeleteMixin,
                models.TimestampMixin,
                models.ModelBase):
    metadata = None


class Server(BASE, NezhaBase):
    """Represents a running server on a host."""

    __tablename__ = 'servers'
    __table_args__ = ()

    id = Column(Integer, primary_key=True)
    ip = Column(String(255))
    status = Column(String(255), default='free')



