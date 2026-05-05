import sqlite3

from flask import current_app, g
from werkzeug.security import generate_password_hash

from .services import serialize_car
from .utils import dump_json


DEMO_CARS = [
    (
        "BMW",
        "5 Series",
        "sedan",
        "ХИТ",
        "28 500 000",
        "28 500 000",
        "339 000",
        "3.0T 340 а.к.",
        "5.1 сек",
        "xDrive AWD",
        "Бензин",
        "Жоғары өнімді дизайн мен технологияның үйлесімі.",
        dump_json(["https://images.unsplash.com/photo-1555215695-3004980ad54e?w=900&q=80"]),
        dump_json(["Panoramic roof", "Harman Kardon audio", "Lane assist", "Parking Plus"]),
    ),
    (
        "Mercedes-Benz",
        "GLE 350",
        "suv",
        "ПРЕМИУМ",
        "52 000 000",
        "52 000 000",
        "619 000",
        "2.0T 258 а.к.",
        "7.1 сек",
        "4MATIC AWD",
        "Бензин",
        "Класс пен қозғалыстың кемел тепе-теңдігі.",
        dump_json(["https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?w=900&q=80"]),
        dump_json(["MBUX Display", "Burmester Audio", "Active Brake", "360 Camera"]),
    ),
    (
        "Porsche",
        "Cayenne S",
        "suv",
        "СПОРТ",
        "78 000 000",
        "78 000 000",
        "929 000",
        "2.9T 440 а.к.",
        "4.9 сек",
        "AWD",
        "Бензин",
        "Спорттық рухты SUV-дің ең биік шыңы.",
        dump_json(["https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=900&q=80"]),
        dump_json(["Sport Chrono", "BOSE Surround", "Air Suspension", "Night Vision"]),
    ),
    (
        "Audi",
        "Q7",
        "suv",
        "ЖАҢА",
        "65 000 000",
        "65 000 000",
        "774 000",
        "3.0T 340 а.к.",
        "5.9 сек",
        "quattro AWD",
        "Бензин",
        "Кеңістік пен қуаттың мінсіз үйлесімі.",
        dump_json(["https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=900&q=80"]),
        dump_json(["Virtual Cockpit", "Bang & Olufsen", "Matrix LED", "Adaptive cruise"]),
    ),
    (
        "Toyota",
        "Land Cruiser 300",
        "suv",
        "БЕСТСЕЛЛЕР",
        "85 000 000",
        "85 000 000",
        "1 012 000",
        "3.5T 415 а.к.",
        "6.7 сек",
        "Full-time 4WD",
        "Бензин",
        "Жол таңдамайтын аңыздың жаңа буыны.",
        dump_json(["https://images.unsplash.com/photo-1559416523-140ddc3d238c?w=900&q=80"]),
        dump_json(["E-KDSS", "Multi-terrain", "14 дисплей", "Driver assist"]),
    ),
    (
        "Lexus",
        "RX 500h",
        "suv",
        "ГИБРИД",
        "55 500 000",
        "55 500 000",
        "661 000",
        "2.4T+Электро",
        "5.4 сек",
        "E-Four AWD",
        "Гибрид",
        "Премиум гибридті технологияның шыңы.",
        dump_json(["https://images.unsplash.com/photo-1549399542-7e3f8b79c341?w=900&q=80"]),
        dump_json(["Mark Levinson", "Digital Mirror", "HUD", "Wireless зарядтау"]),
    ),
]


def get_db():
    if "db" not in g:
        connection = sqlite3.connect(current_app.config["DATABASE_PATH"])
        connection.row_factory = sqlite3.Row
        g.db = connection
    return g.db


def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_app(app):
    app.teardown_appcontext(close_db)

    with app.app_context():
        initialize_database()


def initialize_database():
    connection = get_db()
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS admins(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS cars(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            name TEXT NOT NULL,
            type TEXT DEFAULT 'sedan',
            tag TEXT DEFAULT 'ЖАҢА',
            price TEXT NOT NULL,
            full_price TEXT NOT NULL,
            monthly_price TEXT DEFAULT '',
            engine TEXT DEFAULT '',
            speed TEXT DEFAULT '',
            drive TEXT DEFAULT '',
            fuel TEXT DEFAULT '',
            tagline TEXT DEFAULT '',
            photos TEXT DEFAULT '[]',
            features TEXT DEFAULT '[]',
            is_active INTEGER DEFAULT 1,
            created TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS testdrives(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            car TEXT DEFAULT '',
            status TEXT DEFAULT 'new',
            created TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS contacts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            car TEXT DEFAULT '',
            msg TEXT DEFAULT '',
            created TEXT DEFAULT (datetime('now','localtime'))
        );
        """
    )

    seed_demo_data(connection)
    sync_admin_account(connection)
    connection.commit()


def seed_demo_data(connection):
    total = connection.execute("SELECT COUNT(*) FROM cars").fetchone()[0]
    if total:
        return

    connection.executemany(
        """
        INSERT INTO cars(
            brand, name, type, tag, price, full_price, monthly_price,
            engine, speed, drive, fuel, tagline, photos, features
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        DEMO_CARS,
    )


def sync_admin_account(connection):
    username = current_app.config["ADMIN_USERNAME"]
    password_hash = current_app.config.get("ADMIN_PASSWORD_HASH")

    if not password_hash:
        password_hash = generate_password_hash(current_app.config["ADMIN_PASSWORD"])

    row = connection.execute("SELECT id FROM admins WHERE username=?", (username,)).fetchone()
    if row:
        connection.execute("UPDATE admins SET password=? WHERE id=?", (password_hash, row["id"]))
    else:
        connection.execute(
            "INSERT INTO admins(username, password) VALUES(?, ?)",
            (username, password_hash),
        )


def fetch_active_cars():
    rows = get_db().execute("SELECT * FROM cars WHERE is_active=1 ORDER BY id DESC").fetchall()
    return [serialize_car(row) for row in rows]


def fetch_admin_cars():
    rows = get_db().execute("SELECT * FROM cars ORDER BY id DESC").fetchall()
    return [serialize_car(row) for row in rows]
