from __future__ import annotations

from copy import deepcopy
from typing import Any


FULL_TEXT_FIELDS = {"text_before_marker", "corrected_text"}
BULK_OCR_METADATA_FIELDS = {"ocr_pages"}


def redact_sensitive_payload(payload: Any, *, include_sensitive: bool = False) -> Any:
    """Return a copy with bulky OCR text removed unless explicitly allowed.

    Extracted structured fields are intentionally kept because JSON/Excel outputs
    are the product of the pipeline. The full OCR buffer and per-page OCR payloads
    are debug artifacts and can contain far more personal data than needed.
    """
    if include_sensitive:
        return payload

    redacted = deepcopy(payload)
    _redact_in_place(redacted)
    return redacted


def _redact_in_place(value: Any) -> None:
    if isinstance(value, list):
        for item in value:
            _redact_in_place(item)
        return

    if not isinstance(value, dict):
        return

    for key in list(value):
        if key in FULL_TEXT_FIELDS:
            value[key] = None
        elif key in BULK_OCR_METADATA_FIELDS:
            value.pop(key, None)
            value[f"{key}_redacted"] = True
        else:
            _redact_in_place(value[key])

    metadata = value.get("metadata")
    if isinstance(metadata, dict):
        metadata.setdefault("sensitive_text_redacted", True)
