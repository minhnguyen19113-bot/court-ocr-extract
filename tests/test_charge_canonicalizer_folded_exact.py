from __future__ import annotations

from court_ocr_extract.charge_normalizer import canonicalize_charge


def test_charge_canonicalizer_uses_folded_exact_lexicon_match() -> None:
    assert canonicalize_charge("Cổ ý gây thương tích").canonical_charge == "Cố ý gây thương tích"
    assert canonicalize_charge("Trộm cấp tài sản").canonical_charge == "Trộm cắp tài sản"
