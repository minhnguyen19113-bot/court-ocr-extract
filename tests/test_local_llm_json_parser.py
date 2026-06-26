import pytest

from court_ocr_extract.local_llm.json_parser import (
    StrictJsonError,
    normalize_extraction_payload,
    parse_json_object,
)


def test_parse_json_object_rejects_markdown_free_text():
    with pytest.raises(StrictJsonError):
        parse_json_object("not json")


def test_parse_json_object_accepts_json_fence():
    payload = parse_json_object('```json\n{"case_type": null}\n```')

    assert payload["case_type"] is None


def test_normalize_public_payload_keeps_evidence_by_field():
    payload = normalize_extraction_payload(
        {
            "case_type": "Hình sự",
            "docket_number": "12/2025/TLST-HS",
            "docket_date": None,
            "legal_relationship": None,
            "presiding_judge": None,
            "parties": [
                {
                    "litigation_role": "Bị cáo",
                    "full_name": "Người Tham Gia A",
                    "birth_year": None,
                    "citizen_id": None,
                    "address": None,
                    "evidence_by_field": {
                        "full_name": "Bị cáo: Người Tham Gia A",
                    },
                }
            ],
            "warnings": [],
            "confidence_by_field": {
                "case_type": 0.9,
                "docket_number": 0.9,
                "full_name": 0.8,
            },
            "evidence_by_field": {
                "docket_number": "thụ lý số: 12/2025/TLST-HS",
            },
        }
    )

    assert payload["case_info"]["so_thu_ly"]["evidence_text"] == "thụ lý số: 12/2025/TLST-HS"
    assert payload["participants"][0]["ho_ten"]["evidence_text"] == "Bị cáo: Người Tham Gia A"
