from __future__ import annotations

from court_ocr_extract.extractor import extract_rule_based
from court_ocr_extract.models import ExtractorOutput, FieldValue


def anchor_support_output(text: str) -> ExtractorOutput:
    """Lightweight anchors for validation/support, not the primary extractor."""
    result = extract_rule_based(text)
    case_fields = {
        "loai_an": _field(result.case_info.loai_an, "heuristic_support"),
        "so_thu_ly": _field(result.case_info.so_thu_ly, "heuristic_support"),
        "ngay_thu_ly": _field(result.case_info.ngay_thu_ly, "heuristic_support"),
        "quan_he_phap_luat": _field(result.case_info.quan_he_phap_luat, "heuristic_support"),
        "chu_toa": _field(result.case_info.chu_toa, "heuristic_support"),
    }
    participants = []
    for participant in result.participants:
        participants.append(
            {
                "tu_cach_to_tung": _field(participant.tu_cach_to_tung, "heuristic_support"),
                "ho_ten": _field(participant.ho_ten, "heuristic_support"),
                "nam_sinh": _field(participant.nam_sinh, "heuristic_support"),
                "cccd": _field(participant.cccd, "heuristic_support"),
                "dia_chi": _field(participant.dia_chi, "heuristic_support"),
            }
        )
    return ExtractorOutput(method="heuristic_support", case_fields=case_fields, participants=participants)


def _field(value: str | None, method: str) -> FieldValue:
    return FieldValue(
        value=value,
        confidence=0.45 if value else 0.0,
        evidence_text=value,
        reasoning_brief="Anchor regex hỗ trợ kiểm tra, không phải extractor chính." if value else None,
        source_method=method,
    )
