from __future__ import annotations

from court_ocr_extract.charge_parser import parse_explicit_decision_charges


def test_ve_toi_wins_over_later_pham_toi_procedural_clause() -> None:
    lines = [
        _line(1, "4.1. Xử phạt bị cáo Person Synthetic Alpha 18 tháng tù"),
        _line(2, "về tội “Charge Synthetic Alpha”, nhưng cho hưởng án treo."),
        _line(3, "Trong thời gian thử thách, nếu người này thực hiện"),
        _line(4, "hành vi phạm tội mới thì Tòa án buộc người đó phải"),
        _line(5, "chấp hành hình phạt của bản án trước."),
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
    evidence = output["charge_evidence"][0]
    assert evidence["raw_charge"] == "Charge Synthetic Alpha"
    assert evidence["normalized_charge"] == "Charge Synthetic Alpha"
    assert "phạm tội mới" not in evidence["raw_text"]


def _line(order: int, text: str) -> dict:
    return {
        "line_id": f"p007_l{order:04d}",
        "page_number": 7,
        "reading_order": order - 1,
        "text": text,
    }
