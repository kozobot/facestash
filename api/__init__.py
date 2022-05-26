from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# Initialize Flask
app = Flask(__name__)

# Add CORS support
CORS(app)

# Initialize the database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///facestash.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


@app.route('/')
def hello():
    return 'My First API !!'
