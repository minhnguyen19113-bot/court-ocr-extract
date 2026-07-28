from __future__ import annotations

import pytest

from court_ocr_extract.domain.schema_contract import (
    get_final_excel_schema_contract,
    get_schema_contract,
)
from court_ocr_extract.final_excel_schema import (
    FINAL_EXCEL_COLUMNS,
    FINAL_EXCEL_SHEET_NAME,
)


def test_schema_contract_derives_canonical_fourteen_columns() -> None:
    contract = get_final_excel_schema_contract()

    assert contract.schema_id == "criminal.final_excel"
    assert contract.schema_version == "1.0.0"
    assert contract.case_domain == "criminal"
    assert contract.sheet_name == FINAL_EXCEL_SHEET_NAME
    assert [column.label for column in contract.columns] == FINAL_EXCEL_COLUMNS
    assert [column.export_order for column in contract.columns] == list(range(1, 15))
    assert all(column.required is None for column in contract.columns)
    assert len({column.key for column in contract.columns}) == 14


def test_schema_registry_fails_closed_for_future_domains() -> None:
    assert get_schema_contract() is get_final_excel_schema_contract()
    with pytest.raises(ValueError, match="Unsupported case domain"):
        get_schema_contract(case_domain="civil")
