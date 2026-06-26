import os

from court_ocr_extract.config import Settings
from court_ocr_extract.extraction.local_llm_extractor import MockLocalLLMExtractor
from court_ocr_extract.local_llm.json_parser import normalize_extraction_payload, parse_json_object


def test_mock_local_llm_returns_field_metadata_shape():
    text = (
        "BẢN ÁN HÌNH SỰ SƠ THẨM\n"
        "Vụ án hình sự thụ lý số: 12/2025/TLST-HS ngày 03 tháng 04 năm 2025 "
        "về tội \"Trộm cắp tài sản\".\n"
        "Thẩm phán - Chủ tọa phiên tòa: Người Chủ Tọa\n"
        "Bị cáo: Người Tham Gia A, sinh năm 1990; CCCD số 012345678901; "
        "nơi cư trú: xã B, huyện C.\n"
    )

    output = MockLocalLLMExtractor().extract(text)

    assert output.method == "mock_local_llm"
    assert output.case_fields["so_thu_ly"].value == "12/2025/TLST-HS"
    assert output.case_fields["so_thu_ly"].confidence is not None
    assert output.case_fields["so_thu_ly"].evidence_text


def test_public_local_llm_schema_maps_to_internal_schema():
    payload = parse_json_object(
        """
        {
          "case_type": "Hình sự",
          "docket_number": "12/2025/TLST-HS",
          "docket_date": "03/04/2025",
          "legal_relationship": "Trộm cắp tài sản",
          "presiding_judge": "Người Chủ Tọa",
          "parties": [{"litigation_role": "Bị cáo", "full_name": "Người Tham Gia A", "birth_year": "1990", "citizen_id": null, "address": null}],
          "warnings": [],
          "confidence_by_field": {"docket_number": 0.9, "full_name": 0.8},
          "reasoning_summary": "Suy ra từ cụm về tội."
        }
        """
    )

    normalized = normalize_extraction_payload(payload)

    assert normalized["case_info"]["so_thu_ly"]["value"] == "12/2025/TLST-HS"
    assert normalized["participants"][0]["ho_ten"]["value"] == "Người Tham Gia A"


def test_settings_default_disables_cloud_llm():
    os.environ["ENABLE_CLOUD_LLM_EXTRACTION"] = "false"
    os.environ["ENABLE_LOCAL_LLM_EXTRACTION"] = "true"
    settings = Settings()

    assert settings.enable_cloud_llm is False
    assert settings.enable_local_llm is True
