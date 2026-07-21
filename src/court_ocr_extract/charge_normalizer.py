from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass

from court_ocr_extract.extractors.pre_content_anchor_segmenter import fold_text


CANONICAL_CHARGE_LABELS = (
    "Cố ý gây thương tích",
    "Gây rối trật tự công cộng",
    "Tổ chức sử dụng trái phép chất ma túy",
    "Trộm cắp tài sản",
    "Cho vay lãi nặng trong giao dịch dân sự",
)


@dataclass(frozen=True)
class ChargeNormalization:
    raw_charge: str
    normalized_charge: str
    canonical_charge: str
    normalization_method: str

    @property
    def warning(self) -> str:
        if self.normalization_method == "ambiguous":
            return "ambiguous_charge_canonicalization"
        if self.normalization_method == "folded_exact":
            return "charge_canonicalized_from_ocr"
        return ""


def normalize_charge(value: object) -> str:
    charge = unicodedata.normalize("NFC", str(value or ""))
    charge = re.sub(r"\s+", " ", charge).strip()
    return charge.strip(" “”“\"‘’'.,;:-")


def canonicalize_charge(
    raw_charge: object,
    *,
    canonical_labels: Iterable[str] = CANONICAL_CHARGE_LABELS,
) -> ChargeNormalization:
    raw = str(raw_charge or "")
    normalized = normalize_charge(raw)
    folded = fold_text(normalized)
    candidates = tuple(
        dict.fromkeys(
            label
            for label in canonical_labels
            if folded and fold_text(label) == folded
        )
    )
    if len(candidates) == 1:
        canonical = candidates[0]
        method = "already_canonical" if canonical == normalized else "folded_exact"
        return ChargeNormalization(raw, normalized, canonical, method)
    if len(candidates) > 1:
        return ChargeNormalization(raw, normalized, normalized, "ambiguous")
    return ChargeNormalization(raw, normalized, normalized, "unmapped")
