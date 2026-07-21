import pytest

from tests.sentence_test_support import parse_sentence


@pytest.mark.parametrize(
    "anchor",
    ["trừ ngày tạm giữ", "trừ thời gian tạm giữ", "được trừ thời gian tạm giữ"],
)
def test_sentence_detention_credit_date_range(anchor: str) -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 02 năm 06 tháng tù về tội “Charge Synthetic”. "
        f"{anchor}, tạm giam từ ngày 12/2/2099 đến ngày 6/6/2099."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["detention_credit_text"] == (
        "được trừ thời gian tạm giữ, tạm giam từ 12/02/2099 đến 06/06/2099"
    )

