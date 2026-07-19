import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from src.api.adapters import generation_adapter
from src.api.adapters.generation_adapter import GenerationInProgressError


class GenerationAdapterTest(unittest.TestCase):
    def tearDown(self):
        generation_adapter._active_course_ids.clear()

    def test_generation_delegates_to_existing_service(self):
        package = SimpleNamespace(id=1, status="completed")
        with (
            patch.object(generation_adapter, "get_learning_package", return_value=None),
            patch.object(generation_adapter, "analyze_course", return_value=package) as analyze,
        ):
            result = generation_adapter.generate_course_package(10, 5)

        self.assertIs(result, package)
        analyze.assert_called_once_with(10, 5, language="zh")

    def test_active_course_is_rejected_by_single_process_lock(self):
        generation_adapter._active_course_ids.add(10)
        with self.assertRaises(GenerationInProgressError):
            generation_adapter.generate_course_package(10, 5)

    def test_recent_processing_package_is_rejected_and_lock_is_released(self):
        package = SimpleNamespace(
            status="processing",
            created_at=datetime.now(timezone.utc),
        )
        with patch.object(generation_adapter, "get_learning_package", return_value=package):
            with self.assertRaises(GenerationInProgressError):
                generation_adapter.generate_course_package(10, 5)

        self.assertNotIn(10, generation_adapter._active_course_ids)

    def test_queue_creates_pending_task_and_releases_process_lock(self):
        task = SimpleNamespace(id=7, status="pending")
        with (
            patch.object(generation_adapter, "get_learning_package", return_value=None),
            patch.object(generation_adapter, "create_learning_package_task", return_value=task) as create_task,
        ):
            result = generation_adapter.queue_course_package(10, 5)

        self.assertIs(result, task)
        create_task.assert_called_once_with(10, 5)
        self.assertNotIn(10, generation_adapter._active_course_ids)

    def test_queued_worker_reuses_task_and_releases_lock(self):
        generation_adapter._active_course_ids.add(10)
        completed = SimpleNamespace(id=7, status="completed")
        with patch.object(generation_adapter, "analyze_course", return_value=completed) as analyze:
            result = generation_adapter.run_queued_course_package(7, 10, 5)

        self.assertIs(result, completed)
        analyze.assert_called_once_with(10, 5, language="zh", package_id=7)
        self.assertNotIn(10, generation_adapter._active_course_ids)

    def test_recent_pending_task_is_rejected_and_lock_is_released(self):
        task = SimpleNamespace(status="pending", created_at=datetime.now(timezone.utc))
        with patch.object(generation_adapter, "get_learning_package", return_value=task):
            with self.assertRaises(GenerationInProgressError):
                generation_adapter.queue_course_package(10, 5)

        self.assertNotIn(10, generation_adapter._active_course_ids)


if __name__ == "__main__":
    unittest.main()
