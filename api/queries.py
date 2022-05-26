from . import app
from .models import Performer, Face, Scene
from ariadne import convert_kwargs_to_snake_case

import face_recognition
import pickle


def listPerformers_resolver(obj, info):
    try:
        app.logger.debug("listPerformers_resolver")
        performers = [performer.to_dict() for performer in Performer.query.all()]
        app.logger.info(f"Found {len(performers)} performers")
        payload = {
            "success": True,
            "performer": performers
        }
    except Exception as error:
        payload = {
            "success": False,
            "errors": [str(error)]
        }
    return payload


@convert_kwargs_to_snake_case
def getPerformer_resolver(obj, info, stash_id):
    try:
        performer = Performer.query.get(stash_id)
        app.logger.debug(f'performer: {performer.to_dict()}')
        payload = {
            "success": True,
            "performer": performer.to_dict()
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["Performer item matching {id} not found"]
        }
    return payload

@convert_kwargs_to_snake_case
def getPerformersForScene_resolver(obj, info, oshash):
    try:
        # Get the scene based on the oshash
        scene = Scene.query.get(oshash)
        app.logger.debug(f'scene: {scene.to_dict()}')

        # Map the Scene db objects into what face recognition wants
        scene_face_encodings = []
        for face in scene.faces:
            scene_face_encodings.append(pickle.loads(face.encoding))

        # Run the comparison between the available performer faces and the scene faces
        # Get all the performers with faces
        result = Performer.query.join(Face).all()

        # Map the Performer db objects in to what face recognition wants
        known_face_encodings = []
        known_face_names = []
        for row in result:
            known_face_names.append(row)
            known_face_encodings.append(pickle.loads(row.face.encoding))

        # match each of the faces from the scene
        performers = []
        for scene_face in scene_face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, scene_face, tolerance=0.5)
            if True in matches:
                first_match_index = matches.index(True)
                performers.append(known_face_names[first_match_index])

        payload = {
            "success": True,
            "performer": performers
        }
    except AttributeError:  # todo not found
        payload = {
            "success": False,
            "errors": ["Performer item matching {id} not found"]
        }
    return payload
