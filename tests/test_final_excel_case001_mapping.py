from __future__ import annotations

from court_ocr_extract.final_excel_builder import build_final_excel_rows


def test_synthetic_shape_keeps_primary_roles_only() -> None:
    defendants = [
        {
            "full_name": f"Bị Cáo Synthetic {index}",
            "birth_date_or_year": f"01/01/{1980 + index}",
            "current_address": f"Vùng Bị Cáo Synthetic {index}",
        }
        for index in range(1, 7)
    ]
    participant_roles = [
        "Bị hại",
        "Người giám hộ",
        "Người bảo vệ quyền và lợi ích hợp pháp của bị hại",
        "Bị hại",
    ]
    participants = [
        {
            "role": role,
            "full_name": f"Người Tham Gia Synthetic {index}",
            "birth_date_or_year": f"sinh năm {2000 + index}",
            "address": f"Vùng Người Tham Gia Synthetic {index}",
        }
        for index, role in enumerate(participant_roles, start=1)
    ]
    result = {
        "document_type": "judgment_criminal_first_instance",
        "metadata": {
            "case_acceptance_number": "999/2099/TLST-HS",
            "case_acceptance_date": "09/04/2099",
        },
        "trial_panel": {"presiding_judge": "Chủ Tọa Synthetic"},
        "defendants": defendants,
        "participants": participants,
    }

    rows = build_final_excel_rows(result)

    assert len(rows) == 8
    assert sum(row["TƯ CÁCH TỐ TỤNG"] == "Bị cáo" for row in rows) == 6
    assert [row["TƯ CÁCH TỐ TỤNG"] for row in rows[6:]] == ["Bị hại", "Bị hại"]
    assert all(row["SỐ THỤ LÝ"] == "999/2099/TLST-HS" for row in rows)
    assert all(row["NGÀY THỤ LÝ (DD/MM/YYYY)"] == "09/04/2099" for row in rows)
    assert all(row["HỌ TÊN CHỦ TỌA"] == "Chủ Tọa Synthetic" for row in rows)
    assert all(row["HỌ TÊN ĐƯƠNG SỰ"] for row in rows)
    assert all(
        row["TƯ CÁCH TỐ TỤNG"]
        not in {"Người giám hộ", "Người bảo vệ quyền và lợi ích hợp pháp của bị hại"}
        for row in rows
    )
