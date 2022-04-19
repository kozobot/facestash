from facestash import db

class Performer(db.Model):
    stash_id = db.Column(db.String, primary_key=True)
    created_at = db.Column(db.Date)
    updated_at = db.Column(db.Date)
    def to_dict(self):
        return {
            "id": self.id,
            "stash_id": self.stash_id,
            "created_at": str(self.created_at.strftime('%d-%m-%Y')),
            "updated_at": str(self.created_at.strftime('%d-%m-%Y'))
        }