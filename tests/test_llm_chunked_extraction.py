from __future__ import annotations

import json

from court_ocr_extract.extractors.llm_only_pre_content_extractor import LLMOnlyPreContentExtractor
from court_ocr_extract.settings import PipelineSettings


def test_multi_defendant_input_is_split_and_one_failure_keeps_successful_chunk() -> None:
    calls = []

    def fake_llm(prompt, text):
        request = json.loads(text)
        calls.append(request["chunk_name"])
        if request["chunk_name"] == "defendant_002":
            raise RuntimeError("synthetic chunk failure")
        if request["target"] == "defendants":
            return {"defendants": [{"full_name": "Synthetic Person A", "evidence_line_ids": [request["lines"][0]["line_id"]]}]}
        return {"metadata": {"court_name": "Synthetic Court"}}

    output = LLMOnlyPreContentExtractor(
        PipelineSettings(), llm_callable=fake_llm
    ).extract(_segment(), case_id="synthetic")

    assert "defendant_001" in calls
    assert "defendant_002" in calls
    assert output["status"] == "llm_only_partial"
    assert output["defendants"][0]["full_name"] == "Synthetic Person A"
    assert any("defendant_002" in warning for warning in output["warnings"])


def test_all_chunks_failed_returns_failure_envelope_without_null_schema() -> None:
    def fail(prompt, text):
        raise RuntimeError("synthetic unavailable")

    output = LLMOnlyPreContentExtractor(
        PipelineSettings(), llm_callable=fail
    ).extract(_segment(), case_id="synthetic")

    assert output["status"] == "llm_only_failed"
    assert output["result_valid"] is False
    assert "metadata" not in output
    assert output["llm_status"]


def _segment():
    texts = [
        "SYNTHETIC COURT", "Bản án synthetic", "Thẩm phán: Synthetic Judge",
        "Bị cáo: Synthetic Person A", "Dữ liệu contract A", "2. Bị cáo: Synthetic Person B",
        "Dữ liệu contract B", "Bị hại: Synthetic Participant",
    ]
    return {
        "document_type": "judgment_criminal_first_instance",
        "pre_content_text": "\n".join(texts),
        "pre_content_lines": [
            {"line_id": f"p001_l{i:04d}", "page_number": 1, "text": text}
            for i, text in enumerate(texts, 1)
        ],
        "warnings": [],
    }
