from flask import abort, jsonify, request
from flask_login import current_user, login_required


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
        abort(400)

    if not title.startswith("File:"):
        abort(400)

    api = current_user.wikimedia_api()
    result = api.validate_title(title)

    return jsonify(result)
