from __future__ import annotations

import json

from court_ocr_extract.decision_tail import DecisionTailRecord
from court_ocr_extract.ocr_backends.base import OCRPage, OCRResult
from court_ocr_extract.ocr_cache import OCRCacheRecord
from court_ocr_extract.pre_content_ab import run_pre_content_ab_test
from court_ocr_extract.settings import PipelineSettings


def test_partial_candidate_coverage_is_visible_in_json_and_html(tmp_path) -> None:
    tail = DecisionTailRecord(
        case_id="synthetic_case",
        source_index=1,
        pdf_hash="synthetic_hash",
        backend="synthetic",
        pages_total=8,
        scanned_page_numbers=[8],
        scan_batches=[[8]],
        heading_found=True,
        heading_page=8,
        heading_line_id="p008_l0001",
        heading_text="QUYẾT ĐỊNH",
        text="",
        lines=[
            _tail_line(1, "QUYẾT ĐỊNH"),
            _tail_line(
                2,
                "1. Xử phạt bị cáo Person Synthetic Alpha 12 tháng tù "
                "về tội “Charge Synthetic Alpha”.",
            ),
            _tail_line(
                3,
                "2. Xử phạt bị cáo Person Synthetic Beta 10 tháng tù.",
            ),
        ],
    )
    run_pre_content_ab_test(
        [_front_record()],
        output_dir=tmp_path,
        settings=PipelineSettings(),
        strategies=["rule_anchor_only"],
        decision_tail_records={"synthetic_case": tail},
    )

    output = json.loads(
        (tmp_path / "cases" / "synthetic_case" / "rule_anchor_only_output.json")
        .read_text(encoding="utf-8")
    )
    assert output["verdict_candidate_count"] == 2
    assert output["parsed_charge_count"] == 1
    assert output["mapped_defendant_count"] == 1
    assert output["unmapped_verdict_count"] == 1
    assert output["invalid_charge_count"] == 0
    assert "verdict_charge_coverage_incomplete:1/2" in output["warnings"]
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "invalid charges: 0" in html
    assert "verdict_charge_coverage_incomplete:1/2" in html


def _tail_line(order: int, text: str) -> dict:
    return {
        "line_id": f"p008_l{order:04d}",
        "page_number": 8,
        "reading_order": order - 1,
        "text": text,
    }


def _front_record() -> OCRCacheRecord:
    texts = [
        "Bản án số: 901/2099/HS-ST",
        "Đối với các bị cáo:",
        "1. Person Synthetic Alpha, sinh năm 1990",
        "2. Person Synthetic Beta, sinh năm 1991",
        "NỘI DUNG VỤ ÁN",
    ]
    lines = [
        {"line_id": f"p001_l{index:04d}", "page_number": 1, "text": text}
        for index, text in enumerate(texts, start=1)
    ]
    return OCRCacheRecord(
        "synthetic_case",
        1,
        "synthetic_hash",
        OCRResult(
            backend="synthetic",
            status="success",
            pages_processed=1,
            marker_found=True,
            marker_page=1,
            text="\n".join(texts),
            pages=[OCRPage(page_index=1, lines=lines)],
        ),
    )
