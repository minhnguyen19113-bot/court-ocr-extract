from __future__ import annotations

import json
import logging
import time
import uuid
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from court_ocr_extract.models import OcrPage


LOGGER = logging.getLogger(__name__)


class RemoteWorkerError(RuntimeError):
    pass


class RemoteWorkerClient:
    def __init__(
        self,
        *,
        base_url: str,
        token: str = "",
        timeout: float = 180.0,
        retries: int = 2,
    ) -> None:
        if not base_url:
            raise RemoteWorkerError("GPU_WORKER_BASE_URL is required for remote worker mode.")
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.retries = retries

    @classmethod
    def from_settings(cls, settings) -> "RemoteWorkerClient":
        return cls(
            base_url=settings.gpu_worker_base_url,
            token=settings.gpu_worker_token,
            timeout=settings.gpu_worker_timeout_seconds,
            retries=settings.gpu_worker_retries,
        )

    def health(self) -> dict[str, Any]:
        return self._request_json("GET", "/health")

    def extract(self, text: str) -> dict[str, Any]:
        return self._request_json("POST", "/extract", {"text": text})

    def cleanup(self) -> dict[str, Any]:
        return self._request_json("POST", "/cleanup", {})

    def job_status(self, job_id: str | None = None) -> dict[str, Any]:
        suffix = "/job-status" if not job_id else f"/job-status?job_id={job_id}"
        return self._request_json("GET", suffix)

    def ocr_page(self, image_path: str | Path, page_number: int) -> OcrPage:
        payload = self._multipart_request(
            "/ocr-page",
            fields={"page_number": str(page_number)},
            file_field="image",
            file_path=Path(image_path),
        )
        page_payload = payload.get("page", payload)
        if not isinstance(page_payload, dict):
            raise RemoteWorkerError("Remote /ocr-page response must contain an OCR page object.")
        return OcrPage(**page_payload)

    def _request_json(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers = {"Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(
            self.base_url + path,
            data=data,
            headers=headers,
            method=method,
        )
        return self._open_with_retry(request)

    def _multipart_request(
        self,
        path: str,
        *,
        fields: dict[str, str],
        file_field: str,
        file_path: Path,
    ) -> dict[str, Any]:
        boundary = f"----court-ocr-{uuid.uuid4().hex}"
        body = bytearray()
        for name, value in fields.items():
            body.extend(f"--{boundary}\r\n".encode())
            body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
            body.extend(value.encode("utf-8"))
            body.extend(b"\r\n")
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(
            (
                f'Content-Disposition: form-data; name="{file_field}"; '
                f'filename="{file_path.name}"\r\n'
                "Content-Type: application/octet-stream\r\n\r\n"
            ).encode()
        )
        body.extend(file_path.read_bytes())
        body.extend(b"\r\n")
        body.extend(f"--{boundary}--\r\n".encode())

        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(
            self.base_url + path,
            data=bytes(body),
            headers=headers,
            method="POST",
        )
        return self._open_with_retry(request)

    def _open_with_retry(self, request: urllib.request.Request) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    raw = response.read().decode("utf-8")
                payload = json.loads(raw)
                if not isinstance(payload, dict):
                    raise RemoteWorkerError("Remote worker response must be a JSON object.")
                return payload
            except (urllib.error.URLError, json.JSONDecodeError, RemoteWorkerError) as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(min(2**attempt, 5))
        raise RemoteWorkerError(f"Remote worker request failed: {last_error}") from last_error


class RemoteOcrAdapter:
    def __init__(self, client: RemoteWorkerClient) -> None:
        self.client = client

    @classmethod
    def from_settings(cls, settings) -> "RemoteOcrAdapter":
        return cls(RemoteWorkerClient.from_settings(settings))

    def ocr_page(self, image_path: str | Path, page_number: int) -> OcrPage:
        return self.client.ocr_page(image_path, page_number)


class FallbackOcrAdapter:
    def __init__(self, primary, fallback, fallback_name: str = "local") -> None:
        self.primary = primary
        self.fallback = fallback
        self.fallback_name = fallback_name

    def ocr_page(self, image_path: str | Path, page_number: int) -> OcrPage:
        try:
            return self.primary.ocr_page(image_path, page_number)
        except RemoteWorkerError as exc:
            LOGGER.warning(
                "Remote OCR failed for page=%s; falling back to %s. error=%s",
                page_number,
                self.fallback_name,
                exc,
            )
            return self.fallback.ocr_page(image_path, page_number)
