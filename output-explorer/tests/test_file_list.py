"""受入条件: output/ 配下のファイル一覧が表示される（md, PDF, HTML 対応）"""


class TestFileList:
    def test_lists_all_files_in_output_directory(self, client):
        """output/ 配下の全ファイルが一覧に含まれる"""
        response = client.get("/api/files")
        assert response.status_code == 200
        files = response.json()
        filenames = [f["name"] for f in files]
        assert "2026-06-17_テスト記事.md" in filenames
        assert "report.pdf" in filenames
        assert "presentation.html" in filenames

    def test_returns_file_metadata_from_frontmatter(self, client):
        """md ファイルの frontmatter がメタデータとして返される"""
        response = client.get("/api/files")
        files = response.json()
        md_file = next(f for f in files if f["name"].endswith(".md"))
        assert md_file["metadata"]["type"] == "output"
        assert md_file["metadata"]["destination"] == "Zenn"
        assert md_file["metadata"]["audience"] == "社外エンジニア"

    def test_returns_file_type_for_each_entry(self, client):
        """各ファイルに拡張子ベースのファイル種別が付与される"""
        response = client.get("/api/files")
        files = response.json()
        types = {f["name"]: f["file_type"] for f in files}
        assert types["2026-06-17_テスト記事.md"] == "markdown"
        assert types["report.pdf"] == "pdf"
        assert types["presentation.html"] == "html"
