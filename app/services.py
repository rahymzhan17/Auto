import re
from pathlib import Path
from decimal import Decimal, InvalidOperation

import cloudinary
import cloudinary.uploader
from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png"}
ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/jpg"}
PRICE_PATTERN = re.compile(r"[^\d,.\s]")


class ValidationError(ValueError):
    pass


def configure_cloudinary(app) -> None:
    cloudinary.config(
        cloud_name=app.config["CLOUD_NAME"],
        api_key=app.config["API_KEY"],
        api_secret=app.config["API_SECRET"],
        secure=True,
    )


def clean_text(value, *, field_name: str, max_length: int, allow_blank: bool = False) -> str:
    cleaned = str(value or "").strip()
    if not cleaned and not allow_blank:
        raise ValidationError(f"{field_name} міндетті")
    if len(cleaned) > max_length:
        raise ValidationError(f"{field_name} тым ұзын")
    return cleaned


def parse_price(value) -> Decimal:
    raw_value = clean_text(value, field_name="Баға", max_length=32)
    normalized = PRICE_PATTERN.sub("", raw_value).replace(" ", "").replace(",", ".")
    if normalized.count(".") > 1:
        raise ValidationError("Баға форматы жарамсыз")

    try:
        price = Decimal(normalized)
    except InvalidOperation as error:
        raise ValidationError("Баға сан болуы керек") from error

    if price <= 0:
        raise ValidationError("Баға нөлден үлкен болуы керек")
    return price.quantize(Decimal("0.01"))


def validate_car_form(form):
    return {
        "name": clean_text(form.get("name"), field_name="Модель атауы", max_length=160),
        "price": parse_price(form.get("price")),
        "description": clean_text(
            form.get("description"),
            field_name="Сипаттама",
            max_length=2000,
        ),
    }


def validate_image_file(file_storage: FileStorage | None) -> str:
    if file_storage is None or not file_storage.filename:
        raise ValidationError("Фото таңдалмады")

    filename = secure_filename(file_storage.filename)
    if "." not in filename:
        raise ValidationError("Файл кеңейтімі табылмады")

    extension = filename.rsplit(".", 1)[1].lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError("Тек JPG және PNG файлдарына рұқсат бар")

    if (file_storage.mimetype or "").lower() not in ALLOWED_IMAGE_MIME_TYPES:
        raise ValidationError("Файл түрі жарамсыз")

    return filename


def upload_image_to_cloudinary(file_storage: FileStorage | None) -> str:
    filename = validate_image_file(file_storage)
    file_storage.stream.seek(0)

    try:
        result = cloudinary.uploader.upload(
            file_storage.stream,
            folder=current_app.config["CLOUDINARY_FOLDER"],
            resource_type="image",
            public_id=Path(filename).stem,
            use_filename=True,
            unique_filename=True,
            overwrite=False,
        )
    except Exception as error:  # pragma: no cover - Cloudinary internals are external
        raise RuntimeError("Cloudinary-ге жүктеу сәтсіз аяқталды") from error

    secure_url = str(result.get("secure_url", "")).strip()
    if not secure_url:
        raise RuntimeError("Cloudinary secure_url қайтармады")
    return secure_url


def format_money(value) -> str:
    amount = Decimal(value or 0).quantize(Decimal("0.01"))
    if amount == amount.to_integral():
        return f"{int(amount):,}".replace(",", " ")

    formatted = f"{amount:,.2f}"
    return formatted.replace(",", " ").replace(".", ",")
