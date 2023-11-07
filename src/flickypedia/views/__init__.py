from flask import abort, render_template, request, jsonify
from flask_login import current_user, login_required

from .get_photos import get_photos
from .prepare_info import prepare_info, truncate_description
from .select_photos import select_photos
from .wait_for_upload import get_upload_status, wait_for_upload


def homepage():
    return render_template("homepage.html")


def about():
    return render_template("about.html", current_step=None)


def bookmarklet():
    return render_template("bookmarklet.html", current_step=None)


@login_required
def validate_title_api():
    """
    A basic API for title validation that can be called from JS on the page.

    This allows us to have a single definition of title validation
    which is shared by client and server-side checks.
    """
    try:
        title = request.args["title"]
    except KeyError:
        return abort(400)

    api = current_user.wikimedia_api()
    result = api.validate_title(title)

    return jsonify(result)


__all__ = [
    "about",
    "bookmarklet",
    "get_photos",
    "get_upload_status",
    "homepage",
    "prepare_info",
    "select_photos",
    "truncate_description",
    "validate_title_api",
    "wait_for_upload",
]
