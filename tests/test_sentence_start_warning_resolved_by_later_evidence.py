from tests.test_completeness_validates_aggregate_not_individual_evidence import (
    test_completeness_validates_aggregate_not_individual_evidence,
)


def test_sentence_start_warning_resolved_by_later_evidence() -> None:
    test_completeness_validates_aggregate_not_individual_evidence()
