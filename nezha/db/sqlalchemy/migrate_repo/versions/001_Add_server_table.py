from sqlalchemy import Table, Column, Integer, String, MetaData

meta = MetaData()

server = Table(
    'server', meta,
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
