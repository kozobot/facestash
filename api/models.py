import datetime

from facestash import db


# This is the reference to a Performer in Stash
class Performer(db.Model):
    # use the stash id as the primary key
    stash_id = db.Column(db.String, primary_key=True)
    # when this was created
    created_at = db.Column(db.DATETIME(timezone=True), nullable=False, default=datetime.datetime.now())
    # when this was lasted updated.  Important for determining when to refresh data
    updated_at = db.Column(db.DATETIME(timezone=True), nullable=False, default=datetime.datetime.now())

    def to_dict(self):
        return {
            "stash_id": self.stash_id,
            "created_at": str(self.created_at.strftime('%d-%m-%Y')),
            "updated_at": str(self.created_at.strftime('%d-%m-%Y'))
        }


class Face(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # when this was created
    created_at = db.Column(db.DATETIME(timezone=True), nullable=False, default=datetime.datetime.now())
    # when this was lasted updated.  Important for determining when to refresh data
    updated_at = db.Column(db.DATETIME(timezone=True), nullable=False, default=datetime.datetime.now())

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": str(self.created_at.strftime('%d-%m-%Y')),
            "updated_at": str(self.created_at.strftime('%d-%m-%Y'))
        }