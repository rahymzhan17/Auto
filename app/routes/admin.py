from pathlib import Path

from flask import Blueprint, current_app, jsonify, request

from ..auth import issue_token, require_auth, verify_credentials
from ..db import fetch_admin_cars, get_db
from ..services import serialize_car, validate_car_payload, validate_status_payload
from ..utils import (
    ValidationError,
    decode_base64_image,
    download_image_from_url,
    dump_json,
    json_error,
    new_upload_filename,
)


admin_api = Blueprint("admin_api", __name__)


@admin_api.post("/api/login")
def login():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))

    if not username or not password:
        return json_error("Логин мен парольді толтырыңыз", 400)
    if not verify_credentials(username, password):
        return json_error("Қате логин немесе пароль", 401)

    token = issue_token(username)
    return jsonify({"token": token, "username": username})


@admin_api.get("/api/admin/cars")
@require_auth
def admin_cars():
    return jsonify(fetch_admin_cars())


@admin_api.get("/api/admin/cars/<int:car_id>")
@require_auth
def admin_car_detail(car_id):
    row = get_db().execute("SELECT * FROM cars WHERE id=?", (car_id,)).fetchone()
    if not row:
        return json_error("Табылмады", 404)
    return jsonify(serialize_car(row))


@admin_api.post("/api/admin/cars")
@require_auth
def create_car():
    try:
        payload = validate_car_payload(request.get_json(silent=True))
    except ValidationError as error:
        return json_error(str(error), 400)

    cursor = get_db().execute(
        """
        INSERT INTO cars(
            brand, name, type, tag, price, full_price, monthly_price,
            engine, speed, drive, fuel, tagline, photos, features, is_active
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            payload["brand"],
            payload["name"],
            payload["type"],
            payload["tag"],
            payload["price"],
            payload["full_price"],
            payload["monthly_price"],
            payload["engine"],
            payload["speed"],
            payload["drive"],
            payload["fuel"],
            payload["tagline"],
            dump_json(payload["photos"]),
            dump_json(payload["features"]),
            payload["is_active"],
        ),
    )
    get_db().commit()

    row = get_db().execute("SELECT * FROM cars WHERE id=?", (cursor.lastrowid,)).fetchone()
    return jsonify({"ok": True, "car": serialize_car(row)})


@admin_api.put("/api/admin/cars/<int:car_id>")
@require_auth
def update_car(car_id):
    row = get_db().execute("SELECT id FROM cars WHERE id=?", (car_id,)).fetchone()
    if not row:
        return json_error("Табылмады", 404)

    try:
        payload = validate_car_payload(request.get_json(silent=True))
    except ValidationError as error:
        return json_error(str(error), 400)

    get_db().execute(
        """
        UPDATE cars
        SET brand=?, name=?, type=?, tag=?, price=?, full_price=?, monthly_price=?,
            engine=?, speed=?, drive=?, fuel=?, tagline=?, photos=?, features=?, is_active=?
        WHERE id=?
        """,
        (
            payload["brand"],
            payload["name"],
            payload["type"],
            payload["tag"],
            payload["price"],
            payload["full_price"],
            payload["monthly_price"],
            payload["engine"],
            payload["speed"],
            payload["drive"],
            payload["fuel"],
            payload["tagline"],
            dump_json(payload["photos"]),
            dump_json(payload["features"]),
            payload["is_active"],
            car_id,
        ),
    )
    get_db().commit()

    updated = get_db().execute("SELECT * FROM cars WHERE id=?", (car_id,)).fetchone()
    return jsonify({"ok": True, "car": serialize_car(updated)})


@admin_api.delete("/api/admin/cars/<int:car_id>")
@require_auth
def delete_car(car_id):
    cursor = get_db().execute("DELETE FROM cars WHERE id=?", (car_id,))
    get_db().commit()
    if cursor.rowcount == 0:
        return json_error("Табылмады", 404)
    return jsonify({"ok": True})


@admin_api.get("/api/admin/testdrives")
@require_auth
def list_testdrives():
    rows = get_db().execute(
        "SELECT * FROM testdrives ORDER BY created DESC, id DESC"
    ).fetchall()
    return jsonify([dict(row) for row in rows])


@admin_api.patch("/api/admin/testdrives/<int:testdrive_id>")
@require_auth
def update_testdrive_status(testdrive_id):
    try:
        status = validate_status_payload(request.get_json(silent=True))
    except ValidationError as error:
        return json_error(str(error), 400)

    cursor = get_db().execute(
        "UPDATE testdrives SET status=? WHERE id=?",
        (status, testdrive_id),
    )
    get_db().commit()
    if cursor.rowcount == 0:
        return json_error("Табылмады", 404)
    return jsonify({"ok": True})


@admin_api.delete("/api/admin/testdrives/<int:testdrive_id>")
@require_auth
def delete_testdrive(testdrive_id):
    cursor = get_db().execute("DELETE FROM testdrives WHERE id=?", (testdrive_id,))
    get_db().commit()
    if cursor.rowcount == 0:
        return json_error("Табылмады", 404)
    return jsonify({"ok": True})


@admin_api.get("/api/admin/contacts")
@require_auth
def list_contacts():
    rows = get_db().execute("SELECT * FROM contacts ORDER BY created DESC, id DESC").fetchall()
    return jsonify([dict(row) for row in rows])


@admin_api.get("/api/admin/stats")
@require_auth
def stats():
    connection = get_db()
    read_scalar = lambda query: connection.execute(query).fetchone()[0]
    return jsonify(
        {
            "td_total": read_scalar("SELECT COUNT(*) FROM testdrives"),
            "td_new": read_scalar("SELECT COUNT(*) FROM testdrives WHERE status='new'"),
            "cars": read_scalar("SELECT COUNT(*) FROM cars WHERE is_active=1"),
            "contacts": read_scalar("SELECT COUNT(*) FROM contacts"),
        }
    )


@admin_api.post("/api/admin/upload")
@require_auth
def upload():
    payload = request.get_json(silent=True) or {}

    try:
        image_bytes = decode_base64_image(payload.get("image"))
        filename = new_upload_filename(payload.get("ext", "jpg"))
    except ValidationError as error:
        return json_error(str(error), 400)

    if len(image_bytes) > current_app.config["MAX_IMAGE_BYTES"]:
        return json_error("Сурет тым үлкен", 400)

    destination = Path(current_app.config["UPLOAD_DIR"]) / filename
    destination.write_bytes(image_bytes)
    return jsonify({"ok": True, "url": f"/uploads/{filename}"})


@admin_api.post("/api/admin/upload-url")
@require_auth
def upload_from_url():
    payload = request.get_json(silent=True) or {}

    try:
        result = download_image_from_url(
            payload.get("url"),
            max_bytes=current_app.config["MAX_IMAGE_BYTES"],
        )
    except ValidationError as error:
        return json_error(str(error), 400)

    if result["url"]:
        return jsonify({"ok": True, "url": result["url"]})

    destination = Path(current_app.config["UPLOAD_DIR"]) / result["filename"]
    destination.write_bytes(result["bytes"])
    return jsonify({"ok": True, "url": f"/uploads/{result['filename']}"})
