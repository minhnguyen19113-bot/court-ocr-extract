from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReviewCandidate:
    case_id: str
    source_index: int
    status: str = "success"
    marker_found: bool = False
    warnings_count: int = 0
    participants_count: int = 0
    min_confidence: float | None = None
    metadata: dict[str, str] = field(default_factory=dict)


def select_review_sample(
    candidates: list[ReviewCandidate],
    *,
    sample_size: int,
    seed: int = 42,
    mode: str = "mixed",
) -> list[ReviewCandidate]:
    if sample_size <= 0 or len(candidates) <= sample_size:
        return list(candidates)

    rng = random.Random(seed)
    mode = mode.lower()
    if mode == "first":
        return candidates[:sample_size]
    if mode == "random":
        return rng.sample(candidates, sample_size)
    if mode == "warnings":
        return _take_ranked(candidates, sample_size, lambda item: item.warnings_count)
    if mode == "failed":
        failed = [item for item in candidates if item.status != "success"]
        return _fill(failed, candidates, sample_size, rng)
    return _mixed_sample(candidates, sample_size, rng)


def _mixed_sample(
    candidates: list[ReviewCandidate],
    sample_size: int,
    rng: random.Random,
) -> list[ReviewCandidate]:
    selected: list[ReviewCandidate] = []
    buckets = [
        [item for item in candidates if item.status == "success" and item.warnings_count == 0],
        [item for item in candidates if item.warnings_count > 0],
        [item for item in candidates if not item.marker_found],
        [item for item in candidates if item.participants_count > 1],
        [item for item in candidates if item.min_confidence is not None and item.min_confidence < 0.5],
    ]
    reasons = ["random_success", "warning", "marker_not_found", "many_participants", "low_confidence"]
    for reason, bucket in zip(reasons, buckets, strict=False):
        if not bucket or len(selected) >= sample_size:
            continue
        item = rng.choice(bucket)
        selected.append(_with_reason(item, reason))

    remaining = [item for item in candidates if item.case_id not in {x.case_id for x in selected}]
    rng.shuffle(remaining)
    selected.extend(_with_reason(item, "random_fill") for item in remaining[: sample_size - len(selected)])
    return selected[:sample_size]


def _take_ranked(candidates: list[ReviewCandidate], sample_size: int, key) -> list[ReviewCandidate]:
    ranked = sorted(candidates, key=key, reverse=True)
    return ranked[:sample_size]


def _fill(
    preferred: list[ReviewCandidate],
    all_candidates: list[ReviewCandidate],
    sample_size: int,
    rng: random.Random,
) -> list[ReviewCandidate]:
    selected = list(preferred[:sample_size])
    if len(selected) >= sample_size:
        return selected
    remaining = [item for item in all_candidates if item.case_id not in {x.case_id for x in selected}]
    rng.shuffle(remaining)
    selected.extend(remaining[: sample_size - len(selected)])
    return selected


def _with_reason(candidate: ReviewCandidate, reason: str) -> ReviewCandidate:
    metadata = dict(candidate.metadata)
    metadata.setdefault("select_reason", reason)
    return ReviewCandidate(
        case_id=candidate.case_id,
        source_index=candidate.source_index,
        status=candidate.status,
        marker_found=candidate.marker_found,
        warnings_count=candidate.warnings_count,
        participants_count=candidate.participants_count,
        min_confidence=candidate.min_confidence,
        metadata=metadata,
    )
