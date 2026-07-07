from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from court_ocr_extract.early_stop import detect_marker_across_pages
from court_ocr_extract.ocr_backends.base import OCRPage, OCRResult
from court_ocr_extract.ocr_cache import OCRCacheRecord
from court_ocr_extract.pdf_render import render_pdf_pages
from court_ocr_extract.settings import get_settings
from court_ocr_extract.vlm_backends import get_vlm_backend
from court_ocr_extract.vlm_backends.base import VLMBackend, VLMPageResult


DEFAULT_VLM_PAGE_PROMPT = """Bạn là bộ đọc ảnh trang PDF văn bản tòa án Việt Nam.

Nhiệm vụ: chép lại nội dung nhìn thấy trên ảnh trang, không trích xuất trường dữ liệu pháp lý ở bước này.

Quy tắc bắt buộc:
- Không tóm tắt.
- Không suy đoán.
- Không tự thêm thông tin không nhìn thấy trên ảnh.
- Giữ thứ tự dòng từ trên xuống dưới, trái sang phải.
- Giữ nguyên số, ngày tháng, tên riêng, địa chỉ, CCCD/CMND nếu đọc được.
- Nếu một đoạn không đọc được, ghi đúng: [KHÔNG ĐỌC ĐƯỢC].
- Nếu không chắc một ký tự/từ, giữ gần đúng và thêm vào uncertain_regions.
- Nếu có bảng, giữ dạng markdown table nếu có thể.
- Không giải thích ngoài markdown.

Trả về markdown đúng cấu trúc:

# PAGE {page_number}

## raw_text_lines

* dòng 1
* dòng 2

## tables

[nếu không có bảng ghi: Không có]

## uncertain_regions

* mô tả ngắn vùng/dòng không chắc, hoặc "Không có"
"""


def read_pdf_pages_with_vlm(
    pdf_path: str | Path,
    *,
    case_id: str,
    source_index: int,
    pdf_hash: str | None,
    output_dir: str | Path,
    max_pages: int | None = None,
    backend: VLMBackend | None = None,
    prompt: str = DEFAULT_VLM_PAGE_PROMPT,
) -> OCRCacheRecord:
    settings = get_settings()
    page_limit = _page_limit(max_pages, settings.vlm_max_pages)
    rendered = render_pdf_pages(
        pdf_path,
        Path(output_dir) / "rendered_pages",
        dpi=settings.vlm_render_dpi,
        max_pages=page_limit,
    )
    return read_images_with_vlm(
        [page.image_path for page in rendered],
        case_id=case_id,
        source_index=source_index,
        pdf_hash=pdf_hash,
        output_dir=output_dir,
        backend=backend,
        prompt=prompt,
        page_numbers=[page.page_number for page in rendered],
    )


def read_images_with_vlm(
    image_paths: list[str | Path],
    *,
    case_id: str,
    source_index: int,
    pdf_hash: str | None,
    output_dir: str | Path,
    backend: VLMBackend | None = None,
    prompt: str = DEFAULT_VLM_PAGE_PROMPT,
    page_numbers: list[int] | None = None,
) -> OCRCacheRecord:
    settings = get_settings()
    backend = backend or get_vlm_backend(settings)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    page_results: list[VLMPageResult] = []
    pages: list[OCRPage] = []
    warnings: list[str] = []
    for offset, raw_path in enumerate(image_paths, start=1):
        page_number = page_numbers[offset - 1] if page_numbers else offset
        image_path = Path(raw_path)
        result = backend.read_page(image_path, prompt, page_number)
        page_results.append(result)
        warnings.extend(result.warnings)
        _write_page_artifacts(output_dir, result)
        pages.append(
            OCRPage(
                page_index=page_number,
                text=result.text,
                image_path=str(image_path),
            )
        )

    combined = "\n\n".join(result.text for result in page_results).strip()
    (output_dir / "combined_vlm_text.md").write_text(combined, encoding="utf-8")
    marker = detect_marker_across_pages([result.text for result in page_results], settings.stop_marker)
    backend_name = safe_vlm_backend_name(backend.provider, backend.model_name)
    if any(result.unreadable_count for result in page_results):
        warnings.append("VLM reported unreadable regions.")
    ocr_result = OCRResult(
        backend=backend_name,
        status="success" if combined else "failed",
        pages_processed=len(page_results),
        marker_found=marker.found,
        marker_page=marker.page_index,
        text=combined,
        pages=pages,
        warnings=_dedupe(warnings),
        timing={
            "total_seconds": round(
                sum(result.timing.get("total_seconds", 0.0) for result in page_results),
                6,
            )
        },
    )
    return OCRCacheRecord(
        case_id=case_id,
        source_index=source_index,
        pdf_hash=pdf_hash,
        result=ocr_result,
    )


def safe_vlm_backend_name(provider: str, model_name: str) -> str:
    raw = f"vlm_{provider}_{model_name}".lower()
    return re.sub(r"[^a-z0-9_]+", "_", raw).strip("_")


def _write_page_artifacts(output_dir: Path, result: VLMPageResult) -> None:
    stem = f"page_{result.page_index:03d}"
    (output_dir / f"{stem}.md").write_text(result.text, encoding="utf-8")
    payload: dict[str, Any] = {
        "page_index": result.page_index,
        "text": result.text,
        "warnings": result.warnings,
        "timing": result.timing,
        "unreadable_count": result.unreadable_count,
    }
    if result.raw_response is not None:
        payload["raw_response"] = result.raw_response
    (output_dir / f"{stem}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _page_limit(max_pages: int | None, configured_max_pages: int) -> int | None:
    if max_pages is not None:
        return None if max_pages == 0 else max_pages
    return None if configured_max_pages == 0 else configured_max_pages


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            result.append(value)
            seen.add(value)
    return result

