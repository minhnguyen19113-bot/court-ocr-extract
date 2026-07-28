from __future__ import annotations

import pytest

from court_ocr_extract.domain.workflow import (
    VALID_TRANSITIONS,
    InvalidWorkflowTransition,
    WorkflowState,
    WorkflowTransitionValidator,
)


def test_workflow_states_and_valid_transitions_are_explicit() -> None:
    assert [state.value for state in WorkflowState] == [
        "DRAFT",
        "PROCESSING",
        "PENDING_REVIEW",
        "IN_REVIEW",
        "NEEDS_CORRECTION",
        "REJECTED",
        "APPROVED",
        "PUBLISHED",
        "ARCHIVED",
    ]
    assert VALID_TRANSITIONS[WorkflowState.APPROVED] == {
        WorkflowState.PUBLISHED
    }
    assert WorkflowTransitionValidator.can_transition(
        WorkflowState.DRAFT,
        WorkflowState.PROCESSING,
    )
    assert WorkflowTransitionValidator.can_transition(
        WorkflowState.NEEDS_CORRECTION,
        WorkflowState.PENDING_REVIEW,
    )


@pytest.mark.parametrize(
    "source",
    [state for state in WorkflowState if state is not WorkflowState.APPROVED],
)
def test_only_approved_can_transition_to_published(source: WorkflowState) -> None:
    assert not WorkflowTransitionValidator.can_transition(
        source,
        WorkflowState.PUBLISHED,
    )
    with pytest.raises(InvalidWorkflowTransition):
        WorkflowTransitionValidator.ensure_transition(
            source,
            WorkflowState.PUBLISHED,
        )


def test_approved_and_published_are_distinct_states() -> None:
    assert WorkflowState.APPROVED is not WorkflowState.PUBLISHED
    transition = WorkflowTransitionValidator.ensure_transition(
        WorkflowState.APPROVED,
        WorkflowState.PUBLISHED,
    )
    assert transition.source is WorkflowState.APPROVED
    assert transition.target is WorkflowState.PUBLISHED
