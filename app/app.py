import logging.config

from flask import Flask, jsonify
from flask_cors import CORS
from mongoengine import connect

import customerio  # noqa
from errors import register_errors
from routes import TokenConverter, load_blueprints
from sentry import setup_sentry

_ = customerio  # noqa - make pycharm happy


def create_app(environment: str = 'prod') -> Flask:
    app = Flask(__name__)
    CORS(app, resources={r"/v1/*": {"origins": "*"}})

    # Load default config files
    app.config.from_pyfile(f'config/__init__.py')
    app.config.from_pyfile(f'config/{environment}.py')

    # Setup app-wide logging
    logging.config.dictConfig(app.config['LOGGING'])
    logging.getLogger('root').setLevel(logging.DEBUG if app.config['DEBUG'] else logging.INFO)
    logging.getLogger('boto').setLevel(logging.CRITICAL)

    # Setup sentry error logging
    if not app.config['TESTING']:
        setup_sentry(app)

    # Connect DB
    connect('default', host=app.config['MONGODB_URI'])

    app.url_map.converters['token'] = TokenConverter

    register_errors(app)

    for blueprint in load_blueprints():
        app.register_blueprint(blueprint)

    @app.route('/v1/ping')
    def ping_route():
        return jsonify({'reply': 'pong'})

    return app
