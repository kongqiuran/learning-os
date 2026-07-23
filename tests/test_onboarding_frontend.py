import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_SOURCE = PROJECT_ROOT / "frontend" / "src"


class OnboardingFrontendContractTest(unittest.TestCase):
    def test_dashboard_is_course_first_and_keeps_a_clear_empty_state(self):
        dashboard = (FRONTEND_SOURCE / "pages" / "DashboardPage.tsx").read_text(encoding="utf-8")
        self.assertIn("我的课程", dashboard)
        self.assertIn("WelcomeGuide", dashboard)
        self.assertIn("learning-os:recent-course", dashboard)
        self.assertNotIn("MetricCard", dashboard)

    def test_welcome_guide_contains_the_three_product_steps(self):
        guide = (
            FRONTEND_SOURCE / "components" / "domain" / "WelcomeGuide.tsx"
        ).read_text(encoding="utf-8")

        for step in ("1. 上传课程资料", "2. AI 整理知识", "3. 开始学习"):
            self.assertIn(step, guide)
        self.assertIn("创建第一门课程", guide)

    def test_registration_and_course_creation_continue_to_the_next_step(self):
        register = (FRONTEND_SOURCE / "pages" / "RegisterPage.tsx").read_text(encoding="utf-8")
        dashboard = (FRONTEND_SOURCE / "pages" / "DashboardPage.tsx").read_text(encoding="utf-8")
        dialog = (FRONTEND_SOURCE / "components" / "domain" / "CreateCourseDialog.tsx").read_text(encoding="utf-8")

        self.assertIn("/dashboard?create=1", register)
        self.assertIn("onCreated={(course) => openCourse(course.id)}", dashboard)
        self.assertIn("创建后会直接带你上传第一份资料", dialog)

    def test_first_course_guide_connects_upload_and_generation(self):
        guide = (FRONTEND_SOURCE / "components" / "course" / "FirstCourseGuide.tsx").read_text(encoding="utf-8")
        page = (FRONTEND_SOURCE / "pages" / "CourseSpacePage.tsx").read_text(encoding="utf-8")

        for copy in ("课程已创建", "上传第一份资料", "开始第一次 AI 整理", "任务会继续运行"):
            self.assertIn(copy, guide)
        self.assertIn("<FirstCourseGuide", page)
        self.assertIn('id="ai-learning-section"', page)

    def test_learning_package_empty_state_has_direct_generation_action(self):
        view = (
            FRONTEND_SOURCE / "components" / "course" / "LearningPackageView.tsx"
        ).read_text(encoding="utf-8")
        course_page = (
            FRONTEND_SOURCE / "pages" / "CourseSpacePage.tsx"
        ).read_text(encoding="utf-8")

        self.assertIn("开始整理课程内容", view)
        self.assertIn("canGenerate", view)
        self.assertIn("api.generateScene", course_page)
        self.assertIn("onGenerate={onGenerate}", course_page)
        self.assertIn("canGenerate={canGenerate}", course_page)


if __name__ == "__main__":
    unittest.main()
