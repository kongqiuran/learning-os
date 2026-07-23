import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SETTINGS_PAGE = PROJECT_ROOT / "frontend" / "src" / "pages" / "SettingsPage.tsx"
SUPPORT_MODULE = PROJECT_ROOT / "frontend" / "src" / "lib" / "support.ts"


class SettingsEntitlementFrontendContractTest(unittest.TestCase):
    def test_support_email_uses_current_contact(self):
        support = SUPPORT_MODULE.read_text(encoding="utf-8")

        self.assertIn("3154949097@qq.com", support)
        self.assertNotIn("support@learning-os.cn", support)

    def test_active_entitlement_controls_paid_layout(self):
        page = SETTINGS_PAGE.read_text(encoding="utf-8")

        self.assertIn("activeEntitlements", page)
        self.assertIn("hasActiveEntitlement", page)
        self.assertIn("isActiveEntitlement", page)
        self.assertIn("已开通课程权益", page)
        self.assertIn("免费额度会继续保留，可作为课程权益之外的补充。", page)

    def test_entitlement_card_shows_purchase_value(self):
        page = SETTINGS_PAGE.read_text(encoding="utf-8")

        for label in ("有效期至", "剩余权益", "跟课整理", "教材分析", "考试冲刺", "课程助手"):
            self.assertIn(label, page)
        self.assertIn("item.course_name", page)
        self.assertIn("item.amount_cents", page)


if __name__ == "__main__":
    unittest.main()
