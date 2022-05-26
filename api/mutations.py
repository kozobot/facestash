import functools

from . import app
from datetime import datetime
import pytz
import requests
import tempfile
import traceback

from ariadne import convert_kwargs_to_snake_case
from api import db
from api.models import Performer, Face, Scene

import face_recognition
from PIL import UnidentifiedImageError
import pickle

import cv2

FRAME_SKIP = 15

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
def create_scene_resolver(obj, info, oshash):
    app.logger.debug("create_scene_resolver")
    try:
        now = datetime.utcnow()
        scene = Scene(
            oshash=oshash, created_at=now, updated_at=now
        )
        db.session.add(scene)
        db.session.commit()
        payload = {
            "success": True,
            "performer": scene.to_dict()
        }
    except ValueError:  # date format errors
        payload = {
            "success": False,
            "errors": [f"Incorrect date format provided. Date should be in "
                       f"the format dd-mm-yyyy"]
        }
    return payload


def process_stream(stream):
    # Pull the faces out of the stream
    app.logger.debug(f"process_stream: loading stream {stream}")
    video_capture = cv2.VideoCapture(stream)
    if (video_capture.isOpened() == False):
        raise Exception(f"Could not open stream {stream}")

    # loop through the video frames
    #  Keep a counter for calculating how many frames to skip
    framecounter = 0
    raw_face_encodings = []
    while(video_capture.isOpened()):
        # vid_capture.read() methods returns a tuple, first element is a bool
        # and the second is frame
        ret, frame = video_capture.read()

        # check if we are at the end of the video
        if not ret:
            video_capture.release()
            break

        # check if we should process this frame
        if framecounter % FRAME_SKIP == 0:
            # Resize frame of video to 1/4 size for faster face recognition processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            rgb_small_frame = small_frame[:, :, ::-1]

            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(rgb_small_frame)
            raw_face_encodings.extend(face_recognition.face_encodings(rgb_small_frame, face_locations))

        # increment our counter
        framecounter = framecounter + 1

    # reduce the number of faces so we have a unique set from the video
    app.logger.debug(f"process_stream: Finished processing video. Found {len(raw_face_encodings)} raw faces")
    scene_face_encodings = functools.reduce(
        # add to the scene list if the this face_enc is not matched to the scene list
        lambda l, face_enc: l.append(face_enc) or l
        if True not in face_recognition.compare_faces(l, face_enc, tolerance=0.4) else l,
        raw_face_encodings,
        [])

    app.logger.info(f"process_stream: Found {len(scene_face_encodings)} unique faces in the scene")
    return scene_face_encodings


@convert_kwargs_to_snake_case
def update_scene_resolver(obj, info, oshash, stream, updated_at):
    try:
        app.logger.debug(f"update_scene_resolver: {oshash}")

        # find if we have a scene to update
        face_scene = Scene.query.get(oshash)
        if not face_scene:
            # create the scene since one doesn't exist
            create_scene_resolver(obj, info, oshash)
            face_scene = Scene.query.get(oshash)

        # Check if we need to bother updating the scene.  We will reprocess the scene if the stash scene was
        #  updated more recently, or if there is no prior faces (like if it was just created)
        # The face_scene was loaded from the DB, which we assume is in UTC.  Gross.  We just set the timezone
        # to UTC so we can run the compare.
        # The timezone provided by Stash is in ISO format with a non UTC timestamp.  Convert that timestamp to UTC.
        # If the stash performer was updated more recently than the face perfomer, then go ahead and recompute the face.
        if (datetime.fromisoformat(updated_at).astimezone(pytz.utc) >=
                face_scene.updated_at.replace(tzinfo=pytz.utc) or
                face_scene.faces is None or
                len(face_scene.faces) == 0):
            # process the stream
            scene_face_encodings = process_stream(stream)

            # store any faces
            face_scene.faces = []
            for face_enc in scene_face_encodings:
                face = Face()
                face.encoding = pickle.dumps(face_enc)
                face_scene.faces.append(face)

            # set the updated timestamp
            face_scene.updated_at = datetime.utcnow()

            db.session.add(face_scene)
            db.session.commit()

        payload = {
            "success": True,
            "scene": face_scene.to_dict()
        }
    except AttributeError as err:
        traceback.print_exc()
        payload = {
            "success": False,
            "errors": [f"item matching id {oshash} not found: {err}"]
        }

    app.logger.debug(f"Saved Scene: {oshash}")
    return payload
