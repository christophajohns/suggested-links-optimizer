from flask import Flask, request
from flask_cors import CORS
from utils import valid_data, suggested_links, update_classifier

app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    """Returns the version number of the application.

    :return: Application version
    :rtype: string
    """
    return "Suggested Link Optimizer App v0.0.1"


@app.route("/links", methods=["POST"])
def links():
    if valid_data(request.json):
        return suggested_links(request.json)
    else:
        return {"links": []}


@app.route("/model/<user_id>/links", methods=["POST"])
def links_from_interactive_model(user_id):
    if valid_data(request.json):
        return suggested_links(request.json, user_id)
    else:
        return {"links": []}


@app.route("/model/<user_id>/update", methods=["POST"])
def update_model(user_id):
    return update_classifier(request.json, user_id)
