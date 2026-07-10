from openpyxl import load_workbook

from court_ocr_extract.excel_writer import (
    EXCEL_HEADERS,
    write_excel,
    write_excel_from_results,
)
from court_ocr_extract.models import CaseInfo, ExtractionResult, Participant


def test_canonical_writer_creates_draft_workbook_contract(tmp_path):
    output_path = tmp_path / "synthetic_draft.xlsx"
    drafts = [
        {
            "case_id": "synthetic_case_001",
            "status": "success",
            "marker_found": True,
            "payload": {
                "case": {
                    "case_type": "Loại án synthetic",
                    "filing_number": "SYNTHETIC-001",
                },
                "participants": [
                    {
                        "procedural_role": "Vai trò synthetic",
                        "full_name": "Người kiểm tra synthetic",
                    }
                ],
            },
        }
    ]

    result_path = write_excel(drafts, output_path)
    workbook = load_workbook(result_path, read_only=True)

    assert workbook.sheetnames == ["DATA", "RUN_SUMMARY"]
    assert [cell.value for cell in workbook["DATA"][1]] == EXCEL_HEADERS
    assert workbook["DATA"].max_row == 2


def test_canonical_writer_creates_typed_result_workbook_contract(tmp_path):
    output_path = tmp_path / "synthetic_typed.xlsx"
    result = ExtractionResult(
        case_info=CaseInfo(
            loai_an="Loại án synthetic",
            so_thu_ly="SYNTHETIC-002",
        ),
        participants=[
            Participant(
                tu_cach_to_tung="Vai trò synthetic",
                ho_ten="Người kiểm tra synthetic",
            )
        ],
    )

    result_path = write_excel_from_results([result], output_path)
    workbook = load_workbook(result_path, read_only=True)

    assert workbook.sheetnames == ["Trich xuat"]
    assert [cell.value for cell in workbook["Trich xuat"][1]] == EXCEL_HEADERS
    assert workbook["Trich xuat"].max_row == 2
