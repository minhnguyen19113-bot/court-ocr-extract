from __future__ import annotations

from court_ocr_extract.final_excel_builder import build_final_excel_rows
from court_ocr_extract.final_excel_role_policy import (
    PRIMARY_FINAL_ROLES,
    classify_final_role,
)


def test_final_excel_contains_only_primary_roles_and_exact_aliases() -> None:
    result = {
        "case_id": "synthetic_case",
        "document_type": "judgment_criminal_first_instance",
        "metadata": {"case_acceptance_number": "908/2099/TLST-HS"},
        "trial_panel": {"presiding_judge": "Chủ Tọa Synthetic"},
        "defendants": [
            {"full_name": "Người Synthetic A", "birth_date_or_year": "1990"},
            {"full_name": "Người Synthetic B", "birth_date_or_year": "1991"},
        ],
        "participants": [
            {"role": "Bị hại", "full_name": "Người Synthetic C"},
            {
                "role": "Người có quyền và nghĩa vụ liên quan",
                "full_name": "Người Synthetic D",
            },
            {"role": "Người giám hộ", "full_name": "Người Synthetic E"},
            {"role": "Người bào chữa", "full_name": "Người Synthetic F"},
            {"role": "Hội thẩm nhân dân", "full_name": "Người Synthetic G"},
        ],
    }

    rows = build_final_excel_rows(result)

    assert [row["TƯ CÁCH TỐ TỤNG"] for row in rows] == [
        "Bị cáo",
        "Bị cáo",
        "Bị hại",
    ]
    assert PRIMARY_FINAL_ROLES == {"Bị cáo", "Bị hại"}
    assert all(row["TƯ CÁCH TỐ TỤNG"] in PRIMARY_FINAL_ROLES for row in rows)
    assert all("Hội thẩm" not in row["TƯ CÁCH TỐ TỤNG"] for row in rows)
    related = classify_final_role("Người có quyền và nghĩa vụ liên quan")
    assert related.include_in_final is False
    assert related.include_in_other is True


def test_related_role_is_not_inferred_from_arbitrary_phrase() -> None:
    decision = classify_final_role("Người liên quan đến mô tả synthetic")

    assert decision.include_in_final is False
    assert decision.normalized_role != "Người có quyền lợi, nghĩa vụ liên quan"
