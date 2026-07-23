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

    def test_course_materials_limits_entries_to_current_scene(self):
        materials = (
            FRONTEND_SOURCE / "components" / "course" / "CourseMaterials.tsx"
        ).read_text(encoding="utf-8")

        self.assertIn("allowedDocumentTypes", materials)
        self.assertIn("UPLOAD_CATEGORIES.filter", materials)
        self.assertIn("openUpload(category.type)", materials)
        self.assertIn("initialDocumentType={uploadType}", materials)
        self.assertIn("添加第一份学习资料", materials)
        self.assertIn("action={uploadCategories[0]", materials)

    def test_dialog_submits_selected_type_without_changing_upload_api(self):
        dialog = (
            FRONTEND_SOURCE / "components" / "course" / "UploadDocumentDialog.tsx"
        ).read_text(encoding="utf-8")
        api = (FRONTEND_SOURCE / "lib" / "api.ts").read_text(encoding="utf-8")

        self.assertIn("{ file, documentType, chapterId, onProgress: setProgress }", dialog)
        self.assertIn("allowedDocumentTypes.includes", dialog)
        self.assertIn("setDocumentType(category.type)", dialog)
        self.assertNotIn("<select", dialog)
        self.assertIn("body.append('document_type', documentType)", api)
        self.assertIn("/documents", api)

    def test_upload_reports_progress_and_separates_server_saving(self):
        dialog = (
            FRONTEND_SOURCE / "components" / "course" / "UploadDocumentDialog.tsx"
        ).read_text(encoding="utf-8")
        api = (FRONTEND_SOURCE / "lib" / "api.ts").read_text(encoding="utf-8")
        nginx = (PROJECT_ROOT / "nginx.conf").read_text(encoding="utf-8")

        self.assertIn("new XMLHttpRequest()", api)
        self.assertIn("xhr.upload.addEventListener('progress'", api)
        self.assertIn("progress.percent", dialog)
        self.assertIn("服务器保存中", dialog)
        self.assertIn("文件仍已选中，可以直接重新上传", dialog)
        self.assertIn("重新上传", dialog)
        self.assertIn("proxy_request_buffering off;", nginx)


if __name__ == "__main__":
    unittest.main()
