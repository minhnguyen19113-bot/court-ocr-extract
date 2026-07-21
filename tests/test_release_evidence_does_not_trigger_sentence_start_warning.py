from tests.sentence_test_support import line, parse_sentence


def test_release_evidence_does_not_trigger_sentence_start_warning() -> None:
    output = parse_sentence([
        line(7, 1, "Xử phạt bị cáo Person Synthetic Alpha 03 năm tù về tội “Charge Synthetic”."),
        line(7, 2, "Trả tự do cho bị cáo Person Synthetic Alpha tại phiên tòa."),
    ])

    assert "sentence_start_anchor_unparsed" not in output["warnings"]
    assert output["defendant_sentence_map"]["defendant_alpha"]["release_text"]
