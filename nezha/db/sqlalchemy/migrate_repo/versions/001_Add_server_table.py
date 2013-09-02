from sqlalchemy import Table, Column, Integer, String
from sqlalchemy import Boolean, MetaData, DateTime


meta = MetaData()

server = Table(
    'server', meta,
    Column('created_at', DateTime),
    Column('updated_at', DateTime),
    Column('deleted_at', DateTime),
    Column('deleted', Boolean),
    Column('id', Integer, primary_key=True),
    Column('ip', String(255)),
    Column('status', String(255)),
)

def upgrade(migrate_engine):
    meta.bind = migrate_engine
    server.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    server.drop()
