from __future__ import annotations

import pytest

from court_ocr_extract.domain.form_engine import (
    GenerationMode,
    GenerationRequest,
    GenerationSource,
    TemplateFormat,
)
from court_ocr_extract.services.form_service import (
    FormGenerationRejected,
    FormGenerationViolationCode,
    FormService,
)


def request_for(
    source: GenerationSource,
    *,
    locked: bool = False,
    mode: GenerationMode = GenerationMode.OFFICIAL,
) -> GenerationRequest:
    return GenerationRequest(
        request_id="synthetic-request-1",
        definition_id="SYNTHETIC_CRIMINAL_FORM_A",
        definition_version=1,
        template_version_id="synthetic-template-v1",
        template_version=1,
        source=source,
        source_id="synthetic-source-1",
        source_version=1,
        output_format=TemplateFormat.DOCX,
        mode=mode,
        source_is_locked=locked,
    )


@pytest.mark.parametrize(
    "source",
    [GenerationSource.MACHINE_DRAFT, GenerationSource.REVIEW_DRAFT],
)
def test_official_generation_rejects_unapproved_sources(
    source: GenerationSource,
) -> None:
    validation = FormService().validate(request_for(source))

    assert (
        FormGenerationViolationCode.OFFICIAL_SOURCE_NOT_APPROVED_OR_PUBLISHED
        in validation.violation_codes
    )


def test_approved_snapshot_must_be_locked() -> None:
    validation = FormService().validate(
        request_for(GenerationSource.APPROVED_SNAPSHOT)
    )

    assert (
        FormGenerationViolationCode.APPROVED_SNAPSHOT_NOT_LOCKED
        in validation.violation_codes
    )


def test_draft_preview_is_unsupported_in_phase_zero() -> None:
    validation = FormService().validate(
        request_for(
            GenerationSource.REVIEW_DRAFT,
            mode=GenerationMode.PREVIEW,
        )
    )

    assert (
        FormGenerationViolationCode.DRAFT_PREVIEW_UNSUPPORTED
        in validation.violation_codes
    )


@pytest.mark.parametrize(
    ("source", "locked"),
    [
        (GenerationSource.APPROVED_SNAPSHOT, True),
        (GenerationSource.PUBLISHED_CORE, False),
    ],
)
def test_valid_official_source_still_rejects_unavailable_adapter(
    source: GenerationSource,
    locked: bool,
) -> None:
    request = request_for(source, locked=locked)
    validation = FormService().validate(request)

    assert validation.violation_codes == (
        FormGenerationViolationCode.ADAPTER_UNAVAILABLE,
    )
    with pytest.raises(FormGenerationRejected) as error:
        FormService().generate(request)
    assert error.value.violation_codes == (
        FormGenerationViolationCode.ADAPTER_UNAVAILABLE,
    )

