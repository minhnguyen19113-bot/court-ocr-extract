import pytest

from tests.sentence_test_support import parse_sentence


@pytest.mark.parametrize("variant", ["bắt giam", "bất giam", "bắt giảm"])
def test_sentence_start_ocr_bat_giam_variant(variant: str) -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 02 năm tù về tội “Charge Synthetic”. "
        f"Thời hạn tù tính từ ngày {variant} bị cáo để thi hành án."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["sentence_start_text"] == (
        "thời hạn tù tính từ ngày bắt giam bị cáo để thi hành án"
    )

