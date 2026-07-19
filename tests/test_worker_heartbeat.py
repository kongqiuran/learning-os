import threading
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import worker


class WorkerHeartbeatTest(unittest.TestCase):
    def test_worker_heartbeat_updates_file_independently(self):
        stop_event = threading.Event()
        with TemporaryDirectory() as temporary_directory:
            data_dir = Path(temporary_directory)
            with (
                patch.object(worker, "DATA_DIR", data_dir),
                patch.object(worker, "stop_event", stop_event),
            ):
                heartbeat = threading.Thread(target=worker._worker_heartbeat)
                heartbeat.start()
                heartbeat_path = data_dir / "database" / "worker-heartbeat"
                deadline = time.monotonic() + 1
                while not heartbeat_path.exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                stop_event.set()
                heartbeat.join(timeout=1)

            self.assertTrue(heartbeat_path.exists())
            self.assertFalse(heartbeat.is_alive())


if __name__ == "__main__":
    unittest.main()
