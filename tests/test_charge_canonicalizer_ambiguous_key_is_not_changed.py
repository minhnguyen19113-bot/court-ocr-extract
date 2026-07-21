from __future__ import annotations

from court_ocr_extract.charge_normalizer import canonicalize_charge


def test_ambiguous_folded_key_is_not_changed() -> None:
    result = canonicalize_charge(
        "Charge Sýnthetic",
        canonical_labels=("Charge Synthetic", "Charge Sýnthetic"),
    )

    assert result.canonical_charge == "Charge Sýnthetic"
    assert result.normalization_method == "ambiguous"
    assert result.warning == "ambiguous_charge_canonicalization"
