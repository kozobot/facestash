from . import app
from datetime import datetime
import pytz
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
        now = datetime.utcnow()
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
def update_performer_resolver(obj, info, stash_id, image_path, updated_at):
    try:
        app.logger.debug(f"update_performer_resolver {stash_id}")
        face_performer = Performer.query.get(stash_id)
        if not face_performer:
            # create the performer since one doesn't exist
            create_performer_resolver(obj, info, stash_id)
            face_performer = Performer.query.get(stash_id)

        # Check if we need to bother updating the performer.  We will reprocess the face if the stash performer was
        #  updated more recently, or if there is no prior face (like if it was just created)
        # The face_performer was loaded from the DB, which we assume is in UTC.  Gross.  We just set the timezone
        # to UTC so we can run the compare.
        # The timezone provided by Stash is in ISO format with a non UTC timestamp.  Convert that timestamp to UTC.
        # If the stash performer was updated more recently than the face perfomer, then go ahead and recompute the face.
        if (datetime.fromisoformat(updated_at).astimezone(pytz.utc) >=
                face_performer.updated_at.replace(tzinfo=pytz.utc)
                or
                face_performer.face is None):
            # Load the image and get any faces
            app.logger.info("Starting facial recognition on " + image_path)
            tmp_img = tempfile.NamedTemporaryFile(delete=True)
            try:
                # Fetch the image and save to a temp file
                tmp_img.write(requests.get(
                    image_path,
                    # TODO - load the API key from config
                    headers={'ApiKey': "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOiJ0YWNvIiwiaWF0IjoxNjUwMzc4MzA3LCJzdWIiOiJBUElLZXkifQ.TOFuBYbUAeHes4SRIiKiF4P6BQWhg0VeXVcwyo3X7F0"}
                ).content)
                app.logger.debug(f"Wrote Image to temp file: {tmp_img.name}")

                # find faces in the image
                performer_image = face_recognition.load_image_file(tmp_img.name)
                performer_face_encodings = face_recognition.face_encodings(performer_image)

                # dump to pickle for storage
                if len(performer_face_encodings) == 0:
                    # clear out the existing face if it exists
                    if face_performer.face:
                        app.logger.info(f"Performer {face_performer.stash_id} has no face, clearing old face value {face_performer.face_id}")
                        face_performer.face_id = None
                        face_performer.face = None
                elif len(performer_face_encodings) == 1:
                    face_performer.face = face_performer.face if face_performer.face else Face()
                    face_performer.face.encoding = pickle.dumps(performer_face_encodings[0])
                else:
                    # Too many faces found.  Not storing them at all.
                    app.logger.warning(f"Found unexpected number of encodings({len(performer_face_encodings)}) for {stash_id}")

                app.logger.debug(f"Saved pickle for {stash_id}")
            except (FileNotFoundError, UnidentifiedImageError) as err:
                app.logger.warning(f"Could not load image for facial recognition: {image_path} \n{err}")
            finally:
                tmp_img.close()
        else:
            # This is for the case were we are just updating perfomers in bulk.  No reason to reprocess their faces.
            app.logger.info(f"Skipping facial recoginition on {face_performer.stash_id}, updated recently")

        # set the updated timestamp
        face_performer.updated_at = datetime.utcnow()

        db.session.add(face_performer)
        db.session.commit()
        payload = {
            "success": True,
            "performer": face_performer.to_dict()
        }
    except AttributeError as err:
        traceback.print_exc()
        payload = {
            "success": False,
            "errors": [f"item matching id {stash_id} not found: {err}"]
        }

    app.logger.debug(f"Saved Performer: {payload}")
    return payload


@convert_kwargs_to_snake_case
def create_scene_resolver(obj, info):
    app.logger.debug("create_scene_resolver")


@convert_kwargs_to_snake_case
def update_scene_resolver(obj, info, oshash):
    app.logger.debug(f"update_scene_resolver: {oshash}")

    # find if we have a scene to update

    # go grab the streaming url from Stash

    # process the streaming url

    # store any faces

    # Run the comparison between the available performer faces and the scene faces
