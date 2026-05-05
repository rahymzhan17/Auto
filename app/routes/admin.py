from sqlalchemy.exc import SQLAlchemyError
from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from ..auth import (
    current_admin_username,
    is_admin_authenticated,
    login_required,
    login_user,
    logout_user,
    verify_credentials,
)
from ..db import db
from ..models import Car
from ..services import ValidationError, upload_image_to_cloudinary, validate_car_form


admin = Blueprint("admin", __name__)


def expects_json() -> bool:
    accept_json = request.accept_mimetypes["application/json"]
    accept_html = request.accept_mimetypes["text/html"]
    return request.headers.get("X-Requested-With") == "fetch" or accept_json >= accept_html


def render_admin_dashboard():
    cars = Car.query.order_by(Car.created_at.desc()).all()
    return render_template(
        "admin/index.html",
        admin_username=current_admin_username(),
        cars=cars,
        upload_endpoint=url_for("admin.upload_car"),
    )


@admin.get("/admin")
def admin_page():
    if not is_admin_authenticated():
        return render_template("admin/login.html")
    return render_admin_dashboard()


@admin.post("/admin/login")
def login():
    username = str(request.form.get("username", "")).strip()
    password = str(request.form.get("password", ""))

    if not verify_credentials(username, password):
        flash("Қате логин немесе пароль.", "error")
        return redirect(url_for("admin.admin_page"))

    login_user(username)
    flash("Админ панельге сәтті кірдіңіз.", "success")
    return redirect(url_for("admin.admin_page"))


@admin.post("/admin/logout")
@login_required
def logout():
    logout_user()
    flash("Сессия жабылды.", "success")
    return redirect(url_for("admin.admin_page"))


@admin.post("/upload")
@login_required
def upload_car():
    try:
        payload = validate_car_form(request.form)
        image_url = upload_image_to_cloudinary(request.files.get("image"))
        car = Car(
            name=payload["name"],
            price=payload["price"],
            image_url=image_url,
            description=payload["description"],
        )
        db.session.add(car)
        db.session.commit()
    except ValidationError as error:
        db.session.rollback()
        if expects_json():
            return jsonify({"error": str(error)}), 400
        flash(str(error), "error")
        return redirect(url_for("admin.admin_page"))
    except (RuntimeError, SQLAlchemyError) as error:
        db.session.rollback()
        if expects_json():
            return jsonify({"error": str(error)}), 500
        flash(str(error), "error")
        return redirect(url_for("admin.admin_page"))

    if expects_json():
        return jsonify({"ok": True, "secure_url": image_url, "car": car.to_dict()}), 201

    flash(f"{car.name} сәтті сақталды.", "success")
    return redirect(url_for("admin.admin_page"))


@admin.get("/api/admin/cars")
@login_required
def admin_cars():
    cars = Car.query.order_by(Car.created_at.desc()).all()
    return jsonify([car.to_dict() for car in cars])
