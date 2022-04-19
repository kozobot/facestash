from datetime import date
from ariadne import convert_kwargs_to_snake_case
from api import db
from api.models import Performer


@convert_kwargs_to_snake_case
def create_performer_resolver(obj, info, stash_id):
    try:
        today = date.today()
        performer = Performer(
            stash_id=stash_id, created_at=today, updated_at=today
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
def update_performer_resolver(obj, info, id, title, description):
    try:
        performer = Performer.query.get(id)
        # if performer:
        #     performer.title = title
        #     performer.description = description
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
