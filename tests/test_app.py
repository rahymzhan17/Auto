import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import create_app
from app.db import db
from app.models import Car


class AutoLuxAppTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)
        self.database_path = self.base_path / "test.db"

        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret-key-with-32-characters",
                "DATABASE_URL": f"sqlite:///{self.database_path.as_posix()}",
                "ADMIN_USERNAME": "admin",
                "ADMIN_PASSWORD": "StrongPass123",
                "CLOUD_NAME": "demo-cloud",
                "API_KEY": "demo-key",
                "API_SECRET": "demo-secret",
                "SESSION_COOKIE_SECURE": False,
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()
        self.temp_dir.cleanup()

    def login(self):
        return self.client.post(
            "/admin/login",
            data={"username": "admin", "password": "StrongPass123"},
            follow_redirects=False,
        )

    def test_public_and_login_pages_render(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("AutoLux".encode("utf-8"), response.data)

        admin_page = self.client.get("/admin")
        self.assertEqual(admin_page.status_code, 200)
        self.assertIn("Secure Admin Access".encode("utf-8"), admin_page.data)

    def test_upload_requires_login(self):
        response = self.client.post(
            "/upload",
            headers={"Accept": "application/json", "X-Requested-With": "fetch"},
            data={},
        )
        self.assertEqual(response.status_code, 401)

    @patch("app.routes.admin.upload_image_to_cloudinary")
    def test_upload_creates_car_and_returns_secure_url(self, mock_upload):
        mock_upload.return_value = "https://res.cloudinary.com/demo/image/upload/car.jpg"

        login_response = self.login()
        self.assertEqual(login_response.status_code, 302)

        with self.client as client:
            client.post("/admin/login", data={"username": "admin", "password": "StrongPass123"})
            response = client.post(
                "/upload",
                headers={"Accept": "application/json", "X-Requested-With": "fetch"},
                data={
                    "name": "BMW X7",
                    "price": "85000000",
                    "description": "Premium SUV for production deploy test",
                    "image": (io.BytesIO(b"fake-png-content"), "bmw.png", "image/png"),
                },
                content_type="multipart/form-data",
            )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertEqual(
            payload["secure_url"],
            "https://res.cloudinary.com/demo/image/upload/car.jpg",
        )
        self.assertEqual(payload["car"]["name"], "BMW X7")

        with self.app.app_context():
            cars = Car.query.all()
            self.assertEqual(len(cars), 1)
            self.assertEqual(cars[0].image_url, payload["secure_url"])

    def test_upload_rejects_invalid_extension(self):
        with self.client as client:
            client.post("/admin/login", data={"username": "admin", "password": "StrongPass123"})
            response = client.post(
                "/upload",
                headers={"Accept": "application/json", "X-Requested-With": "fetch"},
                data={
                    "name": "Audi Q8",
                    "price": "72000000",
                    "description": "Invalid file type test",
                    "image": (io.BytesIO(b"plain-text"), "q8.gif", "image/gif"),
                },
                content_type="multipart/form-data",
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn("JPG", response.get_json()["error"])

    @patch("app.routes.admin.upload_image_to_cloudinary")
    def test_api_cars_returns_saved_image_url(self, mock_upload):
        mock_upload.return_value = "https://res.cloudinary.com/demo/image/upload/lexus.jpg"

        with self.client as client:
            client.post("/admin/login", data={"username": "admin", "password": "StrongPass123"})
            client.post(
                "/upload",
                headers={"Accept": "application/json", "X-Requested-With": "fetch"},
                data={
                    "name": "Lexus RX",
                    "price": "55500000",
                    "description": "Hybrid crossover",
                    "image": (io.BytesIO(b"fake-png-content"), "lexus.png", "image/png"),
                },
                content_type="multipart/form-data",
            )

        response = self.client.get("/api/cars")
        self.assertEqual(response.status_code, 200)
        cars = response.get_json()
        self.assertEqual(len(cars), 1)
        self.assertEqual(cars[0]["image_url"], "https://res.cloudinary.com/demo/image/upload/lexus.jpg")


if __name__ == "__main__":
    unittest.main()
