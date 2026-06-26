from __future__ import annotations

import re
import unicodedata
from datetime import datetime

from court_ocr_extract.models import ExtractionResult, Participant


REQUIRED_CASE_FIELDS = {
    "loai_an": "LOẠI ÁN",
    "so_thu_ly": "SỐ THỤ LÝ",
    "ngay_thu_ly": "NGÀY THỤ LÝ",
    "quan_he_phap_luat": "QUAN HỆ PHÁP LUẬT",
    "chu_toa": "HỌ TÊN CHỦ TỌA",
}

REQUIRED_PARTICIPANT_FIELDS = {
    "tu_cach_to_tung": "TƯ CÁCH TỐ TỤNG",
    "ho_ten": "HỌ TÊN ĐƯƠNG SỰ",
    "nam_sinh": "NĂM SINH",
    "cccd": "CCCD",
    "dia_chi": "ĐỊA CHỈ",
}

VALID_ROLES = {
    "Bị cáo",
    "Bị hại",
    "Người bị hại",
    "Nguyên đơn",
    "Bị đơn",
    "Người có quyền lợi, nghĩa vụ liên quan",
    "Người liên quan",
    "Người làm chứng",
    "Đương sự",
}


def validate_extraction(result: ExtractionResult) -> ExtractionResult:
    warnings = list(result.warnings)
    if not result.marker_found:
        _append_unique(warnings, "Cần review: không tìm thấy marker NỘI DUNG VỤ ÁN trong phạm vi OCR.")

    missing_case = [
        label for field, label in REQUIRED_CASE_FIELDS.items() if not getattr(result.case_info, field)
    ]
    if missing_case:
        _append_unique(warnings, "Thiếu thông tin chung: " + ", ".join(missing_case))

    if result.case_info.ngay_thu_ly and not _valid_date(result.case_info.ngay_thu_ly):
        _append_unique(warnings, f"Ngày thụ lý không đúng DD/MM/YYYY: {result.case_info.ngay_thu_ly}")

    _validate_model_evidence(result, warnings)

    if not result.participants:
        _append_unique(warnings, "Không nhận diện được người tham gia tố tụng.")

    for participant in result.participants:
        _validate_participant(participant)

    if _has_low_confidence(result):
        _append_unique(warnings, "Cần review: có field confidence thấp hoặc thiếu căn cứ.")

    result.warnings = warnings
    result.metadata["review_required"] = bool(warnings)
    return result


def _validate_model_evidence(result: ExtractionResult, warnings: list[str]) -> None:
    text = result.text_before_marker or ""
    if not text.strip():
        return

    for field_key, label in REQUIRED_CASE_FIELDS.items():
        if field_key == "quan_he_phap_luat":
            continue
        _validate_field_evidence(result.case_info.field_metadata.get(field_key), label, text, warnings)

    for participant in result.participants:
        for field_key, label in REQUIRED_PARTICIPANT_FIELDS.items():
            _validate_field_evidence(participant.field_metadata.get(field_key), label, text, warnings)


def _validate_field_evidence(field, label: str, text: str, warnings: list[str]) -> None:
    if not field or not field.value or not _is_model_field(field):
        return
    evidence = field.evidence_text or field.source_text
    if not evidence:
        _append_unique(warnings, f"Cần review: field {label} thiếu evidence_text từ model.")
        return
    if not _contains_evidence(text, evidence):
        _append_unique(warnings, f"Cần review: evidence_text của field {label} không khớp OCR text.")


def _is_model_field(field) -> bool:
    source = (field.source_method or "").lower()
    return "llm" in source or "remote" in source or "model" in source


def _validate_participant(participant: Participant) -> None:
    notes = _split_notes(participant.ghi_chu)
    missing = [
        label
        for field, label in REQUIRED_PARTICIPANT_FIELDS.items()
        if field != "cccd" and not getattr(participant, field)
    ]
    if missing:
        notes.append("Thiếu: " + ", ".join(missing))

    if participant.tu_cach_to_tung and participant.tu_cach_to_tung not in VALID_ROLES:
        notes.append(f"Tư cách tố tụng cần kiểm tra: {participant.tu_cach_to_tung}")

    if participant.nam_sinh and not re.fullmatch(r"\d{4}", participant.nam_sinh):
        notes.append(f"Năm sinh không phải 4 chữ số: {participant.nam_sinh}")

    if participant.cccd:
        digits = re.sub(r"\D", "", participant.cccd)
        if len(digits) not in {9, 12}:
            notes.append("CCCD/CMND không phải 9 hoặc 12 số.")
        else:
            participant.cccd = digits

    participant.ghi_chu = "; ".join(_dedupe(notes)) or None


def _has_low_confidence(result: ExtractionResult, threshold: float = 0.5) -> bool:
    for field in result.case_info.field_metadata.values():
        if field.value and field.confidence is not None and field.confidence < threshold:
            return True
    for participant in result.participants:
        for field in participant.field_metadata.values():
            if field.value and field.confidence is not None and field.confidence < threshold:
                return True
    return False


def _valid_date(value: str) -> bool:
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", value):
        return False
    try:
        datetime.strptime(value, "%d/%m/%Y")
    except ValueError:
        return False
    return True


def _contains_evidence(text: str, evidence: str) -> bool:
    evidence_key = _evidence_key(evidence)
    if not evidence_key:
        return False
    text_key = _evidence_key(text)
    if evidence_key in text_key:
        return True
    compact_evidence = evidence_key.replace(" ", "")
    compact_text = text_key.replace(" ", "")
    return bool(compact_evidence and compact_evidence in compact_text)


def _evidence_key(value: str) -> str:
    value = unicodedata.normalize("NFC", value or "").casefold()
    value = re.sub(r"[^\w\sÀ-ỹ]", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


def _split_notes(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)
