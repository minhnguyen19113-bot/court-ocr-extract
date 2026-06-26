from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from court_ocr_extract.config import get_settings
from court_ocr_extract.extraction.local_llm_extractor import LocalLLMExtractor


SYNTHETIC_OCR = """
TÒA ÁN NHÂN DÂN HUYỆN A
BẢN ÁN HÌNH SỰ SƠ THẨM
Vụ án hình sự thụ lý số: 12/2025/TLST-HS ngày 03 tháng 04 năm 2025.
Thẩm phán - Chủ tọa phiên tòa: Người Chủ Tọa.
Bị cáo: Người Tham Gia A, sinh năm 1990; CCCD số 012345678901; nơi cư trú: xã B, huyện C.
Bị hại: Người Tham Gia B, sinh năm 1985; địa chỉ: phường D, thành phố E.
NỘI DUNG VỤ ÁN
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test local LLM extraction using synthetic text.")
    parser.add_argument("--provider", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--base-url", default=None)
    args = parser.parse_args()

    settings = get_settings()
    settings.enable_local_llm = True
    settings.enable_mock_local_llm = False
    if args.provider:
        settings.local_llm_provider = args.provider
    if args.model:
        settings.local_llm_model = args.model
    if args.base_url:
        settings.local_llm_base_url = args.base_url

    print("Local LLM smoke test")
    print(f"  provider: {settings.local_llm_provider}")
    print(f"  model: {settings.local_llm_model}")
    print(f"  base_url: {settings.local_llm_base_url}")

    output = LocalLLMExtractor(settings).extract(SYNTHETIC_OCR)
    payload = {
        "method": output.method,
        "case_non_empty": sum(1 for field in output.case_fields.values() if field.value),
        "participants": len(output.participants),
        "participant_non_empty": [
            sum(1 for field in participant.values() if field.value)
            for participant in output.participants
        ],
        "warnings_count": len(output.warnings),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if output.method != "local_llm" or payload["case_non_empty"] < 3 or payload["participants"] < 1:
        raise SystemExit("Local LLM smoke test did not produce enough structured fields.")


if __name__ == "__main__":
    main()
