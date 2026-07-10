from __future__ import annotations

from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from court_ocr_extract.models import ExtractionResult, Participant
from court_ocr_extract.validation import row_needs_review


EXCEL_HEADERS = [
    "LOẠI ÁN",
    "SỐ THỤ LÝ",
    "NGÀY THỤ LÝ (DD/MM/YYYY)",
    "QUAN HỆ PHÁP LUẬT",
    "TƯ CÁCH TỐ TỤNG",
    "HỌ TÊN ĐƯƠNG SỰ",
    "NĂM SINH",
    "CCCD",
    "ĐỊA CHỈ",
    "HỌ TÊN CHỦ TỌA",
    "GHI CHÚ",
]


def rows_from_payload(case_id: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    case = payload.get("case") or {}
    participants = payload.get("participants") or [
        {"warnings": ["No participant row extracted."]}
    ]
    rows: list[dict[str, Any]] = []
    document_note = "; ".join(payload.get("document_warnings", []))
    for participant in participants:
        participant_note = "; ".join(participant.get("warnings", []))
        note = "; ".join(item for item in [document_note, participant_note] if item)
        rows.append(
            {
                "LOẠI ÁN": case.get("case_type"),
                "SỐ THỤ LÝ": case.get("filing_number"),
                "NGÀY THỤ LÝ (DD/MM/YYYY)": case.get("filing_date"),
                "QUAN HỆ PHÁP LUẬT": case.get("legal_relationship"),
                "TƯ CÁCH TỐ TỤNG": participant.get("procedural_role"),
                "HỌ TÊN ĐƯƠNG SỰ": participant.get("full_name"),
                "NĂM SINH": participant.get("birth_year"),
                "CCCD": participant.get("id_number"),
                "ĐỊA CHỈ": participant.get("address"),
                "HỌ TÊN CHỦ TỌA": case.get("presiding_judge"),
                "GHI CHÚ": note or None,
                "_case_id": case_id,
                "_needs_review": row_needs_review(payload, participant),
            }
        )
    return rows


def rows_from_result(result: ExtractionResult) -> list[dict[str, str | None]]:
    participants = result.participants or [
        Participant(ghi_chu="Không nhận diện được người tham gia tố tụng")
    ]
    rows: list[dict[str, str | None]] = []
    common_note = "; ".join(result.warnings)
    for participant in participants:
        note = "; ".join(item for item in [participant.ghi_chu, common_note] if item)
        rows.append(
            {
                "LOẠI ÁN": result.case_info.loai_an,
                "SỐ THỤ LÝ": result.case_info.so_thu_ly,
                "NGÀY THỤ LÝ (DD/MM/YYYY)": result.case_info.ngay_thu_ly,
                "QUAN HỆ PHÁP LUẬT": result.case_info.quan_he_phap_luat,
                "TƯ CÁCH TỐ TỤNG": participant.tu_cach_to_tung,
                "HỌ TÊN ĐƯƠNG SỰ": participant.ho_ten,
                "NĂM SINH": participant.nam_sinh,
                "CCCD": participant.cccd,
                "ĐỊA CHỈ": participant.dia_chi,
                "HỌ TÊN CHỦ TỌA": result.case_info.chu_toa,
                "GHI CHÚ": note or None,
            }
        )
    return rows


def write_excel(
    draft_records: list[dict[str, Any]],
    output_path: str | Path,
    *,
    run_summary: dict[str, Any] | None = None,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    data_sheet = workbook.active
    data_sheet.title = "DATA"
    data_sheet.append(EXCEL_HEADERS)
    for draft in draft_records:
        for row in rows_from_payload(draft["case_id"], draft["payload"]):
            data_sheet.append([row.get(header) for header in EXCEL_HEADERS])
    _format_data_sheet(data_sheet)

    summary_sheet = workbook.create_sheet("RUN_SUMMARY")
    summary = run_summary or build_run_summary(draft_records)
    for key, value in summary.items():
        summary_sheet.append([key, value])
    summary_sheet.column_dimensions["A"].width = 34
    summary_sheet.column_dimensions["B"].width = 42

    workbook.save(output_path)
    return output_path


def write_excel_from_results(
    results: list[ExtractionResult],
    output_path: str | Path,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    data_sheet = workbook.active
    data_sheet.title = "Trich xuat"
    data_sheet.append(EXCEL_HEADERS)
    for result in results:
        for row in rows_from_result(result):
            data_sheet.append([row.get(header) for header in EXCEL_HEADERS])
    _format_data_sheet(data_sheet)
    workbook.save(output_path)
    return output_path


def build_run_summary(draft_records: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(draft_records)
    failed = sum(1 for record in draft_records if record.get("status") != "success")
    marker_not_found = sum(1 for record in draft_records if not record.get("marker_found"))
    rows = [row for record in draft_records for row in rows_from_payload(record["case_id"], record["payload"])]
    review_rows = sum(1 for row in rows if row.get("_needs_review"))
    return {
        "Tổng số PDF": total,
        "Số file xử lý thành công": total - failed,
        "Số file lỗi": failed,
        "Số dòng cần review": review_rows,
        "Số file không tìm thấy marker": marker_not_found,
        "Số dòng thiếu thông tin quan trọng": _missing_important_count(rows),
        "OCR backend": _joined_unique(record.get("ocr_backend") for record in draft_records),
        "Extractor backend": _joined_unique(record.get("extractor_backend") for record in draft_records),
        "Debug visual run id": _joined_unique(record.get("debug_run_id") for record in draft_records),
    }


def _format_data_sheet(sheet) -> None:
    header_fill = PatternFill("solid", fgColor="D9EAF7")
    header_font = Font(bold=True, color="000000")
    for cell in sheet[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    widths = [16, 20, 22, 32, 28, 28, 12, 18, 48, 28, 44]
    for index, width in enumerate(widths, start=1):
        sheet.column_dimensions[get_column_letter(index)].width = width
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions


def _missing_important_count(rows: list[dict[str, Any]]) -> int:
    important = ["SỐ THỤ LÝ", "NGÀY THỤ LÝ (DD/MM/YYYY)", "TƯ CÁCH TỐ TỤNG", "HỌ TÊN ĐƯƠNG SỰ"]
    return sum(1 for row in rows if any(not row.get(key) for key in important))


def _joined_unique(values) -> str:
    clean = [str(value) for value in values if value]
    return ", ".join(sorted(set(clean)))
