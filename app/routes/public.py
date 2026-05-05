from pathlib import Path

from flask import Blueprint, current_app, jsonify, render_template, request, send_from_directory

from ..db import fetch_active_cars, get_db
from ..services import serialize_car, validate_contact_payload, validate_testdrive_payload
from ..utils import ValidationError, json_error


public = Blueprint("public", __name__)


@public.get("/")
def homepage():
    return render_template("public/index.html")


@public.get("/admin")
def admin_page():
    return render_template("admin/index.html")


@public.get("/api/cars")
def cars():
    return jsonify(fetch_active_cars())


@public.get("/api/cars/<int:car_id>")
def car_detail(car_id):
    row = get_db().execute(
        "SELECT * FROM cars WHERE id=? AND is_active=1",
        (car_id,),
    ).fetchone()
    if not row:
        return json_error("Табылмады", 404)
    return jsonify(serialize_car(row))


@public.post("/api/testdrive")
def create_testdrive():
    try:
        payload = validate_testdrive_payload(request.get_json(silent=True))
    except ValidationError as error:
        return json_error(str(error), 400)

    get_db().execute(
        "INSERT INTO testdrives(name, phone, car) VALUES(?,?,?)",
        (payload["name"], payload["phone"], payload["car"]),
    )
    get_db().commit()
    return jsonify({"ok": True, "message": "Тест-драйвке өтінім қабылданды"})


@public.post("/api/contact")
def create_contact():
    try:
        payload = validate_contact_payload(request.get_json(silent=True))
    except ValidationError as error:
        return json_error(str(error), 400)

    get_db().execute(
        "INSERT INTO contacts(name, phone, car, msg) VALUES(?,?,?,?)",
        (payload["name"], payload["phone"], payload["car"], payload["message"]),
    )
    get_db().commit()
    return jsonify({"ok": True, "message": "Хабарламаңыз қабылданды"})


@public.get("/uploads/<path:filename>")
def uploads(filename):
    upload_dir = Path(current_app.config["UPLOAD_DIR"])
    return send_from_directory(upload_dir, filename)
