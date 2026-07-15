import unittest
from datetime import datetime
from types import SimpleNamespace

from src.ui.cards import (
    render_chapter_card,
    render_exam_diagnosis_card,
    render_exam_focus_card,
    render_formula_card,
    render_question_card,
    render_strategy_card,
)
from src.ui.package_view import render_package_view


class FakeStreamlit:
    def __init__(self, root=None):
        self.root = root or self
        if root is None:
            self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def _record(self, name, *args, **kwargs):
        self.root.calls.append((name, args, kwargs))

    def container(self, **kwargs):
        self._record("container", **kwargs)
        return self

    def expander(self, label, **kwargs):
        self._record("expander", label, **kwargs)
        return self

    def columns(self, count):
        self._record("columns", count)
        size = count if isinstance(count, int) else len(count)
        return [FakeStreamlit(self.root) for _ in range(size)]

    def metric(self, *args, **kwargs):
        self._record("metric", *args, **kwargs)

    def markdown(self, *args, **kwargs):
        self._record("markdown", *args, **kwargs)

    def write(self, *args, **kwargs):
        self._record("write", *args, **kwargs)

    def caption(self, *args, **kwargs):
        self._record("caption", *args, **kwargs)

    def subheader(self, *args, **kwargs):
        self._record("subheader", *args, **kwargs)

    def info(self, *args, **kwargs):
        self._record("info", *args, **kwargs)

    def warning(self, *args, **kwargs):
        self._record("warning", *args, **kwargs)

    def code(self, *args, **kwargs):
        self._record("code", *args, **kwargs)


def _package(content):
    return SimpleNamespace(
        content_json=content,
        created_at=datetime(2026, 7, 15, 10, 30),
    )


class PackageViewTest(unittest.TestCase):
    def test_old_learning_package_renders_without_new_fields(self):
        ui = FakeStreamlit()
        render_package_view(
            SimpleNamespace(name="Signals and Systems"),
            _package(
                {
                    "exam_focus": ["Fourier transform"],
                    "formula_book": ["F = ma"],
                    "chapter_summary": ["Chapter one"],
                    "questions": ["Explain convolution"],
                    "exam_strategy": {"study_advice": "Review core topics first."},
                }
            ),
            3,
            language="en",
            st_module=ui,
        )
        self.assertTrue(any(name == "metric" for name, _, _ in ui.calls))
        self.assertTrue(any(name == "expander" for name, _, _ in ui.calls))

    def test_chinese_and_english_section_titles_render(self):
        zh_ui = FakeStreamlit()
        en_ui = FakeStreamlit()
        empty_package = _package({})
        course = SimpleNamespace(name="Test Course")
        render_package_view(course, empty_package, 0, "zh", zh_ui)
        render_package_view(course, empty_package, 0, "en", en_ui)

        zh_subheaders = [args[0] for name, args, _ in zh_ui.calls if name == "subheader"]
        en_subheaders = [args[0] for name, args, _ in en_ui.calls if name == "subheader"]
        self.assertEqual(
            zh_subheaders,
            [
                "考试诊断",
                "必考重点",
                "考试路线",
                "公式速查表",
                "高频练习题",
                "课程知识地图",
                "章节总结",
            ],
        )
        self.assertEqual(en_subheaders[0], "Exam Diagnosis")
        self.assertIn("Exam Roadmap", en_subheaders)
        self.assertIn("Formula Quick Reference", en_subheaders)

    def test_cards_accept_missing_fields(self):
        ui = FakeStreamlit()
        render_exam_focus_card({}, "zh", ui)
        render_formula_card({}, "zh", ui)
        render_chapter_card({}, "zh", ui)
        render_question_card({}, 1, "zh", ui)
        render_exam_diagnosis_card("Test", {}, 0, "—", "zh", ui)
        render_strategy_card({}, "zh", ui)
        self.assertGreater(len(ui.calls), 0)

    def test_diagnosis_is_derived_from_existing_package_fields(self):
        ui = FakeStreamlit()
        content = {
            "exam_focus": [
                {"topic": "Fourier", "importance": 5},
                {"topic": "Laplace", "importance": 4},
            ],
            "study_strategy": {
                "priority_order": ["Fourier", "Laplace"],
                "study_advice": "Start with high-frequency calculations.",
            },
        }
        render_exam_diagnosis_card("Signals", content, 3, "2026-07-15", "en", ui)
        rendered = "\n".join(str(args[0]) for _, args, _ in ui.calls if args)
        self.assertIn("Signals Exam Diagnosis", rendered)
        self.assertIn("Fourier", rendered)
        self.assertIn("Start with high-frequency calculations.", rendered)

    def test_large_question_set_renders_with_collapsed_answers(self):
        ui = FakeStreamlit()
        questions = [
            {
                "question": f"Question {index}",
                "answer": "Answer",
                "explanation": "Explanation",
            }
            for index in range(100)
        ]
        render_package_view(
            SimpleNamespace(name="Large Course"),
            _package({"questions": questions}),
            10,
            language="en",
            st_module=ui,
        )
        answer_expanders = [
            kwargs
            for name, _, kwargs in ui.calls
            if name == "expander" and kwargs.get("expanded") is False
        ]
        self.assertEqual(len(answer_expanders), 100)


if __name__ == "__main__":
    unittest.main()
