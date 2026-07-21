from tests.sentence_test_support import parse_sentence


def test_sentence_fine_excludes_civil_payment() -> None:
    output = parse_sentence(
        "Tuyên bố bị cáo Person Synthetic Alpha phạm tội “Charge Synthetic”; "
        "buộc bồi thường số tiền 50.000.000 đồng."
    )
    assert output["defendant_sentence_map"] == {}
