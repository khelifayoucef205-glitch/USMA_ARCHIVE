from flask import Blueprint


main = Blueprint("main", __name__)


@main.route("/")
def home():
    return "USMA V0.1 is running!"