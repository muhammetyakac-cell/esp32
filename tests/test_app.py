import os
import tempfile
import unittest

from app import app, init_db


class AppTests(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.config["TESTING"] = True
        app.config["DATABASE_PATH"] = self.db_path
        with app.app_context():
            init_db()
        self.client = app.test_client()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_login_page(self):
        r = self.client.get("/login")
        self.assertEqual(r.status_code, 200)
        self.assertIn("DZY Panel Giriş", r.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
