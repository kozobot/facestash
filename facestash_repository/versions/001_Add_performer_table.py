from sqlalchemy import Table, Column, Integer, MetaData, DateTime

meta = MetaData()

performer = Table(
    'performer', meta,
    Column('stash_id', Integer, primary_key=True),
    Column('created_at', DateTime, nullable=False),
    Column('updated_at', DateTime, nullable=False),
)


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    performer.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    performer.drop()
