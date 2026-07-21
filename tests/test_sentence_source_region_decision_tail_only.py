from court_ocr_extract.source_region_policy import FRONT_PRE_CONTENT
from tests.sentence_test_support import line, parse_sentence


def test_sentence_source_region_decision_tail_only() -> None:
    output = parse_sentence(
        [
            line(
                1,
                1,
                "Xử phạt bị cáo Person Synthetic Alpha 03 năm tù về tội “Charge Synthetic”.",
                region=FRONT_PRE_CONTENT,
            )
        ]
    )
    assert output["defendant_sentence_map"] == {}
    assert "sentence_lines_ignored_from_source_region:front_pre_content" in output["warnings"]
