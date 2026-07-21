from __future__ import annotations

from dataclasses import dataclass

from court_ocr_extract.extractors.pre_content_anchor_segmenter import fold_text


PRIMARY_FINAL_ROLES = frozenset(
    {
        "Bị cáo",
        "Bị hại",
        "Pháp nhân thương mại bị cáo",
    }
)

PRIMARY_ROLE_ALIASES = {
    "Người bị hại": "Bị hại",
}

OTHER_PARTICIPANT_ROLES = (
    "Người bảo vệ quyền và lợi ích hợp pháp",
    "Người giám hộ",
    "Người đại diện",
    "Người bào chữa",
    "Người làm chứng",
    "Người phiên dịch",
    "Người giám định",
    "Người định giá",
    "Người chứng kiến",
)

COURT_PROCEDURAL_ROLES = (
    "Thẩm phán",
    "Chủ tọa",
    "Hội thẩm",
    "Thư ký",
    "Kiểm sát viên",
    "Điều tra viên",
)


@dataclass(frozen=True)
class FinalRoleDecision:
    original_role: str
    normalized_role: str
    category: str
    include_in_final: bool
    include_in_other: bool
    reason: str


_PRIMARY_BY_FOLDED = {fold_text(role): role for role in PRIMARY_FINAL_ROLES}
_ALIASES_BY_FOLDED = {
    fold_text(alias): canonical for alias, canonical in PRIMARY_ROLE_ALIASES.items()
}
_OTHER_BY_FOLDED = tuple(
    (fold_text(role), role)
    for role in sorted(OTHER_PARTICIPANT_ROLES, key=len, reverse=True)
)
_COURT_FOLDED = tuple(fold_text(role) for role in COURT_PROCEDURAL_ROLES)


def classify_final_role(role: object) -> FinalRoleDecision:
    original = _clean(role)
    folded = fold_text(original)
    if folded in _PRIMARY_BY_FOLDED:
        normalized = _PRIMARY_BY_FOLDED[folded]
        return FinalRoleDecision(
            original,
            normalized,
            "primary",
            True,
            False,
            "primary_final_role",
        )
    if folded in _ALIASES_BY_FOLDED:
        normalized = _ALIASES_BY_FOLDED[folded]
        return FinalRoleDecision(
            original,
            normalized,
            "primary_alias",
            True,
            False,
            "explicit_primary_role_alias",
        )
    if any(folded == value or folded.startswith(value + " ") for value in _COURT_FOLDED):
        return FinalRoleDecision(
            original,
            original,
            "court_procedural",
            False,
            False,
            "court_role_not_user_entity",
        )
    for prefix, canonical in _OTHER_BY_FOLDED:
        if folded == prefix or folded.startswith(prefix + " "):
            return FinalRoleDecision(
                original,
                canonical,
                "other_participant",
                False,
                True,
                "supporting_participant_role",
            )
    return FinalRoleDecision(
        original,
        original,
        "other_unclassified",
        False,
        True,
        "unclassified_participant_role_requires_review",
    )


def normalized_row_identity(case_id: object, full_name: object, role: object) -> tuple[str, str, str]:
    decision = classify_final_role(role)
    return (
        fold_text(_clean(case_id)),
        fold_text(_clean(full_name)),
        fold_text(decision.normalized_role),
    )


def _clean(value: object) -> str:
    return " ".join(str(value or "").split()).strip(" ;")
