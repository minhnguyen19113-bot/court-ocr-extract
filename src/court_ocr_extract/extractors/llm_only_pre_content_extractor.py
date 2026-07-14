from __future__ import annotations

from pathlib import Path
from court_ocr_extract.extractors.pre_content_chunking import LLMCallable, extract_pre_content_chunks
from court_ocr_extract.settings import PipelineSettings


class LLMOnlyPreContentExtractor:
    name = "llm_only"

    def __init__(self, settings: PipelineSettings, *, llm_callable: LLMCallable | None = None) -> None:
        self.settings = settings
        self._llm_callable = llm_callable

    def extract(self, segment: dict[str, Any], *, case_id: str) -> dict[str, Any]:
        output = extract_pre_content_chunks(
            segment,
            settings=self.settings,
            prompt=_load_prompt("pre_content_llm_only_prompt.vi.md"),
            strategy=self.name,
            llm_callable=self._llm_callable,
        )
        output["case_id"] = case_id
        output["warnings"].extend(str(item) for item in segment.get("warnings", []) if item)
        return output


def _load_prompt(name: str) -> str:
    path = Path(__file__).resolve().parents[3] / "prompts" / name
    return path.read_text(encoding="utf-8")
