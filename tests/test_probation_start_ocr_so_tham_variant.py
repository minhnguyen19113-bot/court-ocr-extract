import pytest

from tests.sentence_test_support import parse_sentence


@pytest.mark.parametrize("variant", ["sơ thảm", "sơ thẳm"])
def test_probation_start_ocr_so_tham_variant(variant: str) -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 09 tháng tù về tội “Charge Synthetic”, "
        "cho hưởng án treo. Thời gian thử thách là 18 tháng, "
        f"tính từ ngày tuyên án {variant} (09/7/2099)."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["probation_start_text"] == "tính từ ngày tuyên án sơ thẩm 09/07/2099"
    assert variant in "\n".join(item["raw_text"] for item in output["sentence_evidence"])

