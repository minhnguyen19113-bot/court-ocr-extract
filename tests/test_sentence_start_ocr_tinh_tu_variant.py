import pytest

from tests.sentence_test_support import parse_sentence


@pytest.mark.parametrize(
    "clause",
    (
        "Thời hạn tù được tỉnh từ ngày 6/1/2099.",
        "Thời hạn tù được tính tử ngày 6/1/2099.",
        "Thời hạn chấp hành hình phạt tù tính từ ngày 6/1/2099.",
    ),
)
def test_sentence_start_narrow_ocr_variants(clause: str) -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 03 năm tù về tội “Charge Synthetic”. "
        + clause
    )

    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["sentence_start_text"] == "thời hạn tù tính từ ngày 06/01/2099"
    assert "sentence_start_anchor_unparsed" not in output["warnings"]
