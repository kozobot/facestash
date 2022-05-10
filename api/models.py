import datetime

from facestash import db


# This is the reference to a Performer in Stash
class Performer(db.Model):
    __tablename__ = 'performer'
    # use the id from stash as the primary key
    stash_id = db.Column(db.Integer, primary_key=True)
    # relationship to the face
    face_id = db.Column(db.Integer, db.ForeignKey('face.id'))
    # one-to-one to Face
    face = db.relationship('Face', uselist=False)
    # when this was created
    created_at = db.Column(db.DATETIME(timezone=True), nullable=False, default=datetime.datetime.utcnow())
    # when this was lasted updated.  Important for determining when to refresh data
    updated_at = db.Column(db.DATETIME(timezone=True), nullable=False, default=datetime.datetime.utcnow())

    def to_dict(self):
        return {
            "stash_id": self.stash_id,
            "face_id": self.face.id if self.face else self.face_id,
            #"face": self.face.id,
            "created_at": str(self.created_at.strftime('%d-%m-%Y')),
            "updated_at": str(self.updated_at.strftime('%d-%m-%Y'))
        }


class Face(db.Model):
    __tablename__ = 'face'
    id = db.Column(db.Integer, primary_key=True)
    # store the face encoding as a Pickle BLOB
    encoding = db.Column(db.PickleType, nullable=False)
    # when this was created
    created_at = db.Column(db.DATETIME(timezone=True), nullable=False, default=datetime.datetime.utcnow())
    # when this was lasted updated.  Important for determining when to refresh data
    updated_at = db.Column(db.DATETIME(timezone=True), nullable=False, default=datetime.datetime.utcnow())

    def to_dict(self):
        return {
            "id": self.id,
            "encoding": self.encoding,
            "created_at": str(self.created_at.strftime('%d-%m-%Y')),
            "updated_at": str(self.updated_at.strftime('%d-%m-%Y'))
        }