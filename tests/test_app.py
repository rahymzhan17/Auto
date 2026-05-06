import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import create_app


class AutoLuxAppTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)
        self.data_dir = self.base_path / "data"
        self.storage_dir = self.base_path / "storage"
        self.upload_dir = self.storage_dir / "uploads"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        self.app = create_app(
            {
                "TESTING": True,
                "DATABASE_PATH": self.data_dir / "test.db",
                "DATA_DIR": self.data_dir,
                "STORAGE_DIR": self.storage_dir,
                "UPLOAD_DIR": self.upload_dir,
                "JWT_SECRET": "test-secret-key-with-32-characters",
                "ADMIN_USERNAME": "admin",
                "ADMIN_PASSWORD": "StrongPass123",
                "ADMIN_PASSWORD_HASH": "",
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def login_headers(self):
        response = self.client.post(
            "/api/login",
            json={"username": "admin", "password": "StrongPass123"},
        )
        self.assertEqual(response.status_code, 200)
        token = response.get_json()["token"]
        return {"Authorization": f"Bearer {token}"}

    def test_public_pages_render(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("AutoLux".encode("utf-8"), response.data)

        admin_page = self.client.get("/admin")
        self.assertEqual(admin_page.status_code, 200)
        self.assertIn("Басқару Панелі".encode("utf-8"), admin_page.data)

    def test_hidden_car_not_available_publicly(self):
        headers = self.login_headers()
        create_response = self.client.post(
            "/api/admin/cars",
            headers=headers,
            json={
                "brand": "Test",
                "name": "Hidden",
                "type": "sedan",
                "tag": "HIDE",
                "price": "10 000 000",
                "full_price": "10 000 000",
                "monthly_price": "100 000",
                "engine": "2.0",
                "speed": "7.0 сек",
                "drive": "FWD",
                "fuel": "Бензин",
                "tagline": "hidden car",
                "features": ["Feature 1"],
                "photos": [],
                "is_active": 0,
            },
        )
        self.assertEqual(create_response.status_code, 200)
        car_id = create_response.get_json()["car"]["id"]

        public_list = self.client.get("/api/cars")
        self.assertEqual(public_list.status_code, 200)
        public_ids = {car["id"] for car in public_list.get_json()}
        self.assertNotIn(car_id, public_ids)

        public_detail = self.client.get(f"/api/cars/{car_id}")
        self.assertEqual(public_detail.status_code, 404)

    def test_contact_validation(self):
        response = self.client.post(
            "/api/contact",
            json={"name": "", "phone": "", "message": "Hi"},
        )
        self.assertEqual(response.status_code, 400)

    def test_admin_stats_authorized(self):
        response = self.client.get("/api/admin/stats", headers=self.login_headers())
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("cars", data)
        self.assertIn("td_total", data)

    @patch("app.routes.admin.download_image_from_url")
    def test_admin_upload_url_saves_remote_image_locally(self, mock_download):
        mock_download.return_value = {
            "url": "",
            "bytes": b"fake-image-bytes",
            "filename": "remote-photo.jpg",
        }

        response = self.client.post(
            "/api/admin/upload-url",
            headers=self.login_headers(),
            json={"url": "https://example.com/car.jpg"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["url"], "/uploads/remote-photo.jpg")
        self.assertTrue((self.upload_dir / "remote-photo.jpg").exists())

    @patch("app.routes.admin.download_image_from_url")
    def test_admin_upload_url_returns_existing_local_upload(self, mock_download):
        mock_download.return_value = {
            "url": "/uploads/already-there.png",
            "bytes": b"",
            "filename": "",
        }

        response = self.client.post(
            "/api/admin/upload-url",
            headers=self.login_headers(),
            json={"url": "/uploads/already-there.png"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["url"], "/uploads/already-there.png")


if __name__ == "__main__":
    unittest.main()
