from __future__ import annotations

from court_ocr_extract.sentence_parser import parse_defendant_sentences
from court_ocr_extract.source_region_policy import DECISION_TAIL


DEFENDANTS = [
    {"entity_id": "defendant_alpha", "full_name": "Person Synthetic Alpha"},
    {"entity_id": "defendant_beta", "full_name": "Person Synthetic Beta"},
]


def parse_sentence(text, defendants=None):
    return parse_defendant_sentences(
        text,
        defendants=DEFENDANTS[:1] if defendants is None else defendants,
    )


def line(page: int, order: int, text: str, *, region: str = DECISION_TAIL) -> dict:
    return {
        "line_id": f"p{page:03d}_l{order:04d}",
        "page_number": page,
        "reading_order": order - 1,
        "source_region": region,
        "text": text,
    }
