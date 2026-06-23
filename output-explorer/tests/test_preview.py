"""受入条件: PDF/HTML ファイルのプレビューが可能"""


class TestPreview:
    def test_markdown_preview_returns_rendered_html(self, client):
        """md ファイルのプレビューが HTML に変換されて返る"""
        response = client.get("/api/files/2026-06-17_テスト記事.md/preview")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert "<h1>" in response.text

    def test_pdf_preview_returns_pdf_content(self, client):
        """PDF ファイルのプレビューが PDF として返る"""
        response = client.get("/api/files/report.pdf/preview")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_html_preview_returns_html_content(self, client):
        """HTML ファイルのプレビューがそのまま返る"""
        response = client.get("/api/files/presentation.html/preview")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert "<h1>Presentation</h1>" in response.text

    def test_preview_nonexistent_file_returns_404(self, client):
        """存在しないファイルのプレビューは 404"""
        response = client.get("/api/files/nonexistent.md/preview")
        assert response.status_code == 404
