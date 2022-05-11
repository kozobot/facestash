from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api

# Initialize Flask
app = Flask(__name__)

# Add CORS support
CORS(app)

# Initialize the database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///facestash.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Initialize REST support
api = Api(app)


@app.route('/')
def hello():
    return 'My First API !!'
