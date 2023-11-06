import html
import os
import sys

from flask import Flask, request
from jinja2 import StrictUndefined
import sass

from flickypedia.auth import (
    db,
    login,
    logout,
    oauth2_authorize_wikimedia,
    oauth2_callback_wikimedia,
)
from flickypedia.apis.wikidata import (
    get_entity_label,
    get_property_name,
    render_wikidata_date,
)
from flickypedia.config import create_config, get_directories
from flickypedia.duplicates import create_link_to_commons
from flickypedia.views import (
    about,
    bookmarklet,
    get_photos,
    get_upload_status,
    homepage,
    prepare_info,
    select_photos,
    truncate_description,
    validate_title_api,
    wait_for_upload,
)
from flickypedia.tasks import celery_init_app
from flickypedia.utils import a_href, size_at


def create_app(data_directory: str = "data", debug: bool = False):
    app = Flask(__name__)

    config = create_config(data_directory)

    app.config.update(**config)

    db.init_app(app)
    login.init_app(app)
    celery_init_app(app)

    with app.app_context():
        db.create_all()

    for dirname in get_directories(app.config):
        os.makedirs(dirname, exist_ok=True)

    app.add_url_rule("/", view_func=homepage)

    app.add_url_rule("/logout", view_func=logout)
    app.add_url_rule("/authorize/wikimedia", view_func=oauth2_authorize_wikimedia)
    app.add_url_rule("/callback/wikimedia", view_func=oauth2_callback_wikimedia)

    app.add_url_rule("/get_photos", view_func=get_photos, methods=["GET", "POST"])
    app.add_url_rule("/select_photos", view_func=select_photos, methods=["GET", "POST"])
    app.add_url_rule("/prepare_info", view_func=prepare_info, methods=["GET", "POST"])
    app.add_url_rule("/wait_for_upload/<task_id>", view_func=wait_for_upload)
    app.add_url_rule("/wait_for_upload/<task_id>/status", view_func=get_upload_status)

    app.add_url_rule("/about", view_func=about)
    app.add_url_rule("/bookmarklet", view_func=bookmarklet)

    app.add_url_rule("/api/validate_title", view_func=validate_title_api)

    app.jinja_env.filters["a_href"] = a_href
    app.jinja_env.filters["html_unescape"] = html.unescape
    app.jinja_env.filters["size_at"] = size_at
    app.jinja_env.filters["link_to_commons"] = create_link_to_commons
    app.jinja_env.filters["truncate_description"] = truncate_description

    app.jinja_env.filters["wikidata_property_name"] = get_property_name
    app.jinja_env.filters["wikidata_entity_label"] = get_entity_label
    app.jinja_env.filters["wikidata_date"] = render_wikidata_date

    # Compile the CSS.  If we're running in debug mode
    compile_scss(app.static_folder)

    if debug:

        @app.before_request
        def recompile_css():
            if request.path == "/static/style.css":
                compile_scss(app.static_folder)

        print("debug!")

    # This option causes Jinja to throw if we use an undefined variable
    # in one of the templates.
    # See https://alexwlchan.net/2022/strict-jinja/
    app.jinja_env.undefined = StrictUndefined

    # This causes Jinja to remove extraneous whitespace.
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    return app


def compile_scss(static_folder):
    """
    Compile the SCSS file into static.css.
    """
    sass_path = os.path.join(static_folder, "assets", "style.scss")
    css_path = os.path.join(static_folder, "style.css")

    with open(css_path + ".tmp", "w") as out_file:
        out_file.write(sass.compile(filename=sass_path))

    try:
        os.rename(css_path + ".tmp", css_path)
    except FileNotFoundError:
        pass


# celery --app flickypedia.celery worker --loglevel INFO
if os.path.basename(sys.argv[0]) == "celery":
    app = create_app()

    with app.app_context():
        celery = celery_init_app(app)
