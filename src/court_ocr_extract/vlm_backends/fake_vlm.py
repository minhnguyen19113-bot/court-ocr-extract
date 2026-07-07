from __future__ import annotations

import time
from pathlib import Path

from court_ocr_extract.vlm_backends.base import VLMBackendStatus, VLMPageResult


class FakeVLMBackend:
    provider = "fake"
    model_name = "fake-vlm-contract"

    def check_available(self) -> VLMBackendStatus:
        return VLMBackendStatus("fake", True, "Fake VLM backend is available for contract tests.")

    def read_page(self, image_path: Path, prompt: str, page_number: int) -> VLMPageResult:
        started = time.perf_counter()
        text = f"""# PAGE {page_number}

## raw_text_lines

* TOA AN NHAN DAN - CONTRACT FIXTURE
* So: 01/2026/DS-ST
* Ngay 01 thang 01 nam 2026
* Nguyen don: Nguoi Tham Gia A, sinh nam 1980
* Bi don: Nguoi Tham Gia B, sinh nam 1985
* NOI DUNG VU AN
* Phan sau marker chi dung de kiem tra contract.

## tables

Khong co

## uncertain_regions

Khong co
"""
        return VLMPageResult(
            page_index=page_number,
            text=text,
            warnings=[],
            timing={"total_seconds": round(time.perf_counter() - started, 6)},
            raw_response=text,
            unreadable_count=0,
        )

