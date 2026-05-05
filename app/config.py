import os
from pathlib import Path

from werkzeug.security import generate_password_hash


BASE_DIR = Path(__file__).resolve().parent.parent


def load_env(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key:
            os.environ.setdefault(key, value)


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name, "").strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "on"}


def normalize_database_url(value: str) -> str:
    url = str(value or "").strip()
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://") :]
    return url


def load_settings(overrides=None):
    load_env(BASE_DIR / ".env")

    overrides = overrides or {}
    testing = bool(overrides.get("TESTING", False))

    database_url = normalize_database_url(
        overrides.get("DATABASE_URL") or os.getenv("DATABASE_URL", "")
    )
    if not database_url and testing:
        database_url = "sqlite:///:memory:"

    admin_username = str(overrides.get("ADMIN_USERNAME") or os.getenv("ADMIN_USERNAME", "")).strip()
    admin_password = str(overrides.get("ADMIN_PASSWORD") or os.getenv("ADMIN_PASSWORD", ""))
    admin_password_hash = str(
        overrides.get("ADMIN_PASSWORD_HASH") or os.getenv("ADMIN_PASSWORD_HASH", "")
    ).strip()
    if not admin_password_hash and admin_password:
        admin_password_hash = generate_password_hash(admin_password)

    settings = {
        "BASE_DIR": BASE_DIR,
        "SECRET_KEY": str(overrides.get("SECRET_KEY") or os.getenv("SECRET_KEY", "")).strip(),
        "DATABASE_URL": database_url,
        "SQLALCHEMY_DATABASE_URI": overrides.get("SQLALCHEMY_DATABASE_URI") or database_url,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_ENGINE_OPTIONS": {"pool_pre_ping": True},
        "ADMIN_USERNAME": admin_username,
        "ADMIN_PASSWORD_HASH": admin_password_hash,
        "CLOUD_NAME": str(overrides.get("CLOUD_NAME") or os.getenv("CLOUD_NAME", "")).strip(),
        "API_KEY": str(overrides.get("API_KEY") or os.getenv("API_KEY", "")).strip(),
        "API_SECRET": str(overrides.get("API_SECRET") or os.getenv("API_SECRET", "")).strip(),
        "CLOUDINARY_FOLDER": str(
            overrides.get("CLOUDINARY_FOLDER") or os.getenv("CLOUDINARY_FOLDER", "autolux")
        ).strip(),
        "MAX_CONTENT_LENGTH": int(
            overrides.get("MAX_CONTENT_LENGTH") or os.getenv("MAX_CONTENT_LENGTH", str(5 * 1024 * 1024))
        ),
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "SESSION_COOKIE_SECURE": bool(
            overrides.get("SESSION_COOKIE_SECURE", not testing and env_bool("SESSION_COOKIE_SECURE", True))
        ),
        "PREFERRED_URL_SCHEME": "https",
        "TESTING": testing,
    }

    if overrides:
        settings.update(overrides)
        if "DATABASE_URL" in overrides:
            normalized_override = normalize_database_url(overrides["DATABASE_URL"])
            settings["DATABASE_URL"] = normalized_override
            settings["SQLALCHEMY_DATABASE_URI"] = normalized_override

    missing = []
    if not settings.get("SECRET_KEY"):
        missing.append("SECRET_KEY")
    if not settings.get("SQLALCHEMY_DATABASE_URI"):
        missing.append("DATABASE_URL")
    if not settings.get("ADMIN_USERNAME"):
        missing.append("ADMIN_USERNAME")
    if not settings.get("ADMIN_PASSWORD_HASH"):
        missing.append("ADMIN_PASSWORD or ADMIN_PASSWORD_HASH")
    if not settings.get("CLOUD_NAME"):
        missing.append("CLOUD_NAME")
    if not settings.get("API_KEY"):
        missing.append("API_KEY")
    if not settings.get("API_SECRET"):
        missing.append("API_SECRET")

    if missing and not settings.get("TESTING"):
        raise RuntimeError(f"Missing required environment values: {', '.join(missing)}")

    return settings
