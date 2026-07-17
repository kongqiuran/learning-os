import unittest
from pathlib import Path
from unittest.mock import patch

from src.api.factory import create_app


class ApiEntrypointTest(unittest.TestCase):
    def test_api_entrypoint_is_independent_from_streamlit(self):
        project_root = Path(__file__).parents[1]
        source = (project_root / "api_server.py").read_text(encoding="utf-8")
        self.assertIn("from src.api.factory import create_app", source)
        self.assertNotIn("import app", source)
        self.assertNotIn("from app", source)

    def test_existing_streamlit_entrypoint_remains_available(self):
        project_root = Path(__file__).parents[1]
        self.assertTrue((project_root / "app.py").exists())
        self.assertTrue((project_root / "start.bat").exists())

    def test_production_rejects_short_session_secret(self):
        with patch.dict("os.environ", {"APP_ENV": "production"}, clear=False):
            with self.assertRaisesRegex(RuntimeError, "at least 32"):
                create_app(session_secret="secret")

    def test_production_accepts_long_session_secret(self):
        with patch.dict("os.environ", {"APP_ENV": "production"}, clear=False):
            app = create_app(session_secret="a-secure-production-session-secret-123")
        self.assertEqual(app.title, "Learning OS API")


if __name__ == "__main__":
    unittest.main()
