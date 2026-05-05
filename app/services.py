from .utils import (
    ALLOWED_CAR_TYPES,
    DEFAULT_CAR_IMAGE,
    ValidationError,
    clean_choice,
    clean_optional_text,
    clean_phone,
    clean_photo_list,
    clean_price,
    clean_string_list,
    clean_text,
    format_down_payment,
    parse_json_list,
)


def parse_active_flag(value, fallback=1):
    if value in (None, ""):
        return fallback
    if isinstance(value, bool):
        return 1 if value else 0
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return 1
    if text in {"0", "false", "no", "off"}:
        return 0
    raise ValidationError("Белсенділік мәні жарамсыз")


def serialize_car(row):
    data = dict(row)
    photos = parse_json_list(data.get("photos")) or [DEFAULT_CAR_IMAGE]
    features = parse_json_list(data.get("features"))
    down_payment = format_down_payment(data.get("full_price"))

    return {
        "id": data["id"],
        "brand": data["brand"],
        "name": data["name"],
        "type": data.get("type", "sedan"),
        "tag": data.get("tag", "ЖАҢА"),
        "price": data.get("price", ""),
        "fullPrice": data.get("full_price", ""),
        "monthlyPrice": data.get("monthly_price", ""),
        "engine": data.get("engine", ""),
        "speed": data.get("speed", ""),
        "drive": data.get("drive", ""),
        "fuel": data.get("fuel", ""),
        "tagline": data.get("tagline", ""),
        "photos": photos,
        "features": features,
        "active": data.get("is_active", 1),
        "created": data.get("created", ""),
        "fullSpecs": [
            {"k": "engine", "l": "Қозғалтқыш", "v": data.get("engine", "—")},
            {"k": "speed", "l": "0–100 км/с", "v": data.get("speed", "—")},
            {"k": "fuel", "l": "Отын", "v": data.get("fuel", "—")},
            {"k": "drive", "l": "Жетек жүйесі", "v": data.get("drive", "—")},
            {"k": "seats", "l": "Орын саны", "v": "5"},
            {"k": "year", "l": "Жыл", "v": "2024"},
        ],
        "credit": [
            {"l": "Автомобиль бағасы", "v": f'{data.get("full_price", "")} ₸'.strip()},
            {"l": "Бастапқы жарна (20%)", "v": f"{down_payment} ₸"},
            {"l": "Кредит мерзімі", "v": "60 ай"},
            {"l": "Ай сайынғы төлем", "v": f'{data.get("monthly_price", "") or "—"} ₸'},
            {"l": "Пайыздық мөлшерлеме", "v": "9.9% жылдық"},
        ],
    }


def validate_car_payload(payload):
    data = payload or {}

    brand = clean_text(data.get("brand"), max_length=80)
    name = clean_text(data.get("name"), max_length=80)
    price = clean_price(data.get("price"))
    full_price = clean_price(data.get("full_price") or price)
    monthly_price = clean_price(data.get("monthly_price"), required=False)

    return {
        "brand": brand,
        "name": name,
        "type": clean_choice(data.get("type"), ALLOWED_CAR_TYPES, default="sedan"),
        "tag": clean_optional_text(data.get("tag"), max_length=30) or "ЖАҢА",
        "price": price,
        "full_price": full_price,
        "monthly_price": monthly_price,
        "engine": clean_optional_text(data.get("engine"), max_length=60),
        "speed": clean_optional_text(data.get("speed"), max_length=40),
        "drive": clean_optional_text(data.get("drive"), max_length=40),
        "fuel": clean_optional_text(data.get("fuel"), max_length=40),
        "tagline": clean_optional_text(data.get("tagline"), max_length=240),
        "photos": clean_photo_list(data.get("photos")),
        "features": clean_string_list(data.get("features"), item_limit=20, item_length=80),
        "is_active": parse_active_flag(data.get("is_active", data.get("active", 1))),
    }


def validate_contact_payload(payload):
    data = payload or {}
    return {
        "name": clean_text(data.get("name"), max_length=80),
        "phone": clean_phone(data.get("phone")),
        "car": clean_optional_text(data.get("car"), max_length=80),
        "message": clean_optional_text(data.get("message"), max_length=500),
    }


def validate_testdrive_payload(payload):
    data = payload or {}
    return {
        "name": clean_text(data.get("name"), max_length=80),
        "phone": clean_phone(data.get("phone")),
        "car": clean_optional_text(data.get("car"), max_length=80),
    }


def validate_status_payload(payload):
    data = payload or {}
    status = clean_optional_text(data.get("status"), max_length=20).lower()
    if status not in {"new", "confirmed", "done", "cancelled"}:
        raise ValidationError("Күй мәні жарамсыз")
    return status
