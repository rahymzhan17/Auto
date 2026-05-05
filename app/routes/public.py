from pathlib import Path

from flask import Blueprint, current_app, jsonify, render_template, send_from_directory

from ..models import Car


public = Blueprint("public", __name__)


@public.get("/")
def homepage():
    cars = Car.query.order_by(Car.created_at.desc()).all()
    return render_template("public/index.html", cars=cars)


@public.get("/logo.png")
def logo():
    project_root = Path(current_app.root_path).parent
    return send_from_directory(project_root, "logo.png")


@public.get("/api/cars")
def cars_api():
    cars = Car.query.order_by(Car.created_at.desc()).all()
    return jsonify([car.to_dict() for car in cars])
