from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class WorkflowState(str, Enum):
    DRAFT = "DRAFT"
    PROCESSING = "PROCESSING"
    PENDING_REVIEW = "PENDING_REVIEW"
    IN_REVIEW = "IN_REVIEW"
    NEEDS_CORRECTION = "NEEDS_CORRECTION"
    REJECTED = "REJECTED"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


VALID_TRANSITIONS: dict[WorkflowState, frozenset[WorkflowState]] = {
    WorkflowState.DRAFT: frozenset({WorkflowState.PROCESSING}),
    WorkflowState.PROCESSING: frozenset({WorkflowState.PENDING_REVIEW}),
    WorkflowState.PENDING_REVIEW: frozenset({WorkflowState.IN_REVIEW}),
    WorkflowState.IN_REVIEW: frozenset(
        {
            WorkflowState.NEEDS_CORRECTION,
            WorkflowState.REJECTED,
            WorkflowState.APPROVED,
        }
    ),
    WorkflowState.NEEDS_CORRECTION: frozenset(
        {WorkflowState.PROCESSING, WorkflowState.PENDING_REVIEW}
    ),
    WorkflowState.REJECTED: frozenset({WorkflowState.ARCHIVED}),
    WorkflowState.APPROVED: frozenset({WorkflowState.PUBLISHED}),
    WorkflowState.PUBLISHED: frozenset({WorkflowState.ARCHIVED}),
    WorkflowState.ARCHIVED: frozenset(),
}


@dataclass(frozen=True)
class WorkflowTransition:
    source: WorkflowState
    target: WorkflowState


class InvalidWorkflowTransition(ValueError):
    def __init__(self, source: WorkflowState, target: WorkflowState) -> None:
        super().__init__(f"Workflow transition is not allowed: {source.value} -> {target.value}")
        self.source = source
        self.target = target


class WorkflowTransitionValidator:
    @staticmethod
    def can_transition(source: WorkflowState, target: WorkflowState) -> bool:
        return target in VALID_TRANSITIONS[source]

    @classmethod
    def ensure_transition(
        cls,
        source: WorkflowState,
        target: WorkflowState,
    ) -> WorkflowTransition:
        if not cls.can_transition(source, target):
            raise InvalidWorkflowTransition(source, target)
        return WorkflowTransition(source=source, target=target)

    @staticmethod
    def transitions() -> tuple[WorkflowTransition, ...]:
        state_order = {state: index for index, state in enumerate(WorkflowState)}
        return tuple(
            WorkflowTransition(source=source, target=target)
            for source in WorkflowState
            for target in sorted(VALID_TRANSITIONS[source], key=state_order.__getitem__)
        )
