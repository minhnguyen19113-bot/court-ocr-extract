from court_ocr_extract.excel_writer import write_excel
from court_ocr_extract.extraction_pipeline import extract_from_ocr_cache_records
from court_ocr_extract.ocr_backends.base import OCRResult
from court_ocr_extract.ocr_cache import OCRCacheRecord, read_ocr_cache_dir, write_ocr_cache_record
from court_ocr_extract.qa import qa_excel
from court_ocr_extract.review_sampling import ReviewCandidate, select_review_sample
from court_ocr_extract.validation import validate_extraction_payload


def test_mixed_review_sampling_covers_warning_and_marker_not_found():
    candidates = [
        ReviewCandidate("case_001_a", 1, marker_found=True, warnings_count=0),
        ReviewCandidate("case_002_b", 2, marker_found=True, warnings_count=2),
        ReviewCandidate("case_003_c", 3, marker_found=False, warnings_count=0),
        ReviewCandidate("case_004_d", 4, marker_found=True, participants_count=3),
    ]

    selected = select_review_sample(candidates, sample_size=3, seed=7, mode="mixed")

    assert len(selected) == 3
    assert any(item.warnings_count for item in selected)
    assert any(not item.marker_found for item in selected)


def test_validation_flags_status_phrase_as_name():
    payload = {
        "case": {"filing_date": "03/04/2025"},
        "participants": [
            {
                "procedural_role": "Bị cáo",
                "full_name": "có mặt tại phiên tòa",
                "confidence": {"procedural_role": 0.9, "full_name": 0.9},
                "evidence": {"procedural_role": "Bị cáo", "full_name": "có mặt tại phiên tòa"},
            }
        ],
    }

    validated = validate_extraction_payload(payload)

    warnings = validated["participants"][0]["warnings"]
    assert "full_name looks like a status phrase." in warnings


def test_ocr_cache_roundtrip_does_not_require_source_filename(tmp_path):
    record = OCRCacheRecord(
        case_id="case_001_abcd",
        source_index=1,
        pdf_hash="abcd",
        result=OCRResult(
            backend="contract_fixture",
            status="success",
            pages_processed=1,
            marker_found=True,
            marker_page=1,
            text="contract fixture text",
        ),
    )

    write_ocr_cache_record(record, tmp_path)
    records = read_ocr_cache_dir(tmp_path)

    assert records[0].case_id == "case_001_abcd"
    assert records[0].result.text == "contract fixture text"


def test_excel_writer_and_qa_emit_counts_only(tmp_path):
    drafts = [
        {
            "case_id": "case_001_abcd",
            "ocr_backend": "contract_fixture",
            "extractor_backend": "contract_fixture",
            "marker_found": True,
            "status": "success",
            "payload": validate_extraction_payload(
                {
                    "case": {
                        "case_type": "Hình sự",
                        "filing_number": "12/2025/TLST-HS",
                        "filing_date": "03/04/2025",
                        "legal_relationship": "Quan hệ kiểm tra contract",
                        "presiding_judge": "Người Chủ Tọa",
                    },
                    "participants": [
                        {
                            "procedural_role": "Bị cáo",
                            "full_name": "Người Tham Gia A",
                            "birth_year": "1990",
                            "id_number": "012345678901",
                            "address": "Địa chỉ kiểm tra contract",
                            "confidence": {
                                "procedural_role": 0.9,
                                "full_name": 0.9,
                                "birth_year": 0.9,
                                "id_number": 0.9,
                                "address": 0.9,
                            },
                            "evidence": {
                                "procedural_role": "Bị cáo",
                                "full_name": "Người Tham Gia A",
                                "birth_year": "1990",
                                "id_number": "012345678901",
                                "address": "Địa chỉ kiểm tra contract",
                            },
                        }
                    ],
                }
            ),
        }
    ]
    excel_path = tmp_path / "contract.xlsx"

    write_excel(drafts, excel_path)
    summary = qa_excel(excel_path)

    assert summary["total rows"] == 1
    assert summary["invalid id count"] == 0


def test_debug_json_writes_internal_jsonl_and_summary_xlsx(tmp_path):
    record = OCRCacheRecord(
        case_id="case_001_abcd",
        source_index=1,
        pdf_hash="abcd",
        result=OCRResult(
            backend="contract_fixture",
            status="success",
            pages_processed=1,
            marker_found=False,
            marker_page=None,
            text="contract fixture text",
        ),
    )
    debug_dir = tmp_path / "draft"

    drafts = extract_from_ocr_cache_records(
        [record],
        extractor_name="rule_support_only_for_validation",
        debug_json_dir=debug_dir,
    )

    assert len(drafts) == 1
    assert (debug_dir / "draft_internal.jsonl").exists()
    assert (debug_dir / "draft_summary.xlsx").exists()
