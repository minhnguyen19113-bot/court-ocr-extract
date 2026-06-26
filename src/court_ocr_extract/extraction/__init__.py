"""Local information extraction backends."""

from court_ocr_extract.extraction.local_llm_extractor import LocalLLMExtractor
from court_ocr_extract.extraction.merge import merge_extractor_outputs

__all__ = ["LocalLLMExtractor", "merge_extractor_outputs"]
