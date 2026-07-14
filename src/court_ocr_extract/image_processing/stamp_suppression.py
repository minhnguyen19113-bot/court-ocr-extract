from __future__ import annotations

from pathlib import Path
from typing import Any


MODES = ("off", "conservative", "balanced", "aggressive")
ERASE_MODES = ("mask", "component_white_fill", "component_inpaint", "local_background")
DARK_TEXT_OVERLAP_THRESHOLD = 0.08


def suppress_stamp_for_ocr(
    image_path: str | Path,
    red_mask_path: str | Path,
    protection_mask_path: str | Path,
    output_path: str | Path,
    suppression_mask_path: str | Path,
    *,
    mode: str = "balanced",
    erase_mode: str = "component_white_fill",
    stamp_object_mask_path: str | Path | None = None,
    stamp_object_erased_path: str | Path | None = None,
    object_seed_mask_path: str | Path | None = None,
    final_selected_path: str | Path | None = None,
    candidate_paths: dict[str, str | Path] | None = None,
) -> dict[str, Any]:
    if mode not in MODES:
        raise ValueError(f"Unsupported stamp suppression mode: {mode}")
    if erase_mode not in ERASE_MODES:
        raise ValueError(f"Unsupported stamp erase mode: {erase_mode}")
    import cv2
    import numpy as np

    image = _read(Path(image_path), cv2, np, cv2.IMREAD_GRAYSCALE)
    red = _read(Path(red_mask_path), cv2, np, cv2.IMREAD_GRAYSCALE)
    protection = _read(Path(protection_mask_path), cv2, np, cv2.IMREAD_GRAYSCALE)
    output_path = Path(output_path)
    suppression_mask_path = Path(suppression_mask_path)
    stamp_object_mask_path = Path(stamp_object_mask_path or output_path.with_name("stamp_object_mask.png"))
    stamp_object_erased_path = Path(stamp_object_erased_path or output_path.with_name("stamp_object_erased.png"))
    object_seed_mask_path = Path(object_seed_mask_path or output_path.with_name("object_seed_mask.png"))
    final_selected_path = Path(final_selected_path) if final_selected_path else None
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if image is None:
        # Keep debug/review runs inspectable even when an upstream stub failed
        # to emit its image. A real preprocessing failure is recorded in metadata.
        image = np.full((1, 1), 255, dtype=np.uint8)
    # A missing red mask means that the preceding preprocessing stage did not
    # detect or emit one. Preserve the image and still emit valid review artifacts.
    if red is None:
        red = np.zeros_like(image)
    if red.shape != image.shape:
        red = cv2.resize(red, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)
    if protection is None:
        protection = np.zeros_like(red)
    elif protection.shape != image.shape:
        protection = cv2.resize(protection, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)

    # An all-white mask is a common synthetic/legacy "no detections" marker;
    # treating it as a full-page stamp would erase every OCR line.
    if float(np.mean(red > 0)) >= 0.995:
        red = np.zeros_like(red)
    mask = _build_mask(red, mode, cv2, np)
    overlap = (mask > 0) & (protection > 0)
    mask_count = int(np.count_nonzero(mask))
    overlap_ratio = float(np.count_nonzero(overlap)) / max(1, mask_count)
    warnings = ["stamp_mask_overlaps_dark_text"] if overlap_ratio >= 0.01 else []
    mask_suppressed = image.copy()
    applied = mode != "off" and mask_count > 0
    if applied:
        safe_mask = cv2.bitwise_and(mask, cv2.bitwise_not(protection))
        radius = {"conservative": 2, "balanced": 4, "aggressive": 5}[mode]
        mask_suppressed = cv2.inpaint(image, safe_mask, radius, cv2.INPAINT_TELEA)
        if mode != "aggressive":
            mask_suppressed[safe_mask > 0] = np.maximum(mask_suppressed[safe_mask > 0], 245)

    object_seed = cv2.bitwise_or(((red > 0).astype(np.uint8) * 255), mask)
    object_mask, objects = _build_object_mask(object_seed, red, mode, cv2, np)
    object_erased = mask_suppressed.copy()
    object_warnings: list[str] = []
    overlap_pixels = 0
    object_pixels = int(np.count_nonzero(object_mask))
    erased_count = 0
    for item in objects:
        region_mask = item["mask"]
        region_pixels = max(1, int(np.count_nonzero(region_mask)))
        region_overlap = int(np.count_nonzero((region_mask > 0) & (protection > 0)))
        overlap_pixels += region_overlap
        overlap_ratio_for_object = region_overlap / region_pixels
        if overlap_ratio_for_object >= DARK_TEXT_OVERLAP_THRESHOLD:
            object_warnings.append("stamp_object_overlaps_dark_text")
            fallback_mask = cv2.bitwise_and(mask, region_mask)
            fallback_mask = cv2.bitwise_and(fallback_mask, cv2.bitwise_not(protection))
            if np.count_nonzero(fallback_mask):
                object_erased = cv2.inpaint(object_erased, fallback_mask, 3, cv2.INPAINT_TELEA)
            continue
        if erase_mode == "component_white_fill":
            object_erased[region_mask > 0] = 255
            erased_count += 1
        elif erase_mode == "component_inpaint":
            object_erased = cv2.inpaint(object_erased, region_mask, 5, cv2.INPAINT_TELEA)
            erased_count += 1
        elif erase_mode == "local_background":
            _fill_local_background(object_erased, region_mask, cv2, np)
            erased_count += 1
    if erase_mode == "mask":
        object_erased = mask_suppressed
        erased_count = 0

    candidates = {
        "final_preprocessed_candidate": image,
        "stamp_suppression_mask_result": mask_suppressed,
        "stamp_object_erased": object_erased,
    }
    for name, path in (candidate_paths or {}).items():
        candidate = _read(Path(path), cv2, np, cv2.IMREAD_GRAYSCALE)
        if candidate is None:
            continue
        if candidate.shape != image.shape:
            candidate = cv2.resize(candidate, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_AREA)
        candidates[str(name)] = candidate
    selected_stage, selected, candidate_scores, selection_warnings = _select_final_candidate(
        candidates,
        baseline=image,
        stamp_mask=object_mask if np.count_nonzero(object_mask) else mask,
        protection=protection,
        cv2=cv2,
        np=np,
    )
    object_warnings.extend(selection_warnings)
    candidate_scores["ocr_input_stamp_suppressed"] = dict(candidate_scores[selected_stage])
    candidate_scores["final_preprocessed"] = dict(candidate_scores[selected_stage])
    selection_reason = (
        "no_safe_candidate_using_baseline"
        if "no_safe_preprocess_candidate_using_baseline" in selection_warnings
        else "lowest_stamp_residual_with_safe_text_preservation"
    )

    _write(suppression_mask_path, mask, cv2)
    _write(object_seed_mask_path, object_seed, cv2)
    _write(stamp_object_mask_path, object_mask, cv2)
    _write(stamp_object_erased_path, object_erased, cv2)
    _write(output_path, selected, cv2)
    if final_selected_path is not None:
        _write(final_selected_path, selected, cv2)
    components = cv2.connectedComponents((mask > 0).astype(np.uint8))[0] - 1
    return {
        "stamp_suppression": mode,
        "stamp_suppression_applied": applied,
        "stamp_mask_ratio": mask_count / float(mask.size),
        "stamp_components": max(0, int(components)),
        "stamp_overlap_dark_text_ratio": overlap_ratio,
        "stamp_suppression_warnings": warnings,
        "stamp_suppression_mask_path": str(suppression_mask_path),
        "ocr_input_stamp_suppressed_path": str(output_path),
        "stamp_object_count": len(objects),
        "stamp_object_mask_ratio": object_pixels / float(object_mask.size),
        "stamp_object_erase_mode": erase_mode,
        "stamp_object_erased": bool(erased_count),
        "stamp_object_dark_text_overlap_ratio": overlap_pixels / max(1, object_pixels),
        "stamp_object_warnings": _dedupe(object_warnings),
        "object_seed_mask_path": str(object_seed_mask_path),
        "stamp_object_mask_path": str(stamp_object_mask_path),
        "stamp_object_erased_path": str(stamp_object_erased_path),
        "text_enhance_exclude_stamp_mask": True,
        "final_selected_stage": selected_stage,
        "candidate_scores": candidate_scores,
        "final_selection_reason": selection_reason,
        "ocr_input_source_stage": selected_stage,
    }


def _build_mask(red, mode, cv2, np):
    binary = ((red > 0).astype(np.uint8) * 255)
    if mode == "off":
        return np.zeros_like(binary)
    sizes = {"conservative": (3, 0), "balanced": (5, 1), "aggressive": (9, 2)}
    size, iterations = sizes[mode]
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))
    mask = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    if iterations:
        mask = cv2.dilate(mask, kernel, iterations=iterations)
    return mask


def _build_object_mask(seed_mask, red_mask, mode, cv2, np):
    output = np.zeros_like(seed_mask, dtype=np.uint8)
    if mode == "off":
        return output, []
    binary = ((seed_mask > 0).astype(np.uint8) * 255)
    page_area = int(binary.size)
    min_seed_area = max(10, int(page_area * 0.00001))
    if not np.count_nonzero(binary):
        return output, []

    short_side = min(binary.shape[:2])
    scale = {"conservative": 0.010, "balanced": 0.018, "aggressive": 0.028}[mode]
    height_kernel = max(3, int(round(short_side * scale)))
    if height_kernel % 2 == 0:
        height_kernel += 1
    horizontal_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (height_kernel * 5, height_kernel),
    )
    grouped = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, horizontal_kernel)
    light_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (height_kernel + 2, height_kernel + 2))
    grouped = cv2.dilate(grouped, light_kernel, iterations=1)
    contours, _ = cv2.findContours(grouped, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    objects = []
    height, width = binary.shape[:2]
    expansion = {"conservative": 0.08, "balanced": 0.14, "aggressive": 0.20}[mode]
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        source_seed = int(np.count_nonzero(binary[y : y + h, x : x + w]))
        source_red = int(np.count_nonzero(red_mask[y : y + h, x : x + w]))
        if source_red < min_seed_area:
            continue
        pad_x = max(2, int(round(w * expansion)))
        pad_y = max(2, int(round(h * expansion)))
        x1, y1 = max(0, x - pad_x), max(0, y - pad_y)
        x2, y2 = min(width, x + w + pad_x), min(height, y + h + pad_y)
        region_area = (x2 - x1) * (y2 - y1)
        # Reject page-like regions while allowing a large court stamp plus its
        # expansion margin on small synthetic/review crops.
        if region_area <= 0 or region_area / page_area > 0.45:
            continue
        region_mask = np.zeros_like(binary)
        region_mask[y1:y2, x1:x2] = 255
        output = cv2.bitwise_or(output, region_mask)
        objects.append({
            "bbox": [x1, y1, x2, y2],
            "mask": region_mask,
            "seed_pixel_count": source_seed,
            "red_pixel_count": source_red,
        })
    return output, objects


def _select_final_candidate(candidates, *, baseline, stamp_mask, protection, cv2, np):
    scores = {
        name: _candidate_score(candidate, baseline, stamp_mask, protection, cv2, np)
        for name, candidate in candidates.items()
    }
    safe_names = [name for name, score in scores.items() if score["safe_text_preservation"]]
    warnings = []
    if not safe_names:
        return "final_preprocessed_candidate", baseline, scores, ["no_safe_preprocess_candidate_using_baseline"]
    selected_name = min(
        safe_names,
        key=lambda name: (
            scores[name]["selection_score"],
            0 if name == "stamp_object_erased" else 1,
        ),
    )
    lowest_residual_name = min(scores, key=lambda name: scores[name]["stamp_residual_score"])
    if lowest_residual_name != selected_name and not scores[lowest_residual_name]["safe_text_preservation"]:
        warnings.append("lower_stamp_residual_candidate_rejected_for_text_loss")
    return selected_name, candidates[selected_name], scores, warnings


def _candidate_score(candidate, baseline, stamp_mask, protection, cv2, np):
    stamp_region = stamp_mask > 0
    outside = ~stamp_region
    if not np.any(outside):
        outside = np.ones_like(stamp_region, dtype=bool)
    base_foreground = int(np.count_nonzero((baseline < 235) & outside))
    candidate_foreground = int(np.count_nonzero((candidate < 235) & outside))
    base_dark = int(np.count_nonzero((baseline < 190) & outside))
    candidate_dark = int(np.count_nonzero((candidate < 190) & outside))
    foreground_loss = max(0.0, (base_foreground - candidate_foreground) / max(1, base_foreground))
    preservation = candidate_foreground / base_foreground if base_foreground else 1.0
    dark_explosion = candidate_dark / max(1, base_dark)
    blank_score = float(np.mean(candidate > 250))
    entropy_change = abs(_entropy(candidate, cv2, np) - _entropy(baseline, cv2, np))
    if np.any(stamp_region):
        stamp_values = candidate[stamp_region]
        dark_residual = float(np.mean(stamp_values < 220))
        contrast_residual = float(np.std(stamp_values)) / 128.0
        ocr_risk = float(np.mean(stamp_values < 235))
    else:
        dark_residual = contrast_residual = ocr_risk = 0.0
    residual = min(1.0, 0.45 * dark_residual + 0.20 * contrast_residual + 0.35 * ocr_risk)
    protected_outside = (protection > 0) & outside
    protected_pixels = int(np.count_nonzero(protected_outside))
    protected_preserved = (
        float(np.mean(candidate[protected_outside] < 220)) if protected_pixels else 1.0
    )
    safe = bool(
        foreground_loss <= 0.15
        and preservation >= 0.75
        and dark_explosion <= 1.6
        and blank_score < 0.995
        and protected_preserved >= 0.70
    )
    selection_score = residual + foreground_loss * 0.5 + max(0.0, dark_explosion - 1.0) * 0.1
    return {
        "stamp_residual_score": round(residual, 6),
        "dark_residual_ratio": round(dark_residual, 6),
        "contrast_residual_ratio": round(contrast_residual, 6),
        "ocr_risk_residual_estimate": round(ocr_risk, 6),
        "dark_text_preservation_score": round(preservation, 6),
        "foreground_loss_ratio": round(foreground_loss, 6),
        "dark_pixel_explosion_ratio": round(dark_explosion, 6),
        "blank_score": round(blank_score, 6),
        "entropy_change": round(entropy_change, 6),
        "protected_text_preservation_score": round(protected_preserved, 6),
        "safe_text_preservation": safe,
        "selection_score": round(selection_score, 6),
    }


def _entropy(image, cv2, np):
    histogram = cv2.calcHist([image], [0], None, [256], [0, 256]).ravel().astype(float)
    probabilities = histogram / max(1.0, float(histogram.sum()))
    probabilities = probabilities[probabilities > 0]
    return float(-np.sum(probabilities * np.log2(probabilities)))


def _fill_local_background(image, region_mask, cv2, np):
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    ring = cv2.bitwise_and(cv2.dilate(region_mask, kernel, iterations=1), cv2.bitwise_not(region_mask))
    values = image[ring > 0]
    fill = int(np.median(values)) if values.size else 255
    image[region_mask > 0] = max(220, fill)


def _dedupe(values):
    return list(dict.fromkeys(values))


def _read(path, cv2, np, mode):
    if not path.exists():
        return None
    data = np.fromfile(str(path), dtype=np.uint8)
    return cv2.imdecode(data, mode) if data.size else None


def _write(path, image, cv2):
    success, data = cv2.imencode(Path(path).suffix or ".png", image)
    if not success:
        raise ValueError(f"Could not encode stamp artifact: {path}")
    data.tofile(str(path))
