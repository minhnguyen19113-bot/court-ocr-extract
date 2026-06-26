from __future__ import annotations

from court_ocr_extract.extraction.local_llm_extractor import LocalLLMExtractor
from court_ocr_extract.extraction.merge import merge_extractor_outputs
from court_ocr_extract.extraction.rule_support import anchor_support_output
from court_ocr_extract.models import ExtractionResult


SECURITY_WARNING = (
    "Dữ liệu bản án có thể chứa thông tin cá nhân và dữ liệu tố tụng nhạy cảm. "
    "Cloud LLM không được bật mặc định. Chỉ bật khi đã có căn cứ pháp lý, "
    "ẩn danh hóa dữ liệu và chấp thuận bảo mật rõ ràng."
)


def extract_with_cloud_llm_if_enabled(text: str, settings) -> ExtractionResult | None:
    if not getattr(settings, "enable_cloud_llm", False):
        return None
    raise RuntimeError(SECURITY_WARNING + " Cloud LLM adapter chỉ là interface tùy chọn.")


def extract_with_llm_if_enabled(text: str, settings) -> ExtractionResult | None:
    """Backward-compatible local extraction wrapper."""
    if not getattr(settings, "enable_local_llm", True):
        return None
    primary = LocalLLMExtractor(settings).extract(text)
    support = anchor_support_output(text)
    return merge_extractor_outputs(
        source_file=None,
        text_before_marker=text,
        marker_found=True,
        marker_text=None,
        marker_page=None,
        primary=primary,
        support=support,
    )


def correct_with_llm_if_enabled(text: str, settings) -> str:
    if not getattr(settings, "enable_local_llm_correction", False):
        return text
    raise RuntimeError("Local LLM correction chưa được triển khai trong baseline này.")
