"""
Demo to run flask with local debugging or with gunicorn.
"""
from flask import Flask

from views import web_views


def create_app(settings_class):
    """
    Create a Flask app that can be run as a server

    @param settings_class: (str) or Config class
        to settings. See Flask docs.

    @return: Flask
        The flask app
    """
    app = Flask(__name__)
    app.config.from_object(settings_class)
    app.register_blueprint(web_views, url_prefix="/")

    return app


def run_local_app():
    """
    Run app locally just for development, don't use this in production, see main.py.
    """
    settings = "config.LocalConfig"
    app = create_app(settings)

    app.run(
        debug=app.config["DEBUG"],
        host="0.0.0.0",
        port=app.config["HTTP_PORT"],
    )


if __name__ == "__main__":
    run_local_app()
