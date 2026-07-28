from __future__ import annotations

from court_ocr_extract.domain.workflow import (
    WorkflowState,
    WorkflowTransition,
    WorkflowTransitionValidator,
)


class ReviewService:
    @staticmethod
    def start_review(state: WorkflowState) -> WorkflowTransition:
        return WorkflowTransitionValidator.ensure_transition(
            state,
            WorkflowState.IN_REVIEW,
        )

    @staticmethod
    def approve(state: WorkflowState) -> WorkflowTransition:
        return WorkflowTransitionValidator.ensure_transition(
            state,
            WorkflowState.APPROVED,
        )
