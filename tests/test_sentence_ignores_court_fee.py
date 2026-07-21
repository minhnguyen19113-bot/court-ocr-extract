from tests.sentence_test_support import parse_sentence


def test_sentence_ignores_court_fee() -> None:
    output = parse_sentence(
        "Tuyên bố bị cáo Person Synthetic Alpha phạm tội “Charge Synthetic”; "
        "bị cáo phải chịu án phí 200.000 đồng."
    )
    assert output["defendant_sentence_map"] == {}
