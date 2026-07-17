from __future__ import annotations

from court_ocr_extract.source_region_policy import (
    ALLOWED_PRODUCTION_SOURCE_REGIONS,
    DECISION_TAIL,
    FRONT_PRE_CONTENT,
    MIDDLE_EXCLUDED,
    MIDDLE_EXCLUDED_HEADINGS,
    audit_source_region,
    is_source_region_allowed,
)


def test_production_allows_only_front_and_decision_tail() -> None:
    assert ALLOWED_PRODUCTION_SOURCE_REGIONS == {
        FRONT_PRE_CONTENT,
        DECISION_TAIL,
    }
    assert MIDDLE_EXCLUDED not in ALLOWED_PRODUCTION_SOURCE_REGIONS
    assert MIDDLE_EXCLUDED_HEADINGS == {
        "NỘI DUNG VỤ ÁN",
        "NHẬN ĐỊNH CỦA TÒA ÁN",
    }


def test_field_source_contract_rejects_wrong_or_middle_region() -> None:
    assert is_source_region_allowed("SỐ THỤ LÝ", FRONT_PRE_CONTENT)
    assert is_source_region_allowed("QUAN HỆ PHÁP LUẬT", DECISION_TAIL)
    assert not is_source_region_allowed("QUAN HỆ PHÁP LUẬT", FRONT_PRE_CONTENT)

    audit = audit_source_region(
        "HỌ TÊN ĐƯƠNG SỰ",
        MIDDLE_EXCLUDED,
        evidence_line_ids=["p004_l0001"],
    )
    assert audit["allowed"] is False
    assert audit["warning"] == "middle_source_region_is_excluded"

