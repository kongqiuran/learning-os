import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_SOURCE = PROJECT_ROOT / "frontend" / "src"


class PrivacyReconsentFrontendContractTest(unittest.TestCase):
    def test_protected_routes_check_current_user_consent_status(self):
        protected_route = (
            FRONTEND_SOURCE / "components" / "auth" / "ProtectedRoute.tsx"
        ).read_text(encoding="utf-8")

        self.assertIn("usePrivacyConsentStatus(currentUser.isSuccess)", protected_route)
        self.assertIn("consentStatus.data.requires_reconsent", protected_route)
        self.assertIn("<PrivacyReconsentPage", protected_route)

    def test_reconsent_page_links_legal_documents_and_submits_server_bound_consent(self):
        page = (
            FRONTEND_SOURCE / "components" / "privacy" / "PrivacyReconsentPage.tsx"
        ).read_text(encoding="utf-8")
        api = (FRONTEND_SOURCE / "lib" / "api.ts").read_text(encoding="utf-8")

        self.assertIn("隐私政策已更新", page)
        self.assertIn('to="/legal/privacy"', page)
        self.assertIn('to="/legal/terms"', page)
        self.assertIn("同意并继续使用", page)
        consent_api = api[api.index("acceptPrivacyConsent:"):api.index("usage:")]
        self.assertIn("JSON.stringify({ accepted: true })", consent_api)
        self.assertNotIn("policy_version", consent_api)


if __name__ == "__main__":
    unittest.main()
