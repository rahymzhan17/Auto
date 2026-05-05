import os
from pathlib import Path


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


def load_settings(overrides=None):
    load_env(BASE_DIR / ".env")

    default_data_dir = BASE_DIR / "data"
    default_storage_dir = BASE_DIR / "storage"
    default_upload_dir = default_storage_dir / "uploads"
    default_database_path = default_data_dir / "autolux.db"

    data_dir = Path(os.getenv("DATA_DIR", str(default_data_dir)))
    storage_dir = Path(os.getenv("STORAGE_DIR", str(default_storage_dir)))
    upload_dir = Path(os.getenv("UPLOAD_DIR", str(storage_dir / "uploads")))
    database_path = Path(os.getenv("DATABASE_PATH", str(data_dir / "autolux.db")))

    settings = {
        "BASE_DIR": BASE_DIR,
        "DATA_DIR": data_dir,
        "STORAGE_DIR": storage_dir,
        "UPLOAD_DIR": upload_dir,
        "DATABASE_PATH": database_path,
        "JWT_SECRET": os.getenv("JWT_SECRET", "").strip(),
        "JWT_ALGORITHM": "HS256",
        "JWT_EXPIRES_HOURS": int(os.getenv("JWT_EXPIRES_HOURS", "24")),
        "ADMIN_USERNAME": os.getenv("ADMIN_USERNAME", "").strip(),
        "ADMIN_PASSWORD": os.getenv("ADMIN_PASSWORD", ""),
        "ADMIN_PASSWORD_HASH": os.getenv("ADMIN_PASSWORD_HASH", "").strip(),
        "MAX_CONTENT_LENGTH": int(os.getenv("MAX_CONTENT_LENGTH", str(8 * 1024 * 1024))),
        "MAX_IMAGE_BYTES": int(os.getenv("MAX_IMAGE_BYTES", str(5 * 1024 * 1024))),
        "TESTING": False,
    }

    if overrides:
        settings.update(overrides)

    settings["DATA_DIR"].mkdir(parents=True, exist_ok=True)
    settings["STORAGE_DIR"].mkdir(parents=True, exist_ok=True)
    settings["UPLOAD_DIR"].mkdir(parents=True, exist_ok=True)

    missing = []
    if not settings.get("JWT_SECRET"):
        missing.append("JWT_SECRET")
    elif len(settings["JWT_SECRET"]) < 32:
        raise RuntimeError("JWT_SECRET must be at least 32 characters long")
    if not settings.get("ADMIN_USERNAME"):
        missing.append("ADMIN_USERNAME")
    if not (settings.get("ADMIN_PASSWORD") or settings.get("ADMIN_PASSWORD_HASH")):
        missing.append("ADMIN_PASSWORD or ADMIN_PASSWORD_HASH")

    if missing and not settings.get("TESTING"):
        joined = ", ".join(missing)
        raise RuntimeError(f"Missing required environment values: {joined}")

    return settings
