from __future__ import annotations

from court_ocr_extract.domain.form_engine import (
    CapabilityStatus,
    ExclusionRule,
    FormCatalog,
    FormDefinition,
    FormFieldDefinition,
    FormFieldMapping,
    FormTemplate,
    FormTemplateVersion,
    TemplateFormat,
    get_form_engine_capabilities,
)


def test_phase_zero_capability_matrix_is_fail_closed() -> None:
    capabilities = get_form_engine_capabilities()
    matrix = {
        capability.template_format: capability for capability in capabilities.formats
    }

    assert matrix[TemplateFormat.LEGACY_DOC].capability_status is (
        CapabilityStatus.NOT_IMPLEMENTED
    )
    assert matrix[TemplateFormat.DOCX].capability_status is CapabilityStatus.DECLARED
    assert matrix[TemplateFormat.PDF].capability_status is CapabilityStatus.DECLARED
    assert all(not item.adapter_implemented for item in matrix.values())
    assert capabilities.official_generation_available is False
    assert capabilities.draft_preview_available is False


def test_form_definition_is_config_driven_and_covers_mapping_contract() -> None:
    instruction_rule = ExclusionRule(
        rule_id="synthetic-remove-instruction",
        target="bookmark.synthetic_instruction",
        condition="always",
        validation_rule="bookmark_absent",
        removes_instruction=True,
    )
    mapping = FormFieldMapping(
        field_key="synthetic_case_number",
        source_field="case_number",
        source_entity="court_case",
        source_path="court_case.case_number",
        transformation="trim",
        formatter="plain_text",
        required=True,
        allow_manual_input=False,
        default_value=None,
        visibility_condition="always",
        repeat_rule="once",
        exclusion_rule=None,
        validation_rule="non_empty",
        output_placeholder="bookmark.synthetic_case_number",
        instruction_removal_rule=instruction_rule,
    )
    definition = FormDefinition(
        definition_id="SYNTHETIC_CRIMINAL_FORM_A",
        version=1,
        case_domain="criminal",
        template_version_id="synthetic-template-v1",
        fields=(
            FormFieldDefinition(
                field_key="synthetic_case_number",
                label="Số hồ sơ tổng hợp",
                required=True,
            ),
        ),
        mappings=(mapping,),
    )

    assert definition.mappings == (mapping,)
    assert mapping.source_path == "court_case.case_number"
    assert mapping.instruction_removal_rule is instruction_rule


def test_catalog_and_template_versions_are_generic_versioned_contracts() -> None:
    catalog = FormCatalog(
        catalog_id="synthetic-catalog",
        code="SYNTHETIC_CRIMINAL_CATALOG",
        case_domain="criminal",
    )
    template = FormTemplate(
        template_id="synthetic-template",
        catalog_id=catalog.catalog_id,
        code="SYNTHETIC_CRIMINAL_FORM_A",
    )
    template_version = FormTemplateVersion(
        template_version_id="synthetic-template-v1",
        template_id=template.template_id,
        version=1,
        template_format=TemplateFormat.LEGACY_DOC,
        capability_status=CapabilityStatus.NOT_IMPLEMENTED,
    )

    assert template.catalog_id == catalog.catalog_id
    assert template_version.version == 1
    assert template_version.capability_status is CapabilityStatus.NOT_IMPLEMENTED
