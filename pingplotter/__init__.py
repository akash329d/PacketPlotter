from flask import Flask
from .cache import cache
from .routes import routes
from .dataCollection import dataCollection


def pingplotter():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    cache.init_app(app)

    with app.app_context():
        app.register_blueprint(routes)
        app.register_blueprint(dataCollection)
        return app
