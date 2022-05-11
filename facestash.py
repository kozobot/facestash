from api import app, api, db
from ariadne import load_schema_from_path, make_executable_schema, \
    graphql_sync, snake_case_fallback_resolvers, ObjectType
from ariadne.constants import PLAYGROUND_HTML
from flask import request, jsonify
from flask_restful import Resource, reqparse
from api.queries import listPerformers_resolver, getPerformer_resolver
from api.mutations import create_performer_resolver, update_performer_resolver, create_scene_resolver, update_scene_resolver
import os

# Configure the resolvers
query = ObjectType("Query")
mutation = ObjectType("Mutation")
query.set_field("listPerformers", listPerformers_resolver)
query.set_field("getPerformer", getPerformer_resolver)
mutation.set_field("createPerformer", create_performer_resolver)
mutation.set_field("updatePerformer", update_performer_resolver)


# Load the graphql schema
type_defs = load_schema_from_path("schema.graphql")
schema = make_executable_schema(
    type_defs, query, mutation, snake_case_fallback_resolvers
)


# Set up the GraphQL UI for playing with queries
@app.route("/graphql", methods=["GET"])
def graphql_playground():
    return PLAYGROUND_HTML, 200


@app.route("/graphql", methods=["POST"])
def graphql_server():
    data = request.get_json()
    success, result = graphql_sync(
        schema,
        data,
        context_value=request,
        debug=app.debug
    )
    status_code = 200 if success else 400
    return jsonify(result), status_code


@app.before_first_request
def before_first_request():
    logger_level = os.environ.get("LOGLEVEL", "INFO")
    app.logger.warning(f"Setting logger level to {logger_level}")
    app.logger.setLevel(logger_level)


# set up the REST services
parser = reqparse.RequestParser()
parser.add_argument('oshash')


class RestScene(Resource):
    def get(self, oshash):
        # Wrap the GraphQL calls.
        # Stash scrapers only support GET calls, so infer some context rather than use REST convention
        app.logger.debug(f"Rest Call: {oshash}")
        return update_scene_resolver({}, {})


api.add_resource(RestScene, "/rest/scene/<checksum>")
