import json
import sys
import copy
import re
from gql import gql, Client
from graphql.error import GraphQLError
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.exceptions import TransportError, TransportQueryError
from aiohttp import connector


def __prefix(level_char):
    start_level_char = b'\x01'
    end_level_char = b'\x02'

    ret = start_level_char + level_char + end_level_char
    return ret.decode()


def log(levelChar, s):
    s_out = copy.deepcopy(s)
    if not isinstance(s_out, str):
        s_out = str(s_out)
    s_out = re.sub(r'(?<=")(data:image.+?;base64).+?(?=")', r'\1;truncated', s_out)

    if levelChar == "":
        return

    print(__prefix(levelChar) + s_out + "\n", file=sys.stderr, flush=True)


def main(stash_conn):
    # Set up our connection to Stash
    global stash_client, face_client

    # init the gql client for stash
    stash_scheme = stash_conn['Scheme'] if stash_conn.get('Scheme') else 'http'
    stash_domain = stash_conn['Domain'] if stash_conn.get('Domain') else 'localhost'
    stash_port = stash_conn['Port'] if stash_conn.get('Port') else '9999'
    stash_url = f'{stash_scheme}://{stash_domain}:{stash_port}/graphql'
    stash_cookies = {}
    if stash_conn.get('SessionCookie'):
        stash_cookies['session'] = stash_conn['SessionCookie']['Value']
    stash_transport = AIOHTTPTransport(url=stash_url, cookies=stash_cookies)
    stash_client = Client(transport=stash_transport, fetch_schema_from_transport=True)
    log(b'i', f'Created Stash Client ("{stash_url}")')

    # init the gql client for stash
    #   TODO - get this from config
    face_url = f'http://172.17.0.1:5000/graphql'
    face_transport = AIOHTTPTransport(url=face_url)
    face_client = Client(transport=face_transport, fetch_schema_from_transport=True)
    log(b'i', f'Created Face Client ("{face_url}")')


def update_performer(performer):
    log(b't', f'Processing Performer ("{performer["id"]}")')
    try:
        mutationUpdatePerformer = gql("""
                mutation UpdatePerformer($stashId: String!, $imagePath: String!, $updatedAt: String!) {
                  updatePerformer(stash_id: $stashId, image_path: $imagePath, updated_at: $updatedAt) {
                    performer {
                      stash_id
                      face_id
                    }
                  }
                }
            """)
        face_client.execute(mutationUpdatePerformer,
                            variable_values={
                                "stashId": performer["id"],
                                "imagePath": performer["image_path"],
                                "updatedAt": performer["updated_at"]
                            })
    except (GraphQLError, TransportError, TransportQueryError) as err:
        log(b'e', f'Could not process performer in FaceStash {performer["id"]} - {err}')
    except (ConnectionRefusedError, connector.ClientConnectorError, ) as err:
        log(b'e', f'Could not connect to FaceStash: {err}')


def query_stash_performer(performerId):
    # go get a single performer from stash
    log(b't', f"Querying Stash Performer {performerId}")
    result = {'findPerformer': {}}
    try:
        findPerfomer = gql("""
            query findPerformer($id: ID!) {
              findPerformer(id: $id) {
                id
                image_path
                updated_at
              }
            }
        """)
        result = stash_client.execute(findPerfomer,
                                      variable_values={"id": performerId})
    except GraphQLError as err:
        log(b'e', f'Could not load performers {err}')
    except (ConnectionRefusedError, TransportError, connector.ClientConnectorError) as err:
        log(b'e', f'Could not connect to Stash: {err}')

    return result['findPerformer']

def query_all_stash_performers():
    # go get all the performers from stash
    log(b't', "Querying All Stash Performers")
    result = {'allPerformers': []}
    try:
        queryAllPerformers = gql("""
            query Performer {
              allPerformers {
                id
                image_path
                updated_at
              }
            }
        """)
        result = stash_client.execute(queryAllPerformers)
    except GraphQLError as err:
        log(b'e', f'Could not load performers {err}')
    except (ConnectionRefusedError, TransportError, connector.ClientConnectorError) as err:
        log(b'e', f'Could not connect to Stash: {err}')

    return result['allPerformers']


if __name__ == '__main__':
    json_input = json.loads(sys.stdin.read())
    log(b't', f'Starting plugin: {json.dumps(json_input)}')

    # Init our graphql connections
    main(json_input["server_connection"])

    mode = json_input['args']['mode']

    if mode == "generate_performers":
        # fetch all the perfomers from stash
        performers = query_all_stash_performers()
        # loop over the performers and call the face client
        for performer in performers:
            update_performer(performer)
    elif mode == "update_performer":
        performer = query_stash_performer(json_input['args']['hookContext']['id'])
        update_performer(performer)

    # Log that we are done
    log(b'i', json.dumps({"output": "ok"}))
