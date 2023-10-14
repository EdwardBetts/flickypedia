from flask import Flask
from flask_executor import Executor
from flask_sqlalchemy import SQLAlchemy

from flickypedia.config import Config


app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

executor = Executor(app)

from flickypedia import auth  # noqa: E402, F401
from flickypedia import routes  # noqa: E402, F401
