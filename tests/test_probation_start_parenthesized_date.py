import pytest

from tests.sentence_test_support import parse_sentence


@pytest.mark.parametrize(
    "date_text",
    ["(09/7/2099)", "(09/07/2099)", "ngày 09/7/2099", "09 tháng 7 năm 2099"],
)
def test_probation_start_parenthesized_date(date_text: str) -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 09 tháng tù về tội “Charge Synthetic”, "
        "cho hưởng án treo. Thời gian thử thách 18 tháng, "
        f"tính từ ngày tuyên án sơ thẩm {date_text}."
    )
    assert output["defendant_sentence_map"]["defendant_alpha"]["probation_start_text"] == (
        "tính từ ngày tuyên án sơ thẩm 09/07/2099"
    )

