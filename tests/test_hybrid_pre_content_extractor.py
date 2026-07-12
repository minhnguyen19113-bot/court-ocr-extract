from __future__ import annotations

from court_ocr_extract.extractors.hybrid_pre_content_extractor import HybridPreContentExtractor
from court_ocr_extract.settings import PipelineSettings


def test_high_confidence_rule_value_is_not_overwritten_and_conflict_is_recorded() -> None:
    def fake_llm(prompt, text):
        return {
            "metadata": {"judgment_number": "LLM-999", "judgment_date": "10/01/2026"},
            "trial_panel": {}, "defendants": [], "participants": [],
            "evidence": [{"field": "metadata.judgment_number", "line_id": "p001_l0001", "text": "synthetic"}],
        }

    output = HybridPreContentExtractor(PipelineSettings(), llm_callable=fake_llm).extract(
        _segment(["Bản án số: 01/2026/HS-ST", "NHÂN DANH", "Bị cáo: Nguyễn A"]),
        case_id="synthetic",
    )

    assert output["metadata"]["judgment_number"] == "01/2026/HS-ST"
    assert output["metadata"]["judgment_date"] == "10/01/2026"
    assert output["conflicts"][0]["llm_value"] == "LLM-999"
    assert output["needs_review"] is True


def test_llm_can_fill_missing_defendants_with_evidence() -> None:
    def fake_llm(prompt, text):
        return {
            "defendants": [{"full_name": "Tên synthetic", "evidence_line_ids": ["p001_l0002"]}],
            "evidence": [{"field": "defendants[0].full_name", "line_id": "p001_l0002", "text": "Bị cáo"}],
        }

    output = HybridPreContentExtractor(PipelineSettings(), llm_callable=fake_llm).extract(
        _segment(["Bản án số: 01/2026/HS-ST", "Không có defendant anchor rõ"]),
        case_id="synthetic",
    )

    assert output["defendants"][0]["full_name"] == "Tên synthetic"
    assert output["defendants"][0]["evidence_line_ids"] == ["p001_l0002"]


def _segment(texts):
    return {
        "document_type": "judgment_criminal_first_instance",
        "pre_content_text": "\n".join(texts),
        "pre_content_lines": [
            {"line_id": f"p001_l{index:04d}", "page_number": 1, "text": text}
            for index, text in enumerate(texts, start=1)
        ],
        "warnings": [],
    }
