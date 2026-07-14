from __future__ import annotations

from court_ocr_extract.extractors.pre_content_anchor_segmenter import segment_pre_content_anchors
from court_ocr_extract.extractors.rule_anchor_extractor import extract_rule_anchor_output
from tests.test_rule_anchor_metadata import _segment


def test_one_line_trial_panel_is_split_into_all_roles() -> None:
    line = (
        "Thẩm phán - Chủ tọa phiên tòa: Thẩm Phán Synthetic; "
        "Các Hội thẩm nhân dân: Hội Thẩm Synthetic A, Hội Thẩm Synthetic B; "
        "Thư ký phiên tòa: Thư Ký Synthetic; "
        "Đại diện Viện kiểm sát - Kiểm sát viên: Công Tố Synthetic"
    )
    segment = _segment(["Bản án số: 01/2025/HS-ST", line, "xét xử sơ thẩm công khai"])

    output = extract_rule_anchor_output(segment_pre_content_anchors(segment, case_id="synthetic"))

    assert output["trial_panel"]["presiding_judge"] == "Thẩm Phán Synthetic"
    assert output["trial_panel"]["jurors"] == ["Hội Thẩm Synthetic A", "Hội Thẩm Synthetic B"]
    assert output["trial_panel"]["clerk"] == "Thư Ký Synthetic"
    assert output["trial_panel"]["prosecutor"] == "Công Tố Synthetic"


def test_trial_panel_can_start_at_judge_without_composition_heading() -> None:
    segment = _segment(
        [
            "Bản án số: 01/2025/HS-ST",
            "Thẩm phán - Chủ tọa phiên tòa:",
            "Thẩm Phán Synthetic",
            "Các Hội thẩm nhân dân:",
            "Hội Thẩm Synthetic A",
            "Hội Thẩm Synthetic B",
            "thụ lý số: 01/2025/TLST-HS",
        ]
    )

    output = extract_rule_anchor_output(segment_pre_content_anchors(segment, case_id="synthetic"))

    assert output["trial_panel"]["presiding_judge"] == "Thẩm Phán Synthetic"
    assert output["trial_panel"]["jurors"] == ["Hội Thẩm Synthetic A", "Hội Thẩm Synthetic B"]
