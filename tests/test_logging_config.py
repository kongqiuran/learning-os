import json
import logging
import unittest

from src.logging_config import JsonLogFormatter


class JsonLogFormatterTest(unittest.TestCase):
    def test_context_fields_are_always_present(self):
        record = logging.LogRecord(
            "learning_os.test",
            logging.INFO,
            __file__,
            10,
            "Task completed.",
            (),
            None,
        )
        record.event = "task.status.changed"
        record.user_id = 7
        record.task_id = 12
        record.document_id = 19

        payload = json.loads(JsonLogFormatter().format(record))

        self.assertEqual(payload["event"], "task.status.changed")
        self.assertEqual(payload["user_id"], 7)
        self.assertEqual(payload["task_id"], 12)
        self.assertEqual(payload["document_id"], 19)
        self.assertIn("exception", payload)

    def test_error_includes_exception_and_null_context(self):
        record = logging.LogRecord(
            "learning_os.test",
            logging.ERROR,
            __file__,
            20,
            "Operation failed.",
            (),
            None,
        )
        record.event = "operation.failed"
        record.exception = ValueError("safe diagnostic")

        payload = json.loads(JsonLogFormatter().format(record))

        self.assertEqual(payload["exception"], "safe diagnostic")
        self.assertIsNone(payload["user_id"])
        self.assertIsNone(payload["task_id"])
        self.assertIsNone(payload["document_id"])


if __name__ == "__main__":
    unittest.main()
