import sys

import click


@click.group()
def main() -> None:  # pragma: no cover
    pass


@main.command(help="Run a development version of the site")
@click.option(
    "--port", help="The port to bind to.", default=5000, type=int, show_default=True
)
@click.option(
    "--host",
    help="The interface to bind to.",
    default="127.0.0.1",
    type=click.Choice(["127.0.0.1", "0.0.0.0"]),
    show_default=True,
)
@click.option("--debug", help="Run the web app in debug mode.", is_flag=True)
def run_dev_server(port: int, host: str, debug: bool) -> None:
    from flickypedia.uploadr import create_app

    app = create_app(data_directory="data", debug=debug)

    if app.config["OAUTH2_PROVIDERS"]["wikimedia"]["client_id"] is None:
        sys.exit("No Wikimedia client ID provided! Set WIKIMEDIA_CLIENT_ID.")

    if app.config["OAUTH2_PROVIDERS"]["wikimedia"]["client_secret"] is None:
        sys.exit("No Wikimedia client secret provided! Set WIKIMEDIA_CLIENT_SECRET.")

    app.run(debug=debug, port=port, host=host)


@main.command(help="Run the Celery background worker.")
def run_celery_worker() -> None:
    from flickypedia.uploadr import create_app
    from flickypedia.uploadr.tasks import celery_init_app

    app = create_app()
    celery = celery_init_app(app)
    worker = celery.Worker()
    worker.start()
