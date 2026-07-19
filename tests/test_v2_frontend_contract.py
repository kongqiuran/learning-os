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

    def test_pricing_discloses_allowances_and_failure_refund(self):
        pricing = (ROOT / "pages" / "PricingPage.tsx").read_text(encoding="utf-8")
        for disclosure in ("99 元", "跟课资料 AI 整理成功 3 次", "教材解析成功 3 次", "考试冲刺成功 3 次", "AI 助手问答 100 次", "失败、超时或系统中断自动返还", "不自动续费"):
            self.assertIn(disclosure, pricing)


if __name__ == "__main__":
    unittest.main()
