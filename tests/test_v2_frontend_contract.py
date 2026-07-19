import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "frontend" / "src"


class V2FrontendContractTest(unittest.TestCase):
    def test_course_scene_routes_and_chapter_delete_choices_exist(self):
        router = (ROOT / "app" / "router.tsx").read_text(encoding="utf-8")
        page = (ROOT / "pages" / "CourseSpacePage.tsx").read_text(encoding="utf-8")
        for path in ("follow", "textbooks", "exam"):
            self.assertIn(path, router)
        self.assertIn("保留资料并移到未分章节", page)
        self.assertIn("删除章节和其中资料", page)
        self.assertIn("keep_unassigned", page)
        self.assertIn("textbook: 'textbooks'", page)

    def test_new_uploads_hide_legacy_notes_and_are_scoped_by_scene(self):
        categories = (ROOT / "components" / "course" / "uploadCategories.ts").read_text(encoding="utf-8")
        dialog = (ROOT / "components" / "course" / "UploadDocumentDialog.tsx").read_text(encoding="utf-8")
        self.assertNotIn("type: 'NOTES'", categories)
        self.assertIn("follow: ['SLIDES', 'HOMEWORK', 'OTHER']", categories)
        self.assertIn("textbook: ['TEXTBOOK']", categories)
        self.assertIn("exam: ['EXAM', 'HOMEWORK']", categories)
        self.assertIn("allowedDocumentTypes.includes", dialog)

    def test_chapter_creation_keeps_unassigned_materials_visible(self):
        page = (ROOT / "pages" / "CourseSpacePage.tsx").read_text(encoding="utf-8")
        self.assertIn("const hasUnassignedDocuments", page)
        self.assertIn("setSelectedChapterId(hasUnassignedDocuments ? null", page)
        self.assertIn("{unassignedDocumentCount} 份资料", page)
        create_mutation = page.split("const createChapter = useMutation", 1)[1].split("const updateChapter", 1)[0]
        self.assertNotIn("setSelectedChapterId(chapter.id)", create_mutation)

    def test_failed_generation_has_retry_and_section_question_opens_assistant(self):
        package = (ROOT / "components" / "course" / "LearningPackageView.tsx").read_text(encoding="utf-8")
        page = (ROOT / "pages" / "CourseSpacePage.tsx").read_text(encoding="utf-8")
        self.assertIn("本次不会扣除额度", package)
        self.assertIn("重新整理", package)
        self.assertIn("onSelectSection={openAssistant}", page)

    def test_pricing_discloses_allowances_and_failure_refund(self):
        pricing = (ROOT / "pages" / "PricingPage.tsx").read_text(encoding="utf-8")
        for disclosure in ("99 元", "跟课资料 AI 整理成功 3 次", "教材解析成功 3 次", "考试冲刺成功 3 次", "AI 助手问答 100 次", "失败、超时或系统中断自动返还", "不自动续费"):
            self.assertIn(disclosure, pricing)


if __name__ == "__main__":
    unittest.main()
