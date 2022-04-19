import json
import sys
import copy
import re
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport


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

    generate_performers()

    log(b'i', json.dumps({"output": "ok"}))


def generate_performers():
    try:
        log(b't', "Querying All Performers")
        queryAllPerformers = gql("""
            query Performer {
              allPerformers {
                id
                image_path
              }
            }
        """)
        result = stash_client.execute(queryAllPerformers)

        # loop over the performers and call the face client
        for performer in result['allPerformers']:
            log(b'i', f'Processing Performer ("{performer["id"]}")')
            mutationUpdatePerformer = gql("""
                mutation UpdatePerformer($stashId: String!, $imagePath: String!) {
                  updatePerformer(stash_id: $stashId, image_path: $imagePath) {
                    performer {
                      id
                    }
                  }
                }
            """)
            face_client.execute(mutationUpdatePerformer,
                                variable_values={
                                    "stashId": performer["id"], "imagePath": performer["image_path"]
                                })
    except gql.GraphQLException as err:
        log(b'e', f'Could not load performers {err}')


if __name__ == '__main__':
    json_input = json.loads(sys.stdin.read())
    main(json_input["server_connection"])