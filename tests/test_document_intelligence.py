import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import fitz

from src.ai.analyzers.document_analyzer import analyze_document
from src.ai.document.parser import parse_pdf_pages
from src.ai.document.pipeline import (
    DOCUMENT_INTELLIGENCE_PIPELINE_VERSION,
    understand_pdf,
)
from src.ai.document.vision_router import route_page
from src.ai.providers.base import VisionProvider
from src.ai.providers.qwen_vision_provider import QwenVisionProvider
from src.config import VisionConfig
from src.database import create_database_tables, get_db_session
from src.models import Course, Document, DocumentPage, User


class FakeVisionProvider(VisionProvider):
    def __init__(self, available=True, should_fail=False):
        self.available = available
        self.should_fail = should_fail

    @property
    def provider_name(self):
        return "fake-vision"

    @property
    def model_name(self):
        return "fake-v1"

    def is_available(self):
        return self.available

    def analyze_page(self, image_path, page_text, metadata):
        del image_path, page_text, metadata
        if self.should_fail:
            raise RuntimeError("simulated vision failure")
        return SimpleNamespace(
            content={
                "title": "Visual page",
                "summary": "The page contains a teaching diagram.",
                "important_level": 4,
                "key_points": ["Diagram relationship"],
                "formulas": [],
                "figures": ["Teaching diagram"],
                "exam_points": [],
                "teacher_emphasis": [],
                "evidence": [],
                "confidence": 0.9,
            },
            provider=self.provider_name,
            model=self.model_name,
            input_tokens=120,
            output_tokens=40,
        )


class CapturingLLM:
    def __init__(self):
        self.payload = None

    def generate(self, system_prompt, user_prompt, stage="unknown"):
        del system_prompt, stage
        self.payload = json.loads(user_prompt)
        return {
            "summary": "Fused teaching summary",
            "topics": [{"name": "Topic", "importance": 5}],
            "formulas": [],
            "question_patterns": [],
            "errors": [],
        }


class DocumentIntelligenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_database_tables()

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        with get_db_session() as session:
            for model in (DocumentPage, Document, Course, User):
                session.query(model).delete()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_pdf_parser_preserves_pages_and_classifies_visual_page(self):
        pdf_path = Path(self.temp_dir.name) / "pages.pdf"
        image_path = self._make_image()
        with fitz.open() as pdf:
            first = pdf.new_page()
            first.insert_text((72, 72), "A normal text page with course content.")
            second = pdf.new_page()
            second.insert_image(second.rect, filename=str(image_path))
            pdf.save(pdf_path)

        pages = parse_pdf_pages(pdf_path)

        self.assertEqual([page.page_number for page in pages], [1, 2])
        self.assertEqual(pages[0].page_type, "text")
        self.assertEqual(pages[1].page_type, "scanned")
        self.assertFalse(route_page(pages[0]).requires_vision)
        self.assertTrue(route_page(pages[1]).requires_vision)
        self.assertEqual(len(pages[0].content_hash), 64)

    def test_pipeline_creates_document_pages_and_keeps_raw_vision_result(self):
        pdf_path = Path(self.temp_dir.name) / "mixed.pdf"
        image_path = self._make_image()
        with fitz.open() as pdf:
            page = pdf.new_page()
            page.insert_text((72, 72), "A short explanation beside the figure.")
            page.insert_image(fitz.Rect(60, 120, 500, 700), filename=str(image_path))
            pdf.save(pdf_path)
        document, user_id, course_id = self._create_document(pdf_path)

        result = understand_pdf(
            document,
            user_id=user_id,
            course_id=course_id,
            vision_provider=FakeVisionProvider(),
        )

        self.assertEqual(result.pipeline_version, DOCUMENT_INTELLIGENCE_PIPELINE_VERSION)
        self.assertFalse(result.degraded)
        self.assertEqual(result.pages[0].vision_result["title"], "Visual page")
        with get_db_session() as session:
            page = session.query(DocumentPage).one()
            self.assertEqual(page.page_type, "mixed")
            self.assertEqual(page.analysis_status, "completed")
            self.assertEqual(page.vision_result["summary"], "The page contains a teaching diagram.")
            self.assertEqual((page.input_tokens, page.output_tokens), (120, 40))
            self.assertIn("derived", page.image_path)

    def test_vision_failure_falls_back_to_page_text(self):
        pdf_path = Path(self.temp_dir.name) / "fallback.pdf"
        image_path = self._make_image()
        with fitz.open() as pdf:
            page = pdf.new_page()
            page.insert_text((72, 72), "Usable extracted text remains available.")
            page.insert_image(fitz.Rect(60, 120, 500, 700), filename=str(image_path))
            pdf.save(pdf_path)
        document, user_id, course_id = self._create_document(pdf_path)

        result = understand_pdf(
            document,
            user_id=user_id,
            course_id=course_id,
            vision_provider=FakeVisionProvider(should_fail=True),
        )

        self.assertTrue(result.degraded)
        self.assertIn("Usable extracted text", result.pages[0].text_content)
        self.assertEqual(result.pages[0].vision_result, {})
        with get_db_session() as session:
            page = session.query(DocumentPage).one()
            self.assertEqual(page.analysis_status, "failed")
            self.assertIn("simulated vision failure", page.error_detail)

    def test_qwen_provider_normalizes_mock_response_and_usage(self):
        image_path = self._make_image()
        response = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=json.dumps(
                            {
                                "title": "Waveform",
                                "important_level": 9,
                                "key_points": "Period",
                                "confidence": 1.4,
                            }
                        )
                    )
                )
            ],
            usage=SimpleNamespace(prompt_tokens=22, completion_tokens=11),
        )
        completions = SimpleNamespace(create=lambda **kwargs: response)
        client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
        provider = QwenVisionProvider(
            client=client,
            config=VisionConfig(
                enabled=True,
                provider="qwen",
                api_key="test-key",
                base_url="https://example.invalid/v1",
                model="qwen-vl-test",
                timeout_seconds=30,
                max_attempts=1,
                max_pages_per_document=10,
                render_dpi=144,
            ),
        )

        result = provider.analyze_page(image_path, "page text", {"page_number": 1})

        self.assertEqual(result.content["important_level"], 5)
        self.assertEqual(result.content["confidence"], 1.0)
        self.assertEqual(result.content["key_points"], ["Period"])
        self.assertEqual((result.input_tokens, result.output_tokens), (22, 11))

    def test_document_analyzer_accepts_page_understanding_without_persisting_raw_input(self):
        client = CapturingLLM()
        understanding = {
            "pipeline_version": DOCUMENT_INTELLIGENCE_PIPELINE_VERSION,
            "pages": [
                {
                    "page_number": 1,
                    "text": "Extracted text",
                    "vision_result": {"summary": "Raw vision fact"},
                }
            ],
        }

        result = analyze_document(
            "TEXTBOOK",
            "PDF",
            llm_client=client,
            document_understanding=understanding,
        )

        self.assertEqual(
            client.payload["document_understanding"]["pages"][0]["vision_result"]["summary"],
            "Raw vision fact",
        )
        self.assertNotIn("document_understanding", result)
        self.assertEqual(result["summary"], "Fused teaching summary")

    def _create_document(self, pdf_path):
        with get_db_session() as session:
            user = User(
                email=f"document-intelligence-{pdf_path.stem}@example.com",
                password_hash="test",
            )
            session.add(user)
            session.flush()
            course = Course(user_id=user.id, name="Document intelligence")
            session.add(course)
            session.flush()
            document = Document(
                user_id=user.id,
                course_id=course.id,
                original_filename=pdf_path.name,
                stored_filename=pdf_path.name,
                file_path=str(pdf_path),
                mime_type="application/pdf",
                file_size=pdf_path.stat().st_size,
                document_type="TEXTBOOK",
            )
            session.add(document)
            session.flush()
            return document, user.id, course.id

    def _make_image(self):
        image_path = Path(self.temp_dir.name) / "page-image.png"
        pixmap = fitz.Pixmap(
            fitz.csRGB,
            fitz.IRect(0, 0, 300, 300),
            False,
        )
        pixmap.clear_with(220)
        pixmap.save(image_path)
        return image_path


if __name__ == "__main__":
    unittest.main()
