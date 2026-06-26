from court_ocr_extract.extraction.validators import validate_extraction
from court_ocr_extract.models import CaseInfo, ExtractionResult, FieldValue, Participant


def test_validator_flags_missing_marker_and_bad_identity():
    result = ExtractionResult(
        marker_found=False,
        case_info=CaseInfo(ngay_thu_ly="03/04/2025"),
        participants=[Participant(ho_ten="Người Tham Gia A", nam_sinh="1990", cccd="12345")],
    )

    validated = validate_extraction(result)

    assert any("marker" in warning for warning in validated.warnings)
    assert "CCCD/CMND" in validated.participants[0].ghi_chu
    assert validated.metadata["review_required"] is True


def test_validator_flags_model_field_without_evidence():
    result = ExtractionResult(
        marker_found=True,
        text_before_marker="Vụ án hình sự thụ lý số: 12/2025/TLST-HS.",
        case_info=CaseInfo(
            so_thu_ly="12/2025/TLST-HS",
            field_metadata={
                "so_thu_ly": FieldValue(
                    value="12/2025/TLST-HS",
                    confidence=0.9,
                    source_method="local_llm",
                )
            },
        ),
    )

    validated = validate_extraction(result)

    assert any("thiếu evidence_text" in warning for warning in validated.warnings)
    assert validated.metadata["review_required"] is True
