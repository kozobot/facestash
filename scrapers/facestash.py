import json
import sys
import re
import functools
from gql import gql, Client
from graphql.error import GraphQLError
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.exceptions import TransportError, TransportQueryError
from aiohttp import connector

# Load our configured imports
try:
    import py_common.log as log
    import py_common.graphql as graphql
    import py_common.config as config
except ModuleNotFoundError:
    print(
        "You need to download the folder 'py_common' from the community repo (CommunityScrapers/tree/master/scrapers/py_common)",
        file=sys.stderr)
    sys.exit(1)

# init the gql client for facestash
#   TODO - get this from config
face_url = f'http://172.17.0.1:5000/graphql'
face_transport = AIOHTTPTransport(url=face_url)
face_client = Client(transport=face_transport, fetch_schema_from_transport=True)
log.info(f'Created Face Client ("{face_url}")')


def get_scene(id):
    # get the additional info we need for the scene
    query = '''
        query findScene($id: ID!) {
          findScene(id: $id) {
            id
            updated_at
            sceneStreams {
              url
            }
          }
        }
    '''

    # Call graphql and get all the performers
    gql_result = graphql.callGraphQL(query, variables={ "id": id })
    if gql_result is None:
        log.warn(f'Could not find scene {id}')
        return None
    return gql_result['findScene']


def update_scene(scene):
    log.trace(f'Processing Scene ("{scene["id"]}")')
    try:
        mutationUpdateScene = gql("""
                mutation UpdateScene($oshash: String!, $stream: String!, $updatedAt: String!) {
                  updateScene(oshash: $oshash, stream: $stream, updated_at: $updatedAt) {
                    success
                    errors
                    scene { oshash }
                  }
                }
            """)
        stream = next(iter([path for path in scene["sceneStreams"] if re.match(r'.*\.mp4\?resolution=LOW', path['url'])]),None)
        variables = {
            "oshash": scene["id"],
            "stream": stream['url'] + "&apikey=" + config.STASH["api_key"],
            "updatedAt": scene["updated_at"]
        }
        face_client.execute(mutationUpdateScene,
                            variable_values=variables)
    except (GraphQLError, TransportError, TransportQueryError) as err:
        log.error(f'Could not process scene in FaceStash {scene["id"]} - {err}')
    except (ConnectionRefusedError, connector.ClientConnectorError, ) as err:
        log.error(f'Could not connect to FaceStash: {err}')


def get_performers_for_scene(scene):
    log.debug(f'Processing Scene ("{scene["id"]}")')
    try:
        mutationUpdateScene = gql("""
                query GetPerformersForScene($oshash: String!) {
                  getPerformersForScene(oshash: $oshash) {
                    success
                    errors
                    performer {
                      stash_id
                    }
                  }
                }
            """)
        result = face_client.execute(mutationUpdateScene,
                            variable_values={
                                "oshash": scene["id"],
                            })
        return list(map(lambda performer: performer['stash_id'], result['getPerformersForScene']['performer']))
    except (GraphQLError, TransportError, TransportQueryError) as err:
        log.error(f'Could not get performers for scene in FaceStash {scene["id"]} - {err}')
    except (ConnectionRefusedError, connector.ClientConnectorError, ) as err:
        log.error(f'Could not connect to FaceStash: {err}')


def get_performers(ids):
    log.debug(f"Getting peformers: {json.dumps(ids)}")
    # get the additional info we need for the scene
    query = '''
        query findPerfomer($id: ID!) {
          findPerformer(id: $id) {
            name
          }
        }
    '''

    # Call graphql and get all the performers
    return list(map(lambda id: graphql.callGraphQL(query, variables={ "id": id })['findPerformer'], ids))


# Get the scene by the fragment.
def sceneByFragment():
    # read the input.  A title must be passed in for the sceneByURL call
    inp = json.loads(sys.stdin.read())
    log.trace("Input: " + json.dumps(inp))
    if not inp['id']:
        log.error('No id Entered')
    log.trace("id: " + inp['id'])

    # fetch the updated date and the stream from stash
    scene_id = inp['id']
    scene = get_scene(scene_id)
    if scene is None:
        log.error(f"Could not find scene {scene_id}")
        return {}
    log.trace(f"Found scene: {json.dumps(scene)}")

    # call face stash with the info to update the scene
    update_scene(scene)

    # call face stash to get the matched peformers (just ids)
    performer_ids = get_performers_for_scene(scene)

    # call stash to get the performer names for the ids
    performer_names = get_performers(performer_ids)
    log.debug(f"Performer names: {json.dumps(performer_names)}")

    return {
        "performers": performer_names
    }


# Figure out what was invoked by Stash and call the correct thing
if sys.argv[1] == "sceneByFragment":
    print(json.dumps(sceneByFragment()))
else:
    log.error("Unknown argument passed: " + sys.argv[1])
    print(json.dumps({}))
