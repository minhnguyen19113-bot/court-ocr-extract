from __future__ import annotations

from court_ocr_extract.charge_parser import parse_explicit_decision_charges
from court_ocr_extract.source_region_policy import DECISION_TAIL


def test_verdict_spanning_eight_lines_is_parsed() -> None:
    texts = [
        "1. Xử phạt bị cáo",
        "Person Synthetic Alpha",
        "03 năm",
        "06 tháng",
        "tù",
        "về tội",
        "“Charge Synthetic Alpha”",
        "theo quy định synthetic.",
    ]
    lines = [
        {
            "line_id": f"p009_l{index:04d}",
            "page_number": 9,
            "reading_order": index - 1,
            "source_region": DECISION_TAIL,
            "text": text,
        }
        for index, text in enumerate(texts, start=1)
    ]

    output = parse_explicit_decision_charges(
        lines,
        defendants=[
            {"entity_id": "defendant_alpha", "full_name": "Person Synthetic Alpha"}
        ],
    )

    assert output["case_charges"] == ["Charge Synthetic Alpha"]
    assert output["defendant_charge_map"] == {
        "defendant_alpha": ["Charge Synthetic Alpha"]
    }
    assert output["charge_evidence"][0]["line_ids"] == [
        f"p009_l{index:04d}" for index in range(1, 9)
    ]
