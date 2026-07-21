from __future__ import annotations

from court_ocr_extract.charge_parser import parse_explicit_decision_charges
from court_ocr_extract.source_region_policy import DECISION_TAIL


def test_charge_canonicalizer_preserves_raw_charge_in_evidence() -> None:
    output = parse_explicit_decision_charges(
        [
            {
                "line_id": "p009_l0001",
                "source_region": DECISION_TAIL,
                "text": "Xử phạt bị cáo Người Synthetic A về tội \"Cổ ý gây thương tích\"",
            }
        ],
        defendants=[{"entity_id": "defendant_001", "full_name": "Người Synthetic A"}],
    )

    evidence = output["charge_evidence"][0]
    assert evidence["raw_charge"] == "Cổ ý gây thương tích"
    assert evidence["normalized_charge"] == "Cổ ý gây thương tích"
    assert evidence["canonical_charge"] == "Cố ý gây thương tích"
    assert evidence["charge"] == "Cố ý gây thương tích"
    assert evidence["normalization_method"] == "folded_exact"
    assert "charge_canonicalized_from_ocr" in output["warnings"]
