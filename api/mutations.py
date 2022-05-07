import datetime
import logging
import requests
import tempfile
import traceback

from ariadne import convert_kwargs_to_snake_case
from api import db
from api.models import Performer, Face

import face_recognition
from PIL import UnidentifiedImageError
import pickle


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
            # TODO - should we call create performer instead?
            performer = Performer(
                stash_id=stash_id, created_at=now, updated_at=now
            )

        # Load the image and get any faces
        logging.info("Starting facial recognition on " + image_path)

        tmp_img = tempfile.NamedTemporaryFile(delete=True)
        try:
            # Fetch the image and save to a temp file
            tmp_img.write(requests.get(
                image_path,
                # TODO - load the API key from config
                headers={'ApiKey': "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOiJ0YWNvIiwiaWF0IjoxNjUwMzc4MzA3LCJzdWIiOiJBUElLZXkifQ.TOFuBYbUAeHes4SRIiKiF4P6BQWhg0VeXVcwyo3X7F0"}
            ).content)
            logging.debug(f"Wrote Image to temp file: {tmp_img.name}")

            # find faces in the image
            performer_image = face_recognition.load_image_file(tmp_img.name)
            performer_face_encodings = face_recognition.face_encodings(performer_image)

            # dump to pickle for storage
            if len(performer_face_encodings) > 0:
                performer.face = Face()
                performer.face.encoding = pickle.dumps(performer_face_encodings[0])
            else:
                logging.warning(f"Found unexpected number of encodings({len(performer_face_encodings)}) for {stash_id}")

            logging.debug(f"Saved pickle for {stash_id}")
        except (FileNotFoundError, UnidentifiedImageError) as err:
            logging.warning(f"Could not load image for facial recognition: {image_path} \n{err}")
        finally:
            tmp_img.close()

        db.session.add(performer)
        db.session.commit()
        payload = {
            "success": True,
            "performer": performer.to_dict()
        }
    except AttributeError as err:
        traceback.print_exc()
        payload = {
            "success": False,
            "errors": [f"item matching id {stash_id} not found: {err}"]
        }

    return payload
