import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_SOURCE = PROJECT_ROOT / "frontend" / "src"


class OnboardingFrontendContractTest(unittest.TestCase):
    def test_welcome_guide_is_non_blocking_and_only_shown_for_empty_accounts(self):
        dashboard = (FRONTEND_SOURCE / "pages" / "DashboardPage.tsx").read_text(encoding="utf-8")
        guide = (
            FRONTEND_SOURCE / "components" / "domain" / "WelcomeGuide.tsx"
        ).read_text(encoding="utf-8")

        self.assertIn("dashboard.data.course_count === 0", dashboard)
        self.assertIn("isNewAccount(currentUser.data.user.created_at)", dashboard)
        self.assertIn("7 * 24 * 60 * 60 * 1000", dashboard)
        self.assertIn("欢迎使用 Learning OS", guide)
        self.assertIn("关闭首次使用引导", guide)
        self.assertIn("learning-os:onboarding-dismissed:${userId}", guide)
        self.assertIn("window.localStorage.setItem", guide)

    def test_welcome_guide_contains_the_three_product_steps(self):
        guide = (
            FRONTEND_SOURCE / "components" / "domain" / "WelcomeGuide.tsx"
        ).read_text(encoding="utf-8")

        for step in ("1. 上传课程资料", "2. AI 整理知识", "3. 开始学习"):
            self.assertIn(step, guide)
        self.assertIn("创建第一门课程", guide)

    def test_learning_package_empty_state_has_direct_generation_action(self):
        view = (
            FRONTEND_SOURCE / "components" / "course" / "LearningPackageView.tsx"
        ).read_text(encoding="utf-8")
        course_page = (
            FRONTEND_SOURCE / "pages" / "CourseSpacePage.tsx"
        ).read_text(encoding="utf-8")

        self.assertIn("开始整理课程内容", view)
        self.assertIn("canGenerate", view)
        self.assertIn("onGenerate={generateLearningPackage}", course_page)
        self.assertIn("canGenerate={documents.length > 0}", course_page)


if __name__ == "__main__":
    unittest.main()
