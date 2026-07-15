import unittest
from pathlib import Path

from src.i18n import t
from src.ui.generation_status import run_generation_with_feedback


class FakeStatus:
    def __init__(self, root):
        self.root = root

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def write(self, value):
        self.root.calls.append(("write", value, {}))

    def caption(self, value):
        self.root.calls.append(("caption", value, {}))

    def update(self, **kwargs):
        self.root.calls.append(("update", None, kwargs))


class FakeStreamlit:
    def __init__(self):
        self.calls = []

    def status(self, label, **kwargs):
        self.calls.append(("status", label, kwargs))
        return FakeStatus(self)

    def info(self, value):
        self.calls.append(("info", value, {}))


class GenerationFeedbackTest(unittest.TestCase):
    def test_success_displays_all_stages_and_completion(self):
        ui = FakeStreamlit()
        result = run_generation_with_feedback(lambda: "package", "zh", ui)

        self.assertEqual(result, "package")
        rendered = "\n".join(str(value) for _, value, _ in ui.calls if value)
        for key in (
            "generation_status_title",
            "generation_stage_reading",
            "generation_stage_analysis",
            "generation_stage_formula",
            "generation_stage_questions",
        ):
            self.assertIn(t(key, "zh"), rendered)
        self.assertTrue(
            any(
                name == "update" and kwargs.get("state") == "complete"
                for name, _, kwargs in ui.calls
            )
        )
        status_call = next(call for call in ui.calls if call[0] == "status")
        self.assertTrue(status_call[2].get("expanded"))

    def test_failure_sets_error_status_and_reraises(self):
        ui = FakeStreamlit()

        def fail():
            raise RuntimeError("LLM unavailable")

        with self.assertRaisesRegex(RuntimeError, "LLM unavailable"):
            run_generation_with_feedback(fail, "en", ui)
        self.assertTrue(
            any(
                name == "update"
                and kwargs.get("state") == "error"
                and kwargs.get("label") == t("generation_failed_friendly", "en")
                for name, _, kwargs in ui.calls
            )
        )

    def test_feedback_text_switches_languages(self):
        self.assertIn("1-5分钟", t("generation_time_hint", "zh"))
        self.assertIn("1-5 minutes", t("generation_time_hint", "en"))
        self.assertEqual(
            t("generation_failed_friendly", "zh"),
            "生成失败，请检查资料或稍后重试。",
        )

    def test_generation_button_uses_guarded_session_state(self):
        source = (Path(__file__).parents[1] / "app.py").read_text(encoding="utf-8")
        self.assertIn("on_click=request_package_generation", source)
        self.assertIn("disabled=not documents or generation_in_progress", source)
        self.assertIn("run_generation_with_feedback(", source)
        self.assertIn("logger.exception(", source)


if __name__ == "__main__":
    unittest.main()
