from __future__ import annotations

from typing import Any


def evidence_status(participant: dict[str, Any], field: str) -> str:
    evidence = participant.get("evidence") or {}
    confidence = participant.get("confidence") or {}
    if not participant.get(field):
        return "Không có dữ liệu - cần review"
    if not evidence.get(field):
        return "Không có evidence rõ ràng - cần review"
    if float(confidence.get(field) or 0.0) < 0.5:
        return "Confidence thấp - cần review"
    return "Có evidence"
