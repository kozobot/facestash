import datetime
import logging

import face_recognition

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

        # Load the image and get any faces
        logging.info("Starting facial recognition on " + image_path)
        try:
            performer_image = face_recognition.load_image_file(image_path)
            performer_face_encoding = face_recognition.face_encodings(performer_image)[0]
            logging.debug("Found facial encoding: " + performer_face_encoding)
        except FileNotFoundError:
            logging.warn(f"Could not find image for facial recognition: {image_path}")

        db.session.add(performer)
        db.session.commit()
        payload = {
            "success": True,
            "performer": performer.to_dict()
        }

    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": [f"item matching id {stash_id} not found"]
        }
    return payload
