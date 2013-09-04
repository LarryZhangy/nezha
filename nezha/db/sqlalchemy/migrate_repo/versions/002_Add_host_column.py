from sqlalchemy import Table, MetaData, String, Column


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    server = Table('server', meta, autoload=True)
    hostc = Column('host', String(255))
    hostc.create(server)


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    server = Table('server', meta, autoload=True)
    server.c.host.drop()
