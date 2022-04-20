import datetime
from ariadne import convert_kwargs_to_snake_case
from api import db
from api.models import Performer


@convert_kwargs_to_snake_case
def create_performer_resolver(obj, info, stash_id):
    try:
        now = datetime.datetime.now()
        performer = Performer(
            stash_id=stash_id, created_at=now, updated_at=now
        )
        db.session.add(performer)
        db.session.commit()
        payload = {
            "success": True,
            "performer": performer.to_dict()
        }
    except ValueError:  # date format errors
        payload = {
            "success": False,
            "errors": [f"Incorrect date format provided. Date should be in "
                       f"the format dd-mm-yyyy"]
        }
    return payload


@convert_kwargs_to_snake_case
def update_performer_resolver(obj, info, stash_id, image_path):
    try:
        now = datetime.datetime.now()
        performer = Performer.query.get(stash_id)
        if performer:
            performer.updated_at = now
        else:
            performer = Performer(
                stash_id=stash_id, created_at=now, updated_at=now
            )
        # TODO - run the facial stuff
        db.session.add(performer)
        db.session.commit()
        payload = {
            "success": True,
            "performer": performer.to_dict()
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["item matching id {id} not found"]
        }
    return payload
