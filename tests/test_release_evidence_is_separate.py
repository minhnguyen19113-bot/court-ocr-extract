from tests.sentence_test_support import line, parse_sentence


def test_release_evidence_is_separate() -> None:
    output = parse_sentence([
        line(8, 1, "Xử phạt bị cáo Person Synthetic Alpha 09 tháng tù về tội “Charge Synthetic”."),
        line(8, 2, "1.2. Tuyên bố trả tự do cho bị cáo Person Synthetic Alpha tại phiên tòa."),
        line(8, 3, "Nếu không bị tạm giam về tội phạm khác."),
    ])
    release = next(item for item in output["sentence_evidence"] if item["evidence_type"] == "release")
    assert release["line_ids"] == ["p008_l0002"]
    assert "Nếu không" not in release["raw_text"]

