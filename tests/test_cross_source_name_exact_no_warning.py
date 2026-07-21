from tests.sentence_test_support import parse_sentence


def test_cross_source_name_exact_no_warning() -> None:
    output = parse_sentence("Xử phạt bị cáo Person Synthetic Alpha 09 tháng tù về tội “Charge Synthetic”.")
    assert "cross_source_person_name_disagreement" not in output["warnings"]

