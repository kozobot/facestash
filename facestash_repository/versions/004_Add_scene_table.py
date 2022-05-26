from sqlalchemy import Table, Column, Integer, MetaData, DateTime, ForeignKey, String
import json

meta = MetaData()

scene = Table(
    'scene', meta,
    Column('oshash', String, primary_key=True),
    Column('created_at', DateTime, nullable=False),
    Column('updated_at', DateTime, nullable=False),
)


scene_face_association = Table(
    'scene_face_association', meta,
    Column('oshash', String, ForeignKey(scene.c.oshash), primary_key=True),
    # Can't create the face column here because we don't have a db context to load the face table.  Do that
    #  down below in the upgrade method
)


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    # create the scene table
    scene.create()

    # Get a reference to the face table so we can create the primary key
    face = Table('face', meta, autoload=True)

    # create the associate table to faces
    scene_face_association.append_column(
        Column('face_id', Integer, ForeignKey(face.c.id), primary_key=True))
    scene_face_association.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    scene_face_association.drop()
    scene.drop()
