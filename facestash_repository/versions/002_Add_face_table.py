from sqlalchemy import Table, Column, Integer, MetaData, DateTime, BLOB

meta = MetaData()

face = Table(
    'face', meta,
    Column('id', Integer, primary_key=True),
    Column('encoding', BLOB, nullable=False),
    Column('created_at', DateTime, nullable=False),
    Column('updated_at', DateTime, nullable=False),
)


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    face.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    face.drop()
