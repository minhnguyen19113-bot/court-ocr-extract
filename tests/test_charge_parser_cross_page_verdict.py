from __future__ import annotations

from court_ocr_extract.charge_parser import parse_explicit_decision_charges
from court_ocr_extract.source_region_policy import DECISION_TAIL


def test_verdict_block_continues_across_page_break_and_skips_page_number() -> None:
    lines = [
        _line(7, 1, "Xử phạt bị cáo Person Synthetic Alpha"),
        _line(7, 2, "24 tháng tù"),
        _line(8, 1, "8"),
        _line(8, 2, "về tội"),
        _line(8, 3, '"Charge Synthetic Alpha".'),
    ]

    output = parse_explicit_decision_charges(
        lines,
        defendants=[
            {"entity_id": "defendant_alpha", "full_name": "Person Synthetic Alpha"}
        ],
    )

    evidence = output["charge_evidence"][0]
    assert output["case_charges"] == ["Charge Synthetic Alpha"]
    assert evidence["page_number"] == 7
    assert "p008_l0001" not in evidence["line_ids"]
    assert evidence["line_ids"] == [
        "p007_l0001",
        "p007_l0002",
        "p008_l0002",
        "p008_l0003",
    ]


def _line(page: int, order: int, text: str) -> dict:
    return {
        "line_id": f"p{page:03d}_l{order:04d}",
        "page_number": page,
        "reading_order": order - 1,
        "source_region": DECISION_TAIL,
        "text": text,
    }
