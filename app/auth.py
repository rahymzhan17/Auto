from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import current_app, g, jsonify, request
from werkzeug.security import check_password_hash

from .db import get_db


def verify_credentials(username, password):
    row = get_db().execute(
        "SELECT username, password FROM admins WHERE username=?",
        (username,),
    ).fetchone()
    if not row:
        return False
    return check_password_hash(row["password"], password)


def issue_token(username):
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=current_app.config["JWT_EXPIRES_HOURS"]
    )
    return jwt.encode(
        {"sub": username, "exp": expires_at},
        current_app.config["JWT_SECRET"],
        algorithm=current_app.config["JWT_ALGORITHM"],
    )


def require_auth(handler):
    @wraps(handler)
    def wrapped(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
        if not token:
            return jsonify({"error": "Токен табылмады"}), 401

        try:
            payload = jwt.decode(
                token,
                current_app.config["JWT_SECRET"],
                algorithms=[current_app.config["JWT_ALGORITHM"]],
            )
        except jwt.InvalidTokenError:
            return jsonify({"error": "Сессия мерзімі аяқталды"}), 401

        g.current_user = payload.get("sub")
        return handler(*args, **kwargs)

    return wrapped
