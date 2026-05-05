from functools import wraps

from flask import current_app, flash, jsonify, redirect, request, session, url_for
from werkzeug.security import check_password_hash


def _expects_json() -> bool:
    accept_json = request.accept_mimetypes["application/json"]
    accept_html = request.accept_mimetypes["text/html"]
    return request.headers.get("X-Requested-With") == "fetch" or accept_json >= accept_html


def is_admin_authenticated() -> bool:
    return bool(session.get("admin_authenticated"))


def verify_credentials(username: str, password: str) -> bool:
    expected_username = current_app.config["ADMIN_USERNAME"]
    password_hash = current_app.config["ADMIN_PASSWORD_HASH"]
    if username != expected_username or not password_hash:
        return False
    return check_password_hash(password_hash, password)


def login_user(username: str) -> None:
    session.clear()
    session["admin_authenticated"] = True
    session["admin_username"] = username


def logout_user() -> None:
    session.clear()


def current_admin_username() -> str:
    return session.get("admin_username", current_app.config.get("ADMIN_USERNAME", "Admin"))


def login_required(handler):
    @wraps(handler)
    def wrapped(*args, **kwargs):
        if is_admin_authenticated():
            return handler(*args, **kwargs)

        if _expects_json():
            return jsonify({"error": "Авторизация қажет"}), 401

        flash("Алдымен админ панельге кіріңіз.", "error")
        return redirect(url_for("admin.admin_page"))

    return wrapped
