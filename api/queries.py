from .models import Performer
from ariadne import convert_kwargs_to_snake_case
import logging


def listPerformers_resolver(obj, info):
    try:
        logging.debug("listPerformers_resolver")
        performers = [performer.to_dict() for performer in Performer.query.all()]
        logging.info(f"Found {len(performers)} performers")
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
        logging.debug(f'performer: {performer.to_dict()}')
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
