import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_SOURCE = PROJECT_ROOT / "frontend" / "src"


class LegalPagesContractTest(unittest.TestCase):
    def test_legal_pages_are_public_routes(self):
        router = (FRONTEND_SOURCE / "app" / "router.tsx").read_text(encoding="utf-8")
        protected_route_position = router.index('<Route element={<ProtectedRoute />}>')

        for path in ("/legal/privacy", "/legal/terms"):
            route = f'<Route path="{path}"'
            self.assertIn(route, router)
            self.assertLess(
                router.index(route),
                protected_route_position,
                f"{path} must remain available without authentication.",
            )

    def test_legal_content_contains_current_version_and_required_sections(self):
        content = (FRONTEND_SOURCE / "legal" / "legalContent.ts").read_text(encoding="utf-8")

        self.assertIn("Learning OS 隐私政策", content)
        self.assertIn("Learning OS 用户协议", content)
        for section in ("信息使用目的", "AI 服务与第三方处理", "你的权利", "账号注销与终止", "套餐与额度"):
            self.assertIn(section, content)

        page = (FRONTEND_SOURCE / "pages" / "LegalPage.tsx").read_text(encoding="utf-8")
        self.assertRegex(page, re.compile(r"<MarkdownContent>\{document\.content\}</MarkdownContent>"))
        self.assertIn("privacyPolicy.data?.policy_version", page)

    def test_user_center_links_to_real_legal_pages(self):
        settings = (FRONTEND_SOURCE / "pages" / "SettingsPage.tsx").read_text(encoding="utf-8")

        self.assertIn('to="/legal/privacy"', settings)
        self.assertIn('to="/legal/terms"', settings)
        self.assertNotIn("VITE_PRIVACY_POLICY_URL", settings)
        self.assertNotIn("window.alert", settings)


if __name__ == "__main__":
    unittest.main()
