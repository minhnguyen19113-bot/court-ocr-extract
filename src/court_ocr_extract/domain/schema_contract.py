from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from court_ocr_extract.final_excel_schema import (
    FINAL_EXCEL_COLUMNS,
    FINAL_EXCEL_SHEET_NAME,
)


@dataclass(frozen=True)
class SchemaColumn:
    key: str
    label: str
    export_order: int
    required: bool | None = None
    review_rule: str = "DOMAIN_POLICY"


@dataclass(frozen=True)
class SchemaContract:
    schema_id: str
    schema_version: str
    case_domain: str
    sheet_name: str
    columns: tuple[SchemaColumn, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


CRIMINAL_FINAL_EXCEL_SCHEMA = SchemaContract(
    schema_id="criminal.final_excel",
    schema_version="1.0.0",
    case_domain="criminal",
    sheet_name=FINAL_EXCEL_SHEET_NAME,
    columns=tuple(
        SchemaColumn(
            key=column_name,
            label=column_name,
            export_order=index,
        )
        for index, column_name in enumerate(FINAL_EXCEL_COLUMNS, start=1)
    ),
)


def get_final_excel_schema_contract() -> SchemaContract:
    return CRIMINAL_FINAL_EXCEL_SCHEMA


def get_schema_contract(
    *,
    case_domain: str = "criminal",
    schema_id: str = "criminal.final_excel",
) -> SchemaContract:
    if case_domain != CRIMINAL_FINAL_EXCEL_SCHEMA.case_domain:
        raise ValueError(f"Unsupported case domain in Phase 0: {case_domain}")
    if schema_id != CRIMINAL_FINAL_EXCEL_SCHEMA.schema_id:
        raise ValueError(f"Unsupported schema in Phase 0: {schema_id}")
    return CRIMINAL_FINAL_EXCEL_SCHEMA
