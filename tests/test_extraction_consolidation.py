from pathlib import Path

import court_ocr_extract.extraction_pipeline as extraction_pipeline
import court_ocr_extract.extractors.local_llm_extractor as local_llm_module
from court_ocr_extract.extraction_pipeline import extract_from_ocr_cache_records
from court_ocr_extract.extractors.base import ExtractorBackendStatus
from court_ocr_extract.extractors.local_llm_extractor import LocalLLMExtractor
from court_ocr_extract.extractors.rule_support import RuleSupportExtractor
from court_ocr_extract.ocr_backends.base import OCRResult
from court_ocr_extract.ocr_cache import OCRCacheRecord
from court_ocr_extract.settings import PipelineSettings
from court_ocr_extract.validation import row_needs_review


REPO_ROOT = Path(__file__).resolve().parents[1]
REMOVED_EXTRACTION_PATHS = [
    "src/court_ocr_extract/extraction/base.py",
    "src/court_ocr_extract/extraction/local_llm_extractor.py",
    "src/court_ocr_extract/extraction/rule_support.py",
    "src/court_ocr_extract/extractor.py",
    "src/court_ocr_extract/llm.py",
]


def test_canonical_extraction_modules_replace_legacy_paths() -> None:
    assert extraction_pipeline.extract_from_ocr_cache_records
    assert LocalLLMExtractor
    assert RuleSupportExtractor
    assert all(not (REPO_ROOT / path).exists() for path in REMOVED_EXTRACTION_PATHS)


def test_local_llm_contract_uses_fake_response_without_network(monkeypatch) -> None:
    extractor = LocalLLMExtractor(PipelineSettings())

    def fail_network(*args, **kwargs):
        raise AssertionError("Network must not be called by this contract test.")

    fake_payload = {
        "case": {"case_type": "Synthetic", "filing_number": "SYN-001"},
        "participants": [{
            "procedural_role": "Bị cáo", "full_name": "Người synthetic",
            "birth_year": None, "id_number": None, "address": None,
            "confidence": {"procedural_role": 0.9, "full_name": 0.9},
            "evidence": {"procedural_role": "Bị cáo", "full_name": "Người synthetic"},
            "warnings": [],
        }],
        "document_warnings": [],
    }
    monkeypatch.setattr("urllib.request.urlopen", fail_network)
    monkeypatch.setattr(
        local_llm_module.LocalLLMClient,
        "generate_json",
        lambda self, **kwargs: fake_payload,
    )

    payload = extractor.extract_from_text("Synthetic OCR contract text", case_id="synthetic_case")

    assert payload["case"]["filing_number"] == "SYN-001"
    assert payload["participants"][0]["evidence"]["full_name"] == "Người synthetic"
    assert payload["participants"][0]["warnings"] == []


def test_orchestrator_preserves_case_id_evidence_and_review_contract(monkeypatch) -> None:
    class FakeExtractor:
        name = "synthetic"

        def check_available(self):
            return ExtractorBackendStatus(self.name, True, "synthetic")

        def extract_from_text(self, text: str, *, case_id: str):
            return {
                "case": {"case_type": "Synthetic"},
                "participants": [
                    {
                        "procedural_role": "Bị cáo",
                        "full_name": "Người synthetic",
                        "confidence": {"procedural_role": 0.9, "full_name": 0.9},
                        "evidence": {
                            "procedural_role": "Bị cáo",
                            "full_name": "Người synthetic",
                        },
                        "warnings": [],
                    }
                ],
                "document_warnings": [],
            }

    monkeypatch.setattr(
        extraction_pipeline,
        "get_extractor_backend",
        lambda name: FakeExtractor(),
    )
    record = OCRCacheRecord(
        case_id="synthetic_case_001",
        source_index=1,
        pdf_hash="synthetic_hash",
        result=OCRResult(
            backend="synthetic_ocr",
            status="success",
            pages_processed=1,
            marker_found=True,
            marker_page=1,
            text="Synthetic OCR contract text",
        ),
    )

    draft = extract_from_ocr_cache_records(
        [record],
        extractor_name="synthetic",
    )[0]
    participant = draft["payload"]["participants"][0]

    assert draft["case_id"] == "synthetic_case_001"
    assert participant["evidence"]["full_name"] == "Người synthetic"
    assert participant["warnings"] == []
    assert row_needs_review(draft["payload"], participant) is False
