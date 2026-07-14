from __future__ import annotations

import pytest

from court_ocr_extract.extractors.pre_content_anchor_segmenter import segment_pre_content_anchors
from court_ocr_extract.extractors.rule_anchor_extractor import extract_rule_anchor_output


@pytest.mark.parametrize(
    ("judgment_line", "next_line", "number", "date"),
    [
        ("Bản án số: 01/2025/HS-ST Ngày: 15/7/2025", None, "01/2025/HS-ST", "15/7/2025"),
        ("Bản án số: 08/2025/HSST.", "Ngày : 14 - 7 - 2025", "08/2025/HSST", "14-7-2025"),
        ("Bản ản số: 02/2025/HS-ST", "Ngày: 02 - 7-2025", "02/2025/HS-ST", "02-7-2025"),
    ],
)
def test_metadata_judgment_number_and_date_anchor_variants(
    judgment_line, next_line, number, date
) -> None:
    texts = ["TÒA ÁN NHÂN DÂN THÀNH PHÔ SYNTHETIC", judgment_line]
    if next_line:
        texts.append(next_line)
    texts.extend(["Đối với bị cáo:", "Người Synthetic A, sinh ngày 01/01/1990"])

    output = _extract(texts)

    assert output["metadata"]["court_name"] == "TÒA ÁN NHÂN DÂN THÀNH PHỐ SYNTHETIC"
    assert output["metadata"]["judgment_number"] == number
    assert output["metadata"]["judgment_date"] == date


def test_metadata_does_not_use_birth_or_decision_date_as_judgment_date() -> None:
    output = _extract(
        [
            "Bản án số: 03/2025/HS-ST",
            "Quyết định đưa vụ án ra xét xử số: 04/2025/QĐXX ngày 03/6/2025",
            "thụ lý số: 05/2025/TLST-HS",
            "Đối với bị cáo:",
            "Người Synthetic B, sinh ngày 09/7/1990",
        ]
    )

    assert output["metadata"]["judgment_date"] is None
    assert output["metadata"]["trial_decision_number"] == "04/2025/QĐXX"
    assert output["metadata"]["case_acceptance_number"] == "05/2025/TLST-HS"


def _extract(texts: list[str]) -> dict:
    segment = _segment(texts)
    return extract_rule_anchor_output(segment_pre_content_anchors(segment, case_id="synthetic"))


def _segment(texts: list[str], document_type: str = "judgment_criminal_first_instance") -> dict:
    return {
        "document_type": document_type,
        "pre_content_lines": [
            {"line_id": f"p001_l{index:04d}", "page_number": 1, "text": text}
            for index, text in enumerate(texts, start=1)
        ],
        "warnings": [],
    }
