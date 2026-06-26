from __future__ import annotations

import re
from dataclasses import dataclass

from court_ocr_extract.models import CaseInfo, ExtractionResult, Participant
from court_ocr_extract.normalizer import text_before_noi_dung


ROLE_LABEL_RE = re.compile(
    r"(?P<label>"
    r"Các bị cáo|Bị cáo|Người bị hại|Bị hại|"
    r"Người có quyền lợi[, ]+(?:và\s+)?nghĩa vụ liên quan|"
    r"Người có quyền lợi[, ]+nghĩa vụ liên quan|"
    r"Người liên quan|Người làm chứng"
    r")\s*[:：]?",
    re.IGNORECASE,
)

ADDRESS_LABEL_RE = (
    r"nơi cư trú|nơi cư trú hiện nay|địa chỉ|trú tại|cư trú tại|"
    r"nơi đăng ký hộ khẩu thường trú|đăng ký hộ khẩu thường trú|ĐKHKTT|HKTT|"
    r"hộ khẩu thường trú|chỗ ở hiện nay|chỗ ở"
)

ADDRESS_STOP_RE = re.compile(
    r"\s*;\s*(?:nghề nghiệp|trình độ|dân tộc|quốc tịch|giới tính|con ông|con bà|"
    r"tiền án|tiền sự|nhân thân|bị bắt|bị tạm giữ|bị tạm giam|có mặt|vắng mặt|"
    r"CCCD|CMND|Căn cước|Chứng minh)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RoleBlock:
    role: str
    text: str


def extract_rule_based(text: str, source_file: str | None = None) -> ExtractionResult:
    header_text, marker = text_before_noi_dung(text)
    case_info = extract_case_info(header_text)
    participants = extract_participants(header_text)

    warnings: list[str] = []
    if not marker.found:
        warnings.append("Không tìm thấy marker NỘI DUNG VỤ ÁN; đã trích xuất trên OCR text hiện có.")

    return ExtractionResult(
        source_file=source_file,
        marker_found=marker.found,
        marker_text=marker.text,
        case_info=case_info,
        participants=participants,
        warnings=warnings,
    )


def extract_case_info(text: str) -> CaseInfo:
    return CaseInfo(
        loai_an=extract_loai_an(text),
        so_thu_ly=extract_so_thu_ly(text),
        ngay_thu_ly=extract_ngay_thu_ly(text),
        quan_he_phap_luat=extract_quan_he_phap_luat(text),
        chu_toa=extract_chu_toa(text),
    )


def extract_so_thu_ly(text: str) -> str | None:
    patterns = [
        r"(?:thụ\s*lý\s*số|số\s*thụ\s*lý)\s*[:：.]?\s*([0-9]{1,5}\s*/\s*[0-9]{4}\s*/\s*[A-ZĐ0-9/-]+)",
        r"(?:vụ\s*án\s*hình\s*sự\s*)?thụ\s*lý\s*(?:sơ\s*thẩm\s*)?số\s*[:：.]?\s*([0-9]{1,5}\s*/\s*[0-9]{4}\s*/\s*[A-ZĐ0-9/-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return _clean_code(match.group(1))
    return None


def extract_ngay_thu_ly(text: str) -> str | None:
    window_match = re.search(
        r"(?:thụ\s*lý\s*số|số\s*thụ\s*lý).{0,180}?"
        r"(ngày\s+\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{4})",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if window_match:
        parsed = parse_vietnamese_date(window_match.group(1))
        if parsed:
            return parsed

    generic_match = re.search(
        r"\bngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})",
        text,
        flags=re.IGNORECASE,
    )
    if generic_match:
        return _format_date(generic_match.group(1), generic_match.group(2), generic_match.group(3))
    return None


def extract_loai_an(text: str) -> str | None:
    if re.search(r"\b(HÌNH\s*SỰ|Hinh\s*su|HS-ST|HSST|TLST-HS|TLPT-HS)\b", text, re.IGNORECASE):
        return "Hình sự"
    if re.search(r"\bDÂN\s*SỰ|DS-ST|TLST-DS\b", text, re.IGNORECASE):
        return "Dân sự"
    if re.search(r"\bHÔN\s*NHÂN|HNGĐ\b", text, re.IGNORECASE):
        return "Hôn nhân gia đình"
    if re.search(r"\bKINH\s*DOANH|KDTM\b", text, re.IGNORECASE):
        return "Kinh doanh thương mại"
    if re.search(r"\bLAO\s*ĐỘNG|LĐ-ST\b", text, re.IGNORECASE):
        return "Lao động"
    return None


def extract_quan_he_phap_luat(text: str) -> str | None:
    criminal_patterns = [
        r"về\s+tội\s+[\"“”']?([^\"“”'\n;.]+)",
        r"tội\s+danh\s*[:：]\s*([^\n;.]+)",
    ]
    for pattern in criminal_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return _clean_phrase(match.group(1))

    civil_patterns = [
        r"quan\s+hệ\s+pháp\s+luật\s*[:：]\s*([^\n;.]+)",
        r"V[/\\]v\s*[:：]?\s*([^\n;.]+)",
        r"về\s+việc\s*[:：]?\s*([^\n;.]+)",
    ]
    for pattern in civil_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return _clean_phrase(match.group(1))
    return None


def extract_chu_toa(text: str) -> str | None:
    patterns = [
        r"Thẩm\s*phán\s*[-–]\s*Chủ\s*tọa\s*phiên\s*tòa\s*[:：]\s*([^\n;]+)",
        r"Chủ\s*tọa\s*phiên\s*tòa\s*[:：]\s*([^\n;]+)",
        r"Thẩm\s*phán\s*chủ\s*tọa\s*[:：]\s*([^\n;]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return _clean_person_name(match.group(1))
    return None


def extract_participants(text: str) -> list[Participant]:
    participants: list[Participant] = []
    for block in _role_blocks(text):
        for person_text in _split_people(block.text):
            person = extract_person(person_text, role=block.role)
            if person.ho_ten or person.raw_text:
                participants.append(person)
    return participants


def extract_person(text: str, role: str) -> Participant:
    raw = _clean_person_block(text)
    return Participant(
        tu_cach_to_tung=role,
        ho_ten=extract_person_name(raw),
        nam_sinh=extract_birth_year(raw),
        cccd=extract_identity_number(raw),
        dia_chi=extract_address(raw),
        raw_text=raw,
    )


def extract_person_name(text: str) -> str | None:
    prefix = re.split(
        r"\b(?:sinh|SN|năm sinh|giới tính|nghề nghiệp|quốc tịch|dân tộc|địa chỉ|nơi cư trú|"
        r"trú tại|cư trú tại|HKTT|ĐKHKTT|CCCD|CMND|Căn cước|Chứng minh)\b",
        text,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    prefix = re.split(r"[;,]", prefix, maxsplit=1)[0]
    prefix = re.sub(r"^\s*(?:gồm|là|ông|bà|anh|chị|bị cáo|bị hại)\s+", "", prefix, flags=re.I)
    prefix = re.sub(r"^\s*\d+\s*[.)-]\s*", "", prefix)
    prefix = _clean_person_name(prefix)

    if _looks_like_person_name(prefix):
        return prefix

    match = re.search(
        r"(?:ông|bà|anh|chị)?\s*([A-ZÀ-Ỵ][A-Za-zÀ-ỹ'.-]+(?:\s+[A-ZÀ-Ỵ][A-Za-zÀ-ỹ'.-]+){1,7})",
        text,
    )
    if match:
        candidate = _clean_person_name(match.group(1))
        if _looks_like_person_name(candidate):
            return candidate
    return None


def extract_birth_year(text: str) -> str | None:
    patterns = [
        r"(?:sinh\s*năm|năm\s*sinh|SN)\s*[:：]?\s*(\d{4})",
        r"sinh\s*ngày\s*\d{1,2}[/-]\d{1,2}[/-](\d{4})",
        r"sinh\s*ngày\s*\d{1,2}\s*tháng\s*\d{1,2}\s*năm\s*(\d{4})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def extract_identity_number(text: str) -> str | None:
    match = re.search(
        r"(?:CCCD|CMND|Căn\s*cước\s*công\s*dân|Chứng\s*minh\s*nhân\s*dân|"
        r"số\s*định\s*danh\s*cá\s*nhân)\D{0,25}(\d(?:\D?\d){8}(?:\D?\d{3})?)",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    digits = re.sub(r"\D", "", match.group(1))
    return digits if len(digits) in {9, 12} else digits


def extract_address(text: str) -> str | None:
    match = re.search(rf"(?:{ADDRESS_LABEL_RE})\s*[:：]?\s*(.+)$", text, flags=re.IGNORECASE)
    if not match:
        return None
    address = match.group(1).strip()
    stop = ADDRESS_STOP_RE.search(address)
    if stop:
        address = address[: stop.start()]
    address = re.sub(r"\s+", " ", address).strip(" .;:-")
    return address or None


def parse_vietnamese_date(value: str) -> str | None:
    vn_match = re.search(
        r"ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})",
        value,
        flags=re.IGNORECASE,
    )
    if vn_match:
        return _format_date(vn_match.group(1), vn_match.group(2), vn_match.group(3))

    slash_match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", value)
    if slash_match:
        return _format_date(slash_match.group(1), slash_match.group(2), slash_match.group(3))
    return None


def _role_blocks(text: str) -> list[RoleBlock]:
    matches = list(ROLE_LABEL_RE.finditer(text))
    blocks: list[RoleBlock] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block_text = text[start:end].strip(" :：\n\t")
        if block_text:
            blocks.append(RoleBlock(role=_canonical_role(match.group("label")), text=block_text))
    return blocks


def _split_people(block: str) -> list[str]:
    block = re.sub(r"^\s*(?:gồm|bao gồm)\s*[:：]?\s*", "", block, flags=re.IGNORECASE)
    numbered = re.split(r"(?:^|\n)\s*\d{1,2}\s*[.)]\s*", block)
    numbered = [item.strip() for item in numbered if item.strip()]
    if len(numbered) > 1:
        return numbered
    return [block.strip()] if block.strip() else []


def _canonical_role(label: str) -> str:
    normalized = re.sub(r"\s+", " ", label.strip()).lower()
    if "bị cáo" in normalized:
        return "Bị cáo"
    if "bị hại" in normalized:
        return "Bị hại"
    if "quyền lợi" in normalized or "liên quan" in normalized:
        return "Người có quyền lợi, nghĩa vụ liên quan"
    if "làm chứng" in normalized:
        return "Người làm chứng"
    return label.strip()


def _clean_person_block(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip(" .;:-")
    text = re.sub(r"^\s*(?:gồm|là)\s*[:：]?\s*", "", text, flags=re.I)
    return text


def _clean_person_name(value: str) -> str:
    value = re.sub(r"\([^)]*\)", "", value)
    value = re.sub(r"\s+", " ", value).strip(" ,.;:-")
    value = re.sub(r"^(?:Ông|Bà|Anh|Chị)\s+", "", value, flags=re.IGNORECASE)
    return value


def _looks_like_person_name(value: str) -> bool:
    if not value or len(value) < 5:
        return False
    if any(char.isdigit() for char in value):
        return False
    words = value.split()
    return 2 <= len(words) <= 8


def _clean_code(value: str) -> str:
    return re.sub(r"\s+", "", value).strip(" .;:")


def _clean_phrase(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" .;:\"'“”")


def _format_date(day: str, month: str, year: str) -> str | None:
    day_int = int(day)
    month_int = int(month)
    if not (1 <= day_int <= 31 and 1 <= month_int <= 12):
        return None
    return f"{day_int:02d}/{month_int:02d}/{year}"
