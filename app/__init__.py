from flask import Flask


def create_app():
    app = Flask(__name__)

    @app.route("/")
    def home():
        return "USMA V0.1 is running!"

    return app