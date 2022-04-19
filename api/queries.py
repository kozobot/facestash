from .models import Performer
from ariadne import convert_kwargs_to_snake_case


def listPerformers_resolver(obj, info):
    try:
        print("here")
        performers = [performer.to_dict() for performer in Performer.query.all()]
        print(performers)
        payload = {
            "success": True,
            "performers": performers
        }
    except Exception as error:
        payload = {
            "success": False,
            "errors": [str(error)]
        }
    return payload


@convert_kwargs_to_snake_case
def getPerformer_resolver(obj, info, id):
    try:
        performer = Performer.query.get(id)
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
