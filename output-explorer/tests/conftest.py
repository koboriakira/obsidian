import pytest
from pathlib import Path
import tempfile
import shutil

from fastapi.testclient import TestClient


@pytest.fixture
def sample_output_dir(tmp_path: Path) -> Path:
    """output/ ディレクトリの構造を再現するフィクスチャ"""
    md_file = tmp_path / "2026-06-17_テスト記事.md"
    md_file.write_text(
        "---\n"
        "type: output\n"
        "created: 2026-06-17\n"
        "tags:\n"
        "  - Output\n"
        "purpose: 公開\n"
        "audience: 社外エンジニア\n"
        "destination: Zenn\n"
        "---\n"
        "\n"
        "# テスト記事\n"
        "\n"
        "本文です。\n",
        encoding="utf-8",
    )

    pdf_file = tmp_path / "report.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 dummy content")

    html_file = tmp_path / "presentation.html"
    html_file.write_text(
        "<html><body><h1>Presentation</h1></body></html>",
        encoding="utf-8",
    )

    return tmp_path


@pytest.fixture
def client(sample_output_dir: Path) -> TestClient:
    """テスト用 FastAPI クライアント（output_dir を差し替え）"""
    from app.main import create_app

    app = create_app(output_dir=sample_output_dir)
    return TestClient(app)
