"""受入条件: ファイルをクリックすると適切なビューアで開ける"""


class TestViewer:
    def test_viewer_page_loads_for_markdown(self, client):
        """md ファイルのビューアページが表示される"""
        response = client.get("/view/2026-06-17_テスト記事.md")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert "テスト記事" in response.text

    def test_viewer_page_loads_for_pdf(self, client):
        """PDF ファイルのビューアページが表示される"""
        response = client.get("/view/report.pdf")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

    def test_viewer_page_loads_for_html(self, client):
        """HTML ファイルのビューアページが表示される"""
        response = client.get("/view/presentation.html")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

    def test_viewer_nonexistent_file_returns_404(self, client):
        """存在しないファイルのビューアは 404"""
        response = client.get("/view/nonexistent.md")
        assert response.status_code == 404
