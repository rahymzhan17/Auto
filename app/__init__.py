from flask import Flask, jsonify

from .config import load_settings
from .db import init_app as init_db_app
from .routes.admin import admin_api
from .routes.public import public


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_mapping(load_settings(test_config))

    init_db_app(app)

    app.register_blueprint(public)
    app.register_blueprint(admin_api)

    @app.get("/health")
    def healthcheck():
        return jsonify({"ok": True, "service": "autolux"})

    return app
