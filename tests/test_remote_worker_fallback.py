from pathlib import Path

from court_ocr_extract.models import OcrPage
from court_ocr_extract.remote_worker.client import FallbackOcrAdapter, RemoteWorkerError


class FailingRemoteAdapter:
    def ocr_page(self, image_path: str | Path, page_number: int) -> OcrPage:
        raise RemoteWorkerError("synthetic remote outage")


class LocalFallbackAdapter:
    def ocr_page(self, image_path: str | Path, page_number: int) -> OcrPage:
        return OcrPage(page_number=page_number, text="synthetic fallback text")


def test_remote_ocr_adapter_falls_back_to_local():
    adapter = FallbackOcrAdapter(
        FailingRemoteAdapter(),
        LocalFallbackAdapter(),
        fallback_name="local",
    )

    page = adapter.ocr_page("synthetic.png", page_number=1)

    assert page.page_text == "synthetic fallback text"
