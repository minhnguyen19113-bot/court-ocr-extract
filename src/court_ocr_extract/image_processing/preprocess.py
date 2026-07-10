from __future__ import annotations

import math
import shutil
from pathlib import Path
from typing import Any

from PIL import Image, ImageFilter, ImageOps, ImageStat

from court_ocr_extract.image_processing.red_stamp_removal import reduce_red_stamp_with_metadata


DESKEW_MODES = ("off", "safe", "force")
PREPROCESS_PROFILES = ("conservative", "balanced", "aggressive")
TEXT_ENHANCE_MODES = ("off", "light", "medium", "strong")


def preprocess_for_ocr(
    rendered_image_path: str | Path,
    output_path: str | Path,
    *,
    remove_red_stamp: bool = False,
    intermediate_path: str | Path | None = None,
    red_stamp_mode: str = "neutralize",
    red_mask_path: str | Path | None = None,
    black_text_protection_path: str | Path | None = None,
    text_enhanced_path: str | Path | None = None,
    text_enhance_mode: str = "light",
    deskew_mode: str = "off",
    preprocess_profile: str = "conservative",
    metadata: dict[str, Any] | None = None,
) -> Path:
    """Create an OCR helper image while preserving a safe fallback at every stage."""
    if deskew_mode not in DESKEW_MODES:
        raise ValueError(f"Unsupported deskew mode: {deskew_mode}")
    if preprocess_profile not in PREPROCESS_PROFILES:
        raise ValueError(f"Unsupported preprocess profile: {preprocess_profile}")
    if text_enhance_mode not in TEXT_ENHANCE_MODES:
        raise ValueError(f"Unsupported text enhancement mode: {text_enhance_mode}")

    rendered_image_path = Path(rendered_image_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []
    result_metadata: dict[str, Any] = {
        "deskew_mode": deskew_mode,
        "preprocess_profile": preprocess_profile,
        "detected_angle": None,
        "deskew_applied": False,
        "deskew_confidence": 0.0,
        "deskew_reason": "deskew_disabled" if deskew_mode == "off" else "not_evaluated",
        "red_pixels_count": 0,
        "red_pixels_ratio": 0.0,
        "red_seal_removed": False,
        "red_mask_path": str(red_mask_path) if red_mask_path else None,
        "red_removal_mode": red_stamp_mode,
        "black_text_protection_path": (
            str(black_text_protection_path) if black_text_protection_path else None
        ),
        "text_enhance_mode": text_enhance_mode,
        "text_enhanced_path": str(text_enhanced_path) if text_enhanced_path else None,
        "blank_guard_triggered": False,
        "fallback_source": None,
        "warnings": warnings,
    }

    try:
        import cv2
        import numpy as np
    except Exception:
        working_path = rendered_image_path
        if remove_red_stamp:
            intermediate = Path(intermediate_path) if intermediate_path else output_path.with_name(
                output_path.stem + "_red_reduced" + output_path.suffix
            )
            red_result = reduce_red_stamp_with_metadata(
                rendered_image_path,
                intermediate,
                mode=red_stamp_mode,
                mask_path=red_mask_path,
                black_text_protection_path=black_text_protection_path,
            )
            working_path = red_result.output_path
            result_metadata.update(
                {
                    "red_pixels_count": red_result.red_pixels_count,
                    "red_pixels_ratio": red_result.red_pixels_ratio,
                    "red_seal_removed": red_result.red_seal_removed,
                    "red_mask_path": str(red_result.mask_path) if red_result.mask_path else None,
                    "seal_removed_path": str(red_result.output_path),
                    **_red_result_metadata(red_result),
                }
            )
            warnings.extend(red_result.warnings)
        _preprocess_with_pillow(working_path, output_path)
        if text_enhanced_path:
            text_artifact = Path(text_enhanced_path)
            text_artifact.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(output_path, text_artifact)
        warnings.append("opencv_unavailable")
        if deskew_mode != "off":
            warnings.append("deskew_skipped_opencv_unavailable")
        before_metrics = _pillow_metrics(rendered_image_path)
        after_metrics = _pillow_metrics(output_path)
        if _foreground_loss(before_metrics, after_metrics):
            shutil.copy2(working_path, output_path)
            after_metrics = _pillow_metrics(output_path)
            result_metadata["blank_guard_triggered"] = True
            result_metadata["fallback_source"] = (
                "seal_removed" if result_metadata["red_seal_removed"] else "original"
            )
            warnings.extend(["preprocess_blank_guard_triggered", "foreground_loss_too_high"])
        result_metadata.update(_metric_metadata(before_metrics, after_metrics))
        result_metadata["warnings"] = _dedupe(warnings)
        _store_metadata(metadata, result_metadata)
        return output_path

    original = _cv2_read_image(rendered_image_path, cv2, np)
    if original is None:
        shutil.copy2(rendered_image_path, output_path)
        warnings.append("preprocess_image_read_failed")
        _store_metadata(metadata, result_metadata)
        return output_path

    working = original
    if remove_red_stamp:
        intermediate = Path(intermediate_path) if intermediate_path else output_path.with_name(
            output_path.stem + "_red_reduced" + output_path.suffix
        )
        red_result = reduce_red_stamp_with_metadata(
            rendered_image_path,
            intermediate,
            mode=red_stamp_mode,
            mask_path=red_mask_path,
            black_text_protection_path=black_text_protection_path,
        )
        reduced = _cv2_read_image(red_result.output_path, cv2, np)
        if reduced is not None:
            working = reduced
        result_metadata.update(
            {
                "red_pixels_count": red_result.red_pixels_count,
                "red_pixels_ratio": red_result.red_pixels_ratio,
                "red_seal_removed": red_result.red_seal_removed,
                "red_mask_path": str(red_result.mask_path) if red_result.mask_path else None,
                "seal_removed_path": str(red_result.output_path),
                **_red_result_metadata(red_result),
            }
        )
        warnings.extend(red_result.warnings)

    before_metrics = _image_metrics(original, cv2, np)
    safe_stage_metrics = _image_metrics(working, cv2, np)
    if _red_removal_guard(before_metrics, safe_stage_metrics):
        working = original
        result_metadata["red_seal_removed"] = False
        result_metadata["blank_guard_triggered"] = True
        result_metadata["fallback_source"] = "original"
        warnings.extend(
            ["red_removal_guard_triggered", "preprocess_blank_guard_triggered", "foreground_loss_too_high"]
        )

    gray = cv2.cvtColor(working, cv2.COLOR_BGR2GRAY)
    normalized = _apply_profile(gray, preprocess_profile, cv2)
    enhance_before = _image_metrics(normalized, cv2, np)
    attempted_enhanced = _enhance_black_text(normalized, text_enhance_mode, cv2, np)
    if text_enhanced_path:
        text_artifact = Path(text_enhanced_path)
        text_artifact.parent.mkdir(parents=True, exist_ok=True)
        _cv2_write_image(text_artifact, attempted_enhanced, cv2)
    enhance_after = _image_metrics(attempted_enhanced, cv2, np)
    result_metadata.update(
        {
            "foreground_before_enhance": round(enhance_before["foreground_ratio"], 6),
            "foreground_after_enhance": round(enhance_after["foreground_ratio"], 6),
            "dark_pixel_ratio_before": round(enhance_before["dark_pixel_ratio"], 6),
            "dark_pixel_ratio_after": round(enhance_after["dark_pixel_ratio"], 6),
        }
    )
    enhance_guard = _text_enhance_guard(enhance_before, enhance_after)
    if enhance_guard:
        candidate = gray
        result_metadata["fallback_source"] = "seal_removed" if result_metadata["red_seal_removed"] else "original"
        warnings.extend(["text_enhance_guard_triggered", enhance_guard])
    else:
        candidate = attempted_enhanced

    candidate, deskew_metadata, deskew_warnings = _deskew_gray(candidate, deskew_mode, cv2, np)
    result_metadata.update(deskew_metadata)
    warnings.extend(deskew_warnings)
    candidate_metrics = _image_metrics(candidate, cv2, np)

    if _foreground_loss(before_metrics, candidate_metrics):
        candidate = working
        candidate_metrics = _image_metrics(candidate, cv2, np)
        result_metadata["blank_guard_triggered"] = True
        result_metadata["fallback_source"] = "seal_removed" if result_metadata["red_seal_removed"] else "original"
        warnings.extend(["preprocess_blank_guard_triggered", "foreground_loss_too_high"])

    _cv2_write_image(output_path, candidate, cv2)
    result_metadata.update(_metric_metadata(before_metrics, candidate_metrics))
    result_metadata["warnings"] = _dedupe(warnings)
    _store_metadata(metadata, result_metadata)
    return output_path


def _apply_profile(gray, profile: str, cv2):
    if profile == "conservative":
        return cv2.createCLAHE(clipLimit=1.15, tileGridSize=(12, 12)).apply(gray)
    balanced = _balance_light(gray, cv2)
    clip_limit = 1.45 if profile == "balanced" else 1.8
    balanced = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(10, 10)).apply(balanced)
    if profile == "balanced":
        return cv2.fastNlMeansDenoising(balanced, None, h=3, templateWindowSize=7, searchWindowSize=21)
    return cv2.fastNlMeansDenoising(balanced, None, h=5, templateWindowSize=7, searchWindowSize=21)


def _enhance_black_text(gray, mode: str, cv2, np):
    if mode == "off":
        return gray.copy()
    settings = {
        "light": (1.10, 0.16),
        "medium": (1.18, 0.28),
        "strong": (1.28, 0.42),
    }
    gamma, sharpen = settings[mode]
    lookup = np.array(
        [min(255, round(((value / 255.0) ** gamma) * 255.0)) for value in range(256)],
        dtype=np.uint8,
    )
    toned = cv2.LUT(gray, lookup)
    blurred = cv2.GaussianBlur(toned, (0, 0), 1.0)
    enhanced = cv2.addWeighted(toned, 1.0 + sharpen, blurred, -sharpen, 0)
    if mode == "strong":
        enhanced = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(12, 12)).apply(enhanced)
    return enhanced


def _deskew_gray(gray, mode: str, cv2, np):
    metadata = {
        "detected_angle": None,
        "deskew_applied": False,
        "deskew_confidence": 0.0,
        "deskew_reason": "deskew_disabled",
    }
    if mode == "off":
        return gray, metadata, []

    angle, confidence, line_count = _detect_horizontal_angle(gray, cv2, np)
    metadata.update(
        {
            "detected_angle": round(angle, 4) if angle is not None else None,
            "deskew_confidence": round(confidence, 4),
        }
    )
    if angle is None:
        metadata["deskew_reason"] = "insufficient_horizontal_evidence"
        return gray, metadata, ["deskew_skipped_low_confidence"]
    if abs(angle) < 0.3:
        metadata["deskew_reason"] = "angle_below_safe_threshold"
        return gray, metadata, []
    if mode == "safe" and abs(angle) > 5.0:
        metadata["deskew_reason"] = "angle_outside_safe_range"
        return gray, metadata, ["deskew_skipped_angle_outside_safe_range"]
    if mode == "safe" and confidence < 0.65:
        metadata["deskew_reason"] = "confidence_below_safe_threshold"
        return gray, metadata, ["deskew_skipped_low_confidence"]
    if mode == "safe" and _has_edge_content(gray, np):
        metadata["deskew_reason"] = "foreground_near_page_edge"
        return gray, metadata, ["deskew_skipped_crop_risk"]
    if mode == "safe" and _looks_multi_column(gray, np):
        metadata["deskew_reason"] = "ambiguous_multi_column_layout"
        return gray, metadata, ["deskew_skipped_ambiguous_layout"]

    rotated = _rotate_expanded(gray, -angle, cv2, np)
    metadata.update(
        {
            "deskew_applied": True,
            "deskew_reason": "forced_rotation" if mode == "force" else "safe_rotation_high_confidence",
            "deskew_line_count": line_count,
        }
    )
    return rotated, metadata, []


def _detect_horizontal_angle(gray, cv2, np):
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    min_length = max(30, gray.shape[1] // 8)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 1800, threshold=35, minLineLength=min_length, maxLineGap=20)
    if lines is None:
        return None, 0.0, 0
    angles = []
    for line in lines[:, 0]:
        x1, y1, x2, y2 = (int(value) for value in line)
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        if abs(angle) <= 12:
            angles.append(angle)
    if len(angles) < 6:
        return None, min(0.5, len(angles) / 12.0), len(angles)
    values = np.asarray(angles, dtype=float)
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    confidence = min(1.0, len(angles) / 18.0) * max(0.0, 1.0 - mad / 1.5)
    return median, confidence, len(angles)


def _rotate_expanded(gray, angle: float, cv2, np):
    height, width = gray.shape[:2]
    center = (width / 2.0, height / 2.0)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    cosine = abs(matrix[0, 0])
    sine = abs(matrix[0, 1])
    new_width = int((height * sine) + (width * cosine))
    new_height = int((height * cosine) + (width * sine))
    matrix[0, 2] += (new_width / 2.0) - center[0]
    matrix[1, 2] += (new_height / 2.0) - center[1]
    return cv2.warpAffine(
        gray,
        matrix,
        (new_width, new_height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=255,
    )


def _has_edge_content(gray, np) -> bool:
    dark = gray < 210
    margin_y = max(2, int(gray.shape[0] * 0.015))
    margin_x = max(2, int(gray.shape[1] * 0.015))
    edge = np.concatenate(
        [
            dark[:margin_y, :].ravel(),
            dark[-margin_y:, :].ravel(),
            dark[:, :margin_x].ravel(),
            dark[:, -margin_x:].ravel(),
        ]
    )
    return float(np.mean(edge)) > 0.01


def _looks_multi_column(gray, np) -> bool:
    dark = gray < 210
    width = gray.shape[1]
    left = float(np.mean(dark[:, int(width * 0.12) : int(width * 0.43)]))
    center = float(np.mean(dark[:, int(width * 0.47) : int(width * 0.53)]))
    right = float(np.mean(dark[:, int(width * 0.57) : int(width * 0.88)]))
    return left > 0.01 and right > 0.01 and center < min(left, right) * 0.18


def _image_metrics(image, cv2, np) -> dict[str, float]:
    gray = image if len(image.shape) == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    histogram = cv2.calcHist([gray], [0], None, [256], [0, 256]).ravel().astype(float)
    probabilities = histogram / max(1.0, float(histogram.sum()))
    nonzero = probabilities[probabilities > 0]
    entropy = float(-np.sum(nonzero * np.log2(nonzero)))
    return {
        "foreground_ratio": float(np.mean(gray < 245)),
        "dark_pixel_ratio": float(np.mean(gray < 200)),
        "mean_brightness": float(np.mean(gray)),
        "entropy": entropy,
    }


def _foreground_loss(before: dict[str, float], after: dict[str, float]) -> bool:
    before_foreground = before["foreground_ratio"]
    before_dark = before["dark_pixel_ratio"]
    if before_foreground < 0.002 and before_dark < 0.001:
        return False
    foreground_lost = after["foreground_ratio"] < max(0.001, before_foreground * 0.30)
    dark_lost = after["dark_pixel_ratio"] < max(0.0005, before_dark * 0.25)
    nearly_white = after["mean_brightness"] > 252.0 and before["mean_brightness"] < 249.0
    return (foreground_lost and dark_lost) or nearly_white


def _red_removal_guard(before: dict[str, float], after: dict[str, float]) -> bool:
    if _foreground_loss(before, after):
        return True
    entropy_collapsed = before["entropy"] > 0.5 and after["entropy"] < before["entropy"] * 0.20
    foreground_halved = after["foreground_ratio"] < before["foreground_ratio"] * 0.45
    return entropy_collapsed and foreground_halved


def _text_enhance_guard(before: dict[str, float], after: dict[str, float]) -> str | None:
    if _foreground_loss(before, after):
        return "foreground_loss_too_high"
    if after["dark_pixel_ratio"] > max(before["dark_pixel_ratio"] * 2.5, before["dark_pixel_ratio"] + 0.08):
        return "dark_pixel_explosion"
    if after["foreground_ratio"] > max(before["foreground_ratio"] * 2.5, before["foreground_ratio"] + 0.12):
        return "foreground_explosion"
    entropy_collapsed = before["entropy"] > 0.5 and after["entropy"] < before["entropy"] * 0.20
    if entropy_collapsed:
        return "text_enhance_entropy_collapse"
    return None


def _metric_metadata(before: dict[str, float], after: dict[str, float]) -> dict[str, float]:
    return {
        "foreground_before": round(before["foreground_ratio"], 6),
        "foreground_after": round(after["foreground_ratio"], 6),
        "dark_pixels_before": round(before["dark_pixel_ratio"], 6),
        "dark_pixels_after": round(after["dark_pixel_ratio"], 6),
        "mean_brightness_before": round(before["mean_brightness"], 3),
        "mean_brightness_after": round(after["mean_brightness"], 3),
        "entropy_before": round(before["entropy"], 4),
        "entropy_after": round(after["entropy"], 4),
    }


def _preprocess_with_pillow(input_path: Path, output_path: Path) -> None:
    with Image.open(input_path) as image:
        processed = ImageOps.autocontrast(image.convert("L"))
        processed = processed.filter(ImageFilter.SHARPEN)
        processed.save(output_path)


def _pillow_metrics(path: Path) -> dict[str, float]:
    with Image.open(path).convert("L") as image:
        histogram = image.histogram()
        total = max(1, image.width * image.height)
        entropy = 0.0
        for count in histogram:
            if count:
                probability = count / total
                entropy -= probability * math.log2(probability)
        return {
            "foreground_ratio": sum(histogram[:245]) / total,
            "dark_pixel_ratio": sum(histogram[:200]) / total,
            "mean_brightness": float(ImageStat.Stat(image).mean[0]),
            "entropy": entropy,
        }


def _balance_light(gray, cv2):
    background = cv2.medianBlur(gray, 31)
    return cv2.divide(gray, background, scale=255)


def _cv2_read_image(path: Path, cv2, np):
    data = np.fromfile(str(path), dtype=np.uint8)
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def _cv2_write_image(path: Path, image, cv2) -> None:
    success, data = cv2.imencode(path.suffix or ".png", image)
    if not success:
        raise ValueError(f"Could not encode processed image: {path}")
    data.tofile(str(path))


def _store_metadata(target: dict[str, Any] | None, values: dict[str, Any]) -> None:
    if target is not None:
        target.clear()
        target.update(values)


def _red_result_metadata(result) -> dict[str, Any]:
    return {
        "red_mask_components": result.red_mask_components,
        "red_mask_method": result.red_mask_method,
        "red_removal_mode": result.red_removal_mode,
        "red_removed_ratio": round(result.red_removed_ratio, 6),
        "red_residual_ratio_estimate": round(result.red_residual_ratio_estimate, 6),
        "dark_text_overlap_ratio": round(result.dark_text_overlap_ratio, 6),
        "black_text_protection_path": (
            str(result.black_text_protection_path) if result.black_text_protection_path else None
        ),
    }


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
