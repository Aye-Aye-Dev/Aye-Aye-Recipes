"""
Non-API views in HTML
"""
from functools import wraps
from urllib.parse import quote_plus, unquote_plus

from flask import Blueprint, current_app, render_template, request

from controllers import cluster_arns, fossa_node_info, task_summary

web_views = Blueprint("web", __name__)


# TODO - login check for all of blueprint - @web_views.before_request


def check_auth(username, password):
    "Check basic auth."
    return username == "fossa" and password == current_app.config.get("HTTP_USER_PASSWORD")


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
    cluster_details = [{"url_encoded": quote_plus(c), "arn": c} for c in cluster_arns()]

    page_vars = {
        "cluster_arns": cluster_details,
    }
    return render_template("clusters.html", **page_vars)


@web_views.route("/<cluster_arn_encoded>/tasks")
@login_required
def tasks(cluster_arn_encoded):
    cluster_arn = unquote_plus(cluster_arn_encoded)

    page_vars = {
        "cluster_arn": cluster_arn,
        "cluster_arn_encoded": cluster_arn_encoded,
        "task_summary": task_summary(cluster_arn),
    }
    return render_template("tasks.html", **page_vars)


@web_views.route("/<cluster_arn_encoded>/node_info/<ipv4>")
@login_required
def node_info(cluster_arn_encoded, ipv4):
    """
    Fetch node info from the Fossa API in the cluster task running at `ipv4`.

    @param ipv4: (str)
    """
    cluster_arn = unquote_plus(cluster_arn_encoded)
    fossa_node_port = current_app.config["FOSSA_NODE_PORT"]
    node_info = fossa_node_info(fossa_node_port, cluster_arn, ipv4)

    print(node_info)

    page_vars = {
        "cluster_arn": cluster_arn,
        "ipv4": ipv4,
        **node_info,
    }
    return render_template("node_info.html", **page_vars)
