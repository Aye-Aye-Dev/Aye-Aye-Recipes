"""
Non-API views in HTML
"""
from functools import wraps

from flask import Blueprint, current_app, render_template, request

from controllers import cluster_arns

web_views = Blueprint("web", __name__)


def check_auth(username, password):
    "Check basic auth."
    return username == "fossa" and password == current_app.config["HTTP_USER_PASSWORD"]


def login_required(f):
    @wraps(f)
    def wrapped_view(**kwargs):
        auth = request.authorization
        if not (auth and check_auth(auth.username, auth.password)):
            return ("Unauthorized", 401, {"WWW-Authenticate": 'Basic realm="Login Required"'})

        return f(**kwargs)

    return wrapped_view


@web_views.route("/")
@login_required
def available_clusters():
    page_vars = {
        "cluster_arns": cluster_arns(),
    }
    return render_template("clusters.html", **page_vars)
