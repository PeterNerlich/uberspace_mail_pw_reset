from flask import Flask
from flask_babel import Babel
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()
babel = Babel()

import app.models as models

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY')
    app.url_map.strict_slashes = False

    app.config['PREFERRED_URL_SCHEME'] = os.getenv('PREFERRED_URL_SCHEME')
    app.config['SERVER_NAME'] = os.getenv('SERVER_NAME')
    app.config['APPLICATION_ROOT'] = os.getenv('APP_ROOT')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')

    babel.init_app(app)

    db.init_app(app)
    with app.app_context():
        db.create_all()
        db.session.commit()

    from .public import public as public_blueprint
    app.register_blueprint(public_blueprint)

    return app
