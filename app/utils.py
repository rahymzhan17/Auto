import base64
import ipaddress
import json
import re
import socket
import uuid
from pathlib import PurePosixPath
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from flask import jsonify


DEFAULT_CAR_IMAGE = "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=900&q=80"
ALLOWED_CAR_TYPES = {"sedan", "suv", "sport", "other"}
ALLOWED_TESTDRIVE_STATUSES = {"new", "confirmed", "done", "cancelled"}
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
CONTENT_TYPE_TO_EXTENSION = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
PRICE_PATTERN = re.compile(r"^[0-9 ]{1,20}$")
PHONE_PATTERN = re.compile(r"^[0-9+\-() ]{7,25}$")


class ValidationError(ValueError):
    pass


def json_error(message, status=400):
    return jsonify({"error": message}), status


def parse_json_list(raw):
    if isinstance(raw, list):
        return raw
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return []
    return value if isinstance(value, list) else []


def dump_json(value):
    return json.dumps(value, ensure_ascii=False)


def clean_text(value, *, max_length=255, allow_blank=False):
    cleaned = str(value or "").strip()
    if not allow_blank and not cleaned:
        raise ValidationError("Міндетті өріс толтырылмады")
    if len(cleaned) > max_length:
        raise ValidationError("Мәтін тым ұзын")
    return cleaned


def clean_optional_text(value, *, max_length=255):
    cleaned = str(value or "").strip()
    if len(cleaned) > max_length:
        raise ValidationError("Мәтін тым ұзын")
    return cleaned


def clean_phone(value):
    phone = clean_text(value, max_length=25)
    if not PHONE_PATTERN.match(phone):
        raise ValidationError("Телефон нөмірі жарамсыз")
    return phone


def clean_price(value, *, required=True):
    text = clean_optional_text(value, max_length=20)
    if not text and not required:
        return ""
    if not text:
        raise ValidationError("Баға міндетті")
    if not PRICE_PATTERN.match(text):
        raise ValidationError("Баға тек сандар мен бос орындардан тұруы керек")
    return re.sub(r"\s+", " ", text).strip()


def clean_choice(value, allowed, *, default=None):
    cleaned = clean_optional_text(value, max_length=30).lower()
    if not cleaned and default is not None:
        return default
    if cleaned not in allowed:
        raise ValidationError("Таңдалған мән жарамсыз")
    return cleaned


def is_safe_url(value):
    if not value:
        return False
    if value.startswith("/uploads/"):
        return True
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def clean_url(value):
    cleaned = clean_optional_text(value, max_length=1000)
    if not cleaned:
        return ""
    if not is_safe_url(cleaned):
        raise ValidationError("Сурет сілтемесі жарамсыз")
    return cleaned


def clean_string_list(values, *, item_limit=20, item_length=120):
    if values is None:
        return []
    if not isinstance(values, list):
        raise ValidationError("Тізім форматы дұрыс емес")

    cleaned = []
    for raw in values[:item_limit]:
        item = clean_optional_text(raw, max_length=item_length)
        if item:
            cleaned.append(item)
    return cleaned


def clean_photo_list(values):
    if values is None:
        return []
    if not isinstance(values, list):
        raise ValidationError("Фото тізімі дұрыс емес")

    cleaned = []
    for raw in values[:10]:
        url = clean_url(raw)
        if url:
            cleaned.append(url)
    return cleaned


def decode_base64_image(raw_value):
    value = str(raw_value or "").strip()
    if not value:
        raise ValidationError("Сурет дерегі жіберілмеді")
    if "," in value:
        value = value.split(",", 1)[1]
    try:
        return base64.b64decode(value, validate=True)
    except (ValueError, TypeError):
        raise ValidationError("Сурет форматы бұзылған")


def ensure_public_image_host(value):
    parsed = urlparse(value)
    hostname = (parsed.hostname or "").strip().lower()
    if not hostname:
        raise ValidationError("Сурет сілтемесінің домені табылмады")

    try:
        addresses = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise ValidationError("Сурет сілтемесінің домені табылмады")

    for item in addresses:
        address = item[4][0]
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            continue
        if any(
            (
                ip.is_private,
                ip.is_loopback,
                ip.is_link_local,
                ip.is_reserved,
                ip.is_multicast,
                ip.is_unspecified,
            )
        ):
            raise ValidationError("Ішкі желідегі сурет сілтемесіне рұқсат жоқ")


def guess_remote_image_extension(url, content_type):
    cleaned_type = clean_optional_text(content_type, max_length=120).split(";", 1)[0].strip().lower()
    if cleaned_type in CONTENT_TYPE_TO_EXTENSION:
        return CONTENT_TYPE_TO_EXTENSION[cleaned_type]

    suffix = PurePosixPath(urlparse(url).path).suffix.lower().lstrip(".")
    if suffix in ALLOWED_IMAGE_EXTENSIONS:
        return suffix
    return ""


def download_image_from_url(raw_value, *, max_bytes, timeout=10):
    url = clean_url(raw_value)
    if not url:
        raise ValidationError("Сурет сілтемесі жарамсыз")
    if url.startswith("/uploads/"):
        return {"url": url, "bytes": b"", "filename": ""}

    ensure_public_image_host(url)

    request = Request(url, headers={"User-Agent": "AutoLux/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            extension = guess_remote_image_extension(url, content_type)
            if not extension:
                raise ValidationError("Сілтеме тікелей JPG, PNG немесе WEBP суретіне апаруы керек")

            declared_size = response.headers.get("Content-Length")
            if declared_size and declared_size.isdigit() and int(declared_size) > max_bytes:
                raise ValidationError("Сурет тым үлкен")

            chunks = []
            total_size = 0
            while True:
                chunk = response.read(64 * 1024)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > max_bytes:
                    raise ValidationError("Сурет тым үлкен")
                chunks.append(chunk)
    except ValidationError:
        raise
    except (HTTPError, URLError, TimeoutError, OSError):
        raise ValidationError("Сурет сілтемесін жүктеу мүмкін болмады")

    return {
        "url": "",
        "bytes": b"".join(chunks),
        "filename": new_upload_filename(extension),
    }


def new_upload_filename(extension):
    ext = clean_optional_text(extension, max_length=10).lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError("Қолдау жоқ файл түрі")
    return f"{uuid.uuid4().hex}.{ext}"


def format_down_payment(full_price):
    digits = re.sub(r"\D", "", str(full_price or ""))
    if not digits:
        return "0"
    return f"{int(digits) // 5:,}".replace(",", " ")
