from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    performer = Table('performer', meta, autoload=True)
    face = Table('face', meta, autoload=True)
    facec = Column('face_id', Integer, ForeignKey(face.c.id))
    facec.create(performer)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    performer = Table('performer', meta, autoload=True)
    performer.c.face.drop()
