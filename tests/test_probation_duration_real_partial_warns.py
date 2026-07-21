import pytest

from tests.sentence_test_support import parse_sentence


@pytest.mark.parametrize("duration", ["04 năm, 06...", "03 năm và..."])
def test_probation_duration_real_partial_warns(duration: str) -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 02 năm tù về tội “Charge Synthetic”, "
        f"cho hưởng án treo. Thời gian thử thách {duration}"
    )
    assert "probation_duration_partial" in output["warnings"]

