from __future__ import annotations

import cv2
import numpy as np

from court_ocr_extract.ocr_backends.stamp_filter import filter_lines_by_stamp_mask


def test_balanced_filter_excludes_stamp_line_and_keeps_body_line(tmp_path) -> None:
    mask = np.zeros((100, 160), dtype=np.uint8)
    mask[10:40, 10:70] = 255
    path = tmp_path / "stamp_mask.png"
    assert cv2.imwrite(str(path), mask)
    lines = [
        {"line_id": "p001_l0001", "text": "stamp", "bbox": [10, 10, 70, 40]},
        {"line_id": "p001_l0002", "text": "body", "bbox": [80, 60, 140, 80]},
    ]

    kept, excluded = filter_lines_by_stamp_mask(lines, path, None, mode="balanced")

    assert [line["text"] for line in kept] == ["body"]
    assert excluded[0]["reason"] == "stamp_mask_overlap"
    assert excluded[0]["stamp_overlap_ratio"] > 0.9


def test_protected_text_is_kept_and_filter_has_no_silent_fallback(tmp_path) -> None:
    stamp = np.zeros((100, 160), dtype=np.uint8)
    protection = np.zeros_like(stamp)
    stamp[10:40, 10:70] = 255
    protection[10:40, 10:70] = 255
    stamp_path = tmp_path / "stamp.png"
    protection_path = tmp_path / "protection.png"
    assert cv2.imwrite(str(stamp_path), stamp)
    assert cv2.imwrite(str(protection_path), protection)

    kept, excluded = filter_lines_by_stamp_mask(
        [{"line_id": "p001_l0001", "text": "protected", "bbox": [10, 10, 70, 40]}],
        stamp_path, protection_path, mode="conservative"
    )

    assert [line["text"] for line in kept] == ["protected"]
    assert excluded == []
