from __future__ import annotations

import argparse
import html
import io
import secrets
import sys
import zipfile
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from court_ocr_extract.config import get_settings
from court_ocr_extract.file_utils import unique_path


class TransferRequestHandler(BaseHTTPRequestHandler):
    server_version = "CourtOcrTransfer/0.1"
    token = ""
    max_upload_bytes = 2 * 1024 * 1024 * 1024

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send_text("ok")
            return
        if not self._authorized(parsed):
            self._send_error(HTTPStatus.FORBIDDEN, "Invalid token.")
            return
        if parsed.path in {"", "/"}:
            self._send_html(self._upload_page())
            return
        if parsed.path == "/outputs":
            self._send_html(self._outputs_page())
            return
        if parsed.path.startswith("/download/excel/"):
            filename = unquote(parsed.path.removeprefix("/download/excel/"))
            self._send_file(get_settings().excel_dir, filename)
            return
        if parsed.path.startswith("/download/json/"):
            filename = unquote(parsed.path.removeprefix("/download/json/"))
            self._send_file(get_settings().json_dir, filename)
            return
        self._send_error(HTTPStatus.NOT_FOUND, "Not found.")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/upload":
            self._send_error(HTTPStatus.NOT_FOUND, "Not found.")
            return
        if not self._authorized(parsed):
            self._send_error(HTTPStatus.FORBIDDEN, "Invalid token.")
            return

        content_length = int(self.headers.get("Content-Length") or "0")
        if content_length <= 0:
            self._send_error(HTTPStatus.BAD_REQUEST, "Missing upload body.")
            return
        if content_length > self.max_upload_bytes:
            self._send_error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Upload too large.")
            return

        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type or "boundary=" not in content_type:
            self._send_error(HTTPStatus.BAD_REQUEST, "Expected multipart/form-data.")
            return

        body = self.rfile.read(content_length)
        saved = self._save_multipart_uploads(body, content_type)
        self._send_json({"saved": saved, "count": len(saved)})

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        # Keep terminal logs free of uploaded filenames or document details.
        status = args[1] if len(args) > 1 else "-"
        sys.stderr.write(f"{self.address_string()} {self.command} {status}\n")

    def _authorized(self, parsed) -> bool:
        query = parse_qs(parsed.query)
        query_token = (query.get("token") or [""])[0]
        header_token = self.headers.get("X-Transfer-Token", "")
        return query_token == self.token or header_token == self.token

    def _save_multipart_uploads(self, body: bytes, content_type: str) -> list[str]:
        boundary = _extract_boundary(content_type)
        parts = _multipart_file_parts(body, boundary)
        settings = get_settings()
        upload_dir = settings.raw_pdf_dir / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)

        saved: list[str] = []
        for original_name, content in parts:
            suffix = Path(original_name).suffix.lower()
            if suffix == ".zip":
                saved.extend(_extract_pdf_zip(content, upload_dir))
            elif suffix == ".pdf" or content.startswith(b"%PDF"):
                saved.append(_write_generated_pdf(upload_dir, content).name)
        return saved

    def _upload_page(self) -> str:
        token = html.escape(self.token)
        return f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Court OCR Transfer</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #111827; }}
    main {{ max-width: 760px; }}
    input, button {{ font: inherit; }}
    input[type=file] {{ display: block; margin: 14px 0; }}
    button {{ padding: 9px 14px; }}
    pre {{ background: #f4f6f8; border: 1px solid #d9dee7; padding: 12px; overflow: auto; }}
    a {{ color: #0f766e; font-weight: 700; }}
  </style>
</head>
<body>
  <main>
    <h1>Upload PDF vào VM</h1>
    <p>Chọn nhiều PDF hoặc một file ZIP chứa PDF. File sẽ được lưu bằng tên tự sinh để tránh lộ tên file thật trong log.</p>
    <input id="files" type="file" accept=".pdf,.zip,application/pdf,application/zip" multiple />
    <button id="upload">Upload</button>
    <p><a href="/outputs?token={token}">Xem output Excel/JSON</a></p>
    <pre id="log"></pre>
  </main>
  <script>
    const token = "{token}";
    const files = document.querySelector("#files");
    const log = document.querySelector("#log");
    document.querySelector("#upload").addEventListener("click", async () => {{
      log.textContent = "";
      for (const file of files.files) {{
        const data = new FormData();
        data.append("file", file);
        log.textContent += `Uploading ${{file.name}}...\\n`;
        const response = await fetch(`/upload?token=${{encodeURIComponent(token)}}`, {{
          method: "POST",
          body: data
        }});
        const payload = await response.json();
        if (!response.ok) {{
          log.textContent += `FAILED: ${{JSON.stringify(payload)}}\\n`;
          continue;
        }}
        log.textContent += `Saved ${{payload.count}} file(s).\\n`;
      }}
      log.textContent += "Done. Chạy batch trong PowerShell trên VM.\\n";
    }});
  </script>
</body>
</html>"""

    def _outputs_page(self) -> str:
        settings = get_settings()
        token = quote(self.token)
        excel_links = _links_for(settings.excel_dir, "excel", token)
        json_links = _links_for(settings.json_dir, "json", token)
        return f"""<!doctype html>
<html lang="vi">
<head><meta charset="utf-8" /><title>Court OCR Outputs</title></head>
<body style="font-family: Arial, sans-serif; margin: 32px;">
  <h1>Outputs</h1>
  <p><a href="/?token={token}">Quay lại upload</a></p>
  <h2>Excel</h2>
  <ul>{excel_links or "<li>Chưa có file Excel.</li>"}</ul>
  <h2>JSON</h2>
  <ul>{json_links or "<li>Chưa có file JSON.</li>"}</ul>
</body>
</html>"""

    def _send_file(self, directory: Path, filename: str) -> None:
        path = (directory / Path(filename).name).resolve()
        base = directory.resolve()
        if base not in path.parents or not path.exists() or not path.is_file():
            self._send_error(HTTPStatus.NOT_FOUND, "File not found.")
            return
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header(
            "Content-Disposition",
            f'attachment; filename="{path.name.encode("ascii", "ignore").decode() or "download"}"',
        )
        self.end_headers()
        self.wfile.write(data)

    def _send_text(self, text: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(text.encode("utf-8"))

    def _send_html(self, text: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(text.encode("utf-8"))

    def _send_json(self, payload: dict) -> None:
        import json

        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_error(self, status: HTTPStatus, message: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(f'{{"error": "{html.escape(message)}"}}'.encode("utf-8"))


def _extract_boundary(content_type: str) -> bytes:
    for item in content_type.split(";"):
        item = item.strip()
        if item.startswith("boundary="):
            return item.split("=", 1)[1].strip('"').encode("utf-8")
    raise ValueError("multipart boundary not found")


def _multipart_file_parts(body: bytes, boundary: bytes) -> list[tuple[str, bytes]]:
    marker = b"--" + boundary
    parts: list[tuple[str, bytes]] = []
    for raw_part in body.split(marker):
        raw_part = raw_part.strip(b"\r\n")
        if not raw_part or raw_part == b"--":
            continue
        if raw_part.endswith(b"--"):
            raw_part = raw_part[:-2].rstrip(b"\r\n")
        if b"\r\n\r\n" in raw_part:
            raw_headers, content = raw_part.split(b"\r\n\r\n", 1)
        elif b"\n\n" in raw_part:
            raw_headers, content = raw_part.split(b"\n\n", 1)
        else:
            continue
        headers = raw_headers.decode("utf-8", errors="replace")
        filename = _filename_from_headers(headers)
        if not filename:
            continue
        if content.endswith(b"\r\n"):
            content = content[:-2]
        elif content.endswith(b"\n"):
            content = content[:-1]
        parts.append((filename, content))
    return parts


def _filename_from_headers(headers: str) -> str | None:
    for line in headers.splitlines():
        if not line.lower().startswith("content-disposition:"):
            continue
        for item in line.split(";"):
            item = item.strip()
            if item.startswith("filename="):
                return item.split("=", 1)[1].strip().strip('"') or None
    return None


def _write_generated_pdf(upload_dir: Path, content: bytes) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = unique_path(upload_dir, f"uploaded_{stamp}.pdf")
    path.write_bytes(content)
    return path


def _extract_pdf_zip(content: bytes, upload_dir: Path) -> list[str]:
    saved: list[str] = []
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        for item in archive.infolist():
            if item.is_dir() or not item.filename.lower().endswith(".pdf"):
                continue
            with archive.open(item) as handle:
                path = _write_generated_pdf(upload_dir, handle.read())
            saved.append(path.name)
    return saved


def _links_for(directory: Path, kind: str, token: str) -> str:
    if not directory.exists():
        return ""
    suffix = ".xlsx" if kind == "excel" else ".json"
    items = []
    for path in sorted(directory.glob(f"*{suffix}")):
        name = html.escape(path.name)
        href = f"/download/{kind}/{quote(path.name)}?token={token}"
        items.append(f'<li><a href="{href}">{name}</a></li>')
    return "\n".join(items)


def main() -> None:
    parser = argparse.ArgumentParser(description="Temporary PDF/output transfer server for a VM.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--token", default=None)
    parser.add_argument("--max-upload-mb", type=int, default=2048)
    args = parser.parse_args()

    token = args.token or secrets.token_urlsafe(12)
    TransferRequestHandler.token = token
    TransferRequestHandler.max_upload_bytes = args.max_upload_mb * 1024 * 1024

    server = ThreadingHTTPServer((args.host, args.port), TransferRequestHandler)
    print("Transfer server started.")
    print(f"Open from local browser: http://<VM_PUBLIC_IP>:{args.port}/?token={token}")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
