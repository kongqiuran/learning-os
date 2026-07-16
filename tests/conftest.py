import os
import tempfile
from pathlib import Path


TEST_ROOT = tempfile.TemporaryDirectory(prefix="learning-os-pytest-")
TEST_ROOT_PATH = Path(TEST_ROOT.name)
os.environ["LEARNING_OS_TESTING"] = "1"
os.environ["LEARNING_OS_DATA_DIR"] = str(TEST_ROOT_PATH / "data")
os.environ["DATABASE_URL"] = f"sqlite:///{(TEST_ROOT_PATH / 'test.db').as_posix()}"


def pytest_unconfigure(config):
    del config
    from src.database.connection import engine

    engine.dispose()
    TEST_ROOT.cleanup()
