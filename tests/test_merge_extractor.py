from court_ocr_extract.extraction.merge import merge_extractor_outputs
from court_ocr_extract.models import ExtractorOutput, FieldValue


def test_merge_conflict_chooses_higher_confidence_without_leaking_values():
    primary = ExtractorOutput(
        method="local_llm",
        case_fields={
            "so_thu_ly": FieldValue(
                value="synthetic-low",
                confidence=0.4,
                source_method="local_llm",
            )
        },
    )
    support = ExtractorOutput(
        method="heuristic_support",
        case_fields={
            "so_thu_ly": FieldValue(
                value="synthetic-high",
                confidence=0.9,
                source_method="heuristic_support",
            )
        },
    )

    result = merge_extractor_outputs(
        source_file="synthetic.pdf",
        text_before_marker="Synthetic text",
        marker_found=True,
        marker_text="NỘI DUNG VỤ ÁN",
        marker_page=2,
        primary=primary,
        support=support,
    )

    assert result.case_info.so_thu_ly == "synthetic-high"
    assert any("Conflict" in warning and "so_thu_ly" in warning for warning in result.warnings)
    assert all("synthetic-low" not in warning for warning in result.warnings)
    assert all("synthetic-high" not in warning for warning in result.warnings)
