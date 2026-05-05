from flask import Flask, jsonify, request
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import load_settings
from .db import init_app as init_db_app
from .routes.admin import admin
from .routes.public import public
from .services import configure_cloudinary, format_money


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_mapping(load_settings(test_config))
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    init_db_app(app)
    configure_cloudinary(app)
    app.jinja_env.filters["money"] = format_money

    app.register_blueprint(public)
    app.register_blueprint(admin)

    @app.errorhandler(RequestEntityTooLarge)
    def handle_file_too_large(_error):
        message = "Файл тым үлкен. JPG немесе PNG және 5MB-тан кіші файл жүктеңіз."
        if request.accept_mimetypes["application/json"] >= request.accept_mimetypes["text/html"]:
            return jsonify({"error": message}), 413
        return message, 413

    @app.get("/health")
    def healthcheck():
        return jsonify({"ok": True, "service": "autolux"})

    return app
