import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_SOURCE = PROJECT_ROOT / "frontend" / "src"


class UploadExperienceFrontendContractTest(unittest.TestCase):
    def test_primary_upload_entries_bind_expected_document_types(self):
        categories = (
            FRONTEND_SOURCE / "components" / "course" / "uploadCategories.ts"
        ).read_text(encoding="utf-8")

        expected = {
            "TEXTBOOK": "上传教材",
            "SLIDES": "上传课件",
            "OTHER": "上传补充资料",
            "EXAM": "上传试卷",
        }
        for document_type, action in expected.items():
            self.assertIn(f"type: '{document_type}'", categories)
            self.assertIn(f"action: '{action}'", categories)

    def test_course_materials_exposes_all_primary_category_entries(self):
        materials = (
            FRONTEND_SOURCE / "components" / "course" / "CourseMaterials.tsx"
        ).read_text(encoding="utf-8")

        self.assertIn("PRIMARY_UPLOAD_CATEGORIES.map", materials)
        self.assertIn("openUpload(category.type)", materials)
        self.assertIn("initialDocumentType={uploadType}", materials)

    def test_dialog_submits_selected_type_without_changing_upload_api(self):
        dialog = (
            FRONTEND_SOURCE / "components" / "course" / "UploadDocumentDialog.tsx"
        ).read_text(encoding="utf-8")
        api = (FRONTEND_SOURCE / "lib" / "api.ts").read_text(encoding="utf-8")

        self.assertIn("{ file, documentType }", dialog)
        self.assertIn("setDocumentType(category.type)", dialog)
        self.assertNotIn("<select", dialog)
        self.assertIn("body.append('document_type', documentType)", api)
        self.assertIn("/documents", api)


if __name__ == "__main__":
    unittest.main()
