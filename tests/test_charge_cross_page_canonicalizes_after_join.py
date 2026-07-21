from __future__ import annotations

from court_ocr_extract.charge_parser import parse_explicit_decision_charges


def test_cross_page_charge_is_canonicalized_only_after_join() -> None:
    output = parse_explicit_decision_charges(
        "\n".join(
            [
                "Xử phạt bị cáo Person Synthetic Alpha về tội “Trộm cấp",
                "tài sản”.",
            ]
        ),
        defendants=[
            {"entity_id": "defendant_alpha", "full_name": "Person Synthetic Alpha"}
        ],
    )

    evidence = output["charge_evidence"][0]
    assert evidence["normalized_charge"] == "Trộm cấp tài sản"
    assert evidence["canonical_charge"] == "Trộm cắp tài sản"
    assert evidence["normalization_method"] == "folded_exact"
    assert output["case_charges"] == ["Trộm cắp tài sản"]
