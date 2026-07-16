import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.config import DATA_DIR, get_database_url


class ConfigIsolationTest(unittest.TestCase):
    def test_pytest_data_directory_is_outside_project_data(self):
        configured_data_dir = Path(os.environ["LEARNING_OS_DATA_DIR"]).resolve()
        self.assertEqual(DATA_DIR.resolve(), configured_data_dir)
        self.assertIn("learning-os-pytest-", str(configured_data_dir))

    def test_process_database_url_takes_precedence_over_dotenv(self):
        with tempfile.TemporaryDirectory() as directory:
            expected_path = Path(directory) / "precedence.db"
            with patch.dict(
                os.environ,
                {
                    "DATABASE_URL": f"sqlite:///{expected_path.as_posix()}",
                    "LEARNING_OS_TESTING": "1",
                },
                clear=False,
            ):
                self.assertEqual(get_database_url(), f"sqlite:///{expected_path.as_posix()}")

    def test_test_mode_rejects_production_database(self):
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "sqlite:///data/database/learning_os.db",
                "LEARNING_OS_TESTING": "1",
            },
            clear=False,
        ):
            with self.assertRaisesRegex(RuntimeError, "Tests cannot use the production"):
                get_database_url()


if __name__ == "__main__":
    unittest.main()
