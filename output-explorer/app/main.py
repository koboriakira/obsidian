from pathlib import Path

import frontmatter
import markdown as md
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

TEMPLATES_DIR = Path(__file__).parent / "templates"


EXTENSION_TYPE_MAP = {
    ".md": "markdown",
    ".pdf": "pdf",
    ".html": "html",
    ".htm": "html",
}

DEFAULT_OUTPUT_DIR = Path.home() / "obsidian" / "my-vault" / "output"


def _parse_file_entry(path: Path) -> dict:
    ext = path.suffix.lower()
    file_type = EXTENSION_TYPE_MAP.get(ext, "other")
    metadata = {}
    if file_type == "markdown":
        try:
            post = frontmatter.load(path)
            metadata = dict(post.metadata)
        except Exception:
            pass
    return {
        "name": path.name,
        "file_type": file_type,
        "metadata": metadata,
    }


def create_app(output_dir: Path | None = None) -> FastAPI:
    output_dir = output_dir or DEFAULT_OUTPUT_DIR
    app = FastAPI(title="Output Explorer")

    @app.get("/", response_class=HTMLResponse)
    def index():
        return (TEMPLATES_DIR / "index.html").read_text(encoding="utf-8")

    @app.get("/api/files")
    def list_files():
        files = sorted(output_dir.iterdir())
        return [_parse_file_entry(f) for f in files if f.is_file()]

    @app.get("/api/files/{filename}/preview")
    def preview_file(filename: str):
        path = output_dir / filename
        if not path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        ext = path.suffix.lower()
        if ext == ".md":
            post = frontmatter.load(path)
            html = md.markdown(post.content)
            return HTMLResponse(html)
        if ext == ".pdf":
            return FileResponse(path, media_type="application/pdf")
        if ext in (".html", ".htm"):
            return HTMLResponse(path.read_text(encoding="utf-8"))
        return FileResponse(path)

    @app.get("/view/{filename}")
    def view_file(filename: str):
        path = output_dir / filename
        if not path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        ext = path.suffix.lower()
        if ext == ".md":
            post = frontmatter.load(path)
            body_html = md.markdown(post.content)
            title = post.get("title", filename)
        elif ext == ".pdf":
            title = filename
            body_html = (
                f'<iframe src="/api/files/{filename}/preview" '
                f'style="width:100%;height:90vh;border:none;"></iframe>'
            )
        else:
            title = filename
            body_html = (
                f'<iframe src="/api/files/{filename}/preview" '
                f'style="width:100%;height:90vh;border:none;"></iframe>'
            )
        page = (
            "<!DOCTYPE html>"
            '<html><head><meta charset="utf-8">'
            f"<title>{title}</title>"
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            "</head><body>"
            f"{body_html}"
            "</body></html>"
        )
        return HTMLResponse(page)

    return app
