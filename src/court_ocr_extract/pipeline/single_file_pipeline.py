from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from court_ocr_extract.config import Settings, get_settings
from court_ocr_extract.export.excel_writer import write_excel
from court_ocr_extract.extraction.gliner_extractor import GLiNERExtractor
from court_ocr_extract.extraction.local_llm_extractor import LocalLLMExtractor
from court_ocr_extract.extraction.merge import merge_extractor_outputs
from court_ocr_extract.extraction.rule_support import anchor_support_output
from court_ocr_extract.extraction.validators import validate_extraction
from court_ocr_extract.file_utils import (
    safe_stem,
    sha256_file,
    sha256_text,
    short_hash,
    store_original_pdf,
    write_json,
    write_text,
)
from court_ocr_extract.models import (
    FileProcessMetadata,
    OcrDocument,
    ProcessResult,
    model_to_dict,
    path_to_str,
)
from court_ocr_extract.pdf.validate_pdf import validate_pdf
from court_ocr_extract.pipeline.early_stop_pipeline import EarlyStopConfig, EarlyStopPipeline
from court_ocr_extract.postprocess.normalize_text import normalize_ocr_text
from court_ocr_extract.postprocess.section_splitter import split_before_marker
from court_ocr_extract.privacy import redact_sensitive_payload


LOGGER = logging.getLogger(__name__)


def process_pdf(
    pdf_path: str | Path,
    *,
    dpi: int | None = None,
    remove_red_stamp: bool | None = None,
    max_scan_pages: int | None = None,
    max_pages: int | None = None,
    stop_on_marker: bool | None = None,
    stop_after_marker: bool | None = None,
    use_local_llm: bool | None = None,
    force: bool | None = None,
    settings: Settings | None = None,
    mock_page_texts: dict[int, str] | None = None,
) -> ProcessResult:
    settings = settings or get_settings()
    settings.ensure_dirs()

    pdf_path = Path(pdf_path)
    page_count = validate_pdf(pdf_path)
    stored_pdf = store_original_pdf(pdf_path, settings.raw_pdf_dir)
    dpi = dpi or settings.ocr_dpi
    remove_red_stamp = settings.enable_red_stamp_removal if remove_red_stamp is None else remove_red_stamp
    max_scan_pages = max_scan_pages or max_pages or settings.max_scan_pages
    stop_on_marker = (
        settings.stop_on_section_marker
        if stop_on_marker is None and stop_after_marker is None
        else bool(stop_on_marker if stop_on_marker is not None else stop_after_marker)
    )
    force = settings.force_reprocess if force is None else force
    use_local_llm = settings.enable_local_llm if use_local_llm is None else use_local_llm

    file_hash = sha256_file(stored_pdf)
    cache_key = _cache_key(
        file_hash=file_hash,
        dpi=dpi,
        remove_red_stamp=remove_red_stamp,
        max_scan_pages=max_scan_pages,
        stop_on_marker=stop_on_marker,
        force_full_ocr=settings.force_full_ocr,
        marker=settings.section_marker,
    )
    stem = f"{safe_stem(stored_pdf.name)}_{short_hash(cache_key, 10)}"
    cache_json = settings.ocr_raw_dir / f"{stem}.json"

    if cache_json.exists() and not force:
        from court_ocr_extract.ocr.surya_adapter import load_ocr_document

        LOGGER.info("Using cached OCR for file_id=%s", short_hash(file_hash))
        ocr_document = load_ocr_document(cache_json)
    else:
        from court_ocr_extract.ocr.surya_adapter import save_ocr_document

        ocr_document = _ocr_until_marker(
            pdf_path=stored_pdf,
            output_stem=stem,
            page_count=page_count,
            dpi=dpi,
            remove_red_stamp=remove_red_stamp,
            max_scan_pages=max_scan_pages,
            stop_on_marker=stop_on_marker,
            force_full_ocr=settings.force_full_ocr,
            settings=settings,
            mock_page_texts=mock_page_texts,
        )
        ocr_document.file_id = short_hash(file_hash)
        ocr_document.preprocessing_config = {
            "dpi": dpi,
            "remove_red_stamp": remove_red_stamp,
            "max_scan_pages": max_scan_pages,
            "stop_on_marker": stop_on_marker,
            "section_marker": settings.section_marker,
        }
        save_ocr_document(ocr_document, cache_json)

    result = process_ocr_document(
        ocr_document,
        source_file=stored_pdf.name,
        output_stem=stem,
        settings=settings,
        use_local_llm=use_local_llm,
        marker_found=ocr_document.marker_found,
        marker_text=settings.section_marker if ocr_document.marker_found else None,
        marker_page=ocr_document.marker_page,
    )
    result.source_pdf = path_to_str(pdf_path)
    result.stored_pdf = path_to_str(stored_pdf)
    result.ocr_raw_json = path_to_str(cache_json)
    result.metadata = FileProcessMetadata(
        file_id=short_hash(file_hash),
        filename=stored_pdf.name,
        path="[redacted]",
        page_count=page_count,
        status="completed",
        pages_ocr=ocr_document.pages_ocr,
        marker_page=ocr_document.marker_page,
        stop_reason=ocr_document.stop_reason,
    )
    _write_checkpoint(settings, result)
    return result


def process_text_file(
    text_path: str | Path,
    settings: Settings | None = None,
    output_stem: str | None = None,
    use_local_llm: bool | None = None,
) -> ProcessResult:
    text_path = Path(text_path)
    text = text_path.read_text(encoding="utf-8")
    return process_ocr_text(
        text,
        source_file=text_path.name,
        output_stem=output_stem or safe_stem(text_path.name),
        settings=settings,
        use_local_llm=use_local_llm,
    )


def process_ocr_document(
    document: OcrDocument,
    *,
    source_file: str | None,
    output_stem: str,
    settings: Settings,
    use_local_llm: bool,
    marker_found: bool,
    marker_text: str | None,
    marker_page: int | None,
) -> ProcessResult:
    return process_ocr_text(
        document.text,
        source_file=source_file,
        output_stem=output_stem,
        settings=settings,
        use_local_llm=use_local_llm,
        marker_found=marker_found,
        marker_text=marker_text,
        marker_page=marker_page,
        metadata={
            "pages_ocr": document.pages_ocr,
            "stop_reason": document.stop_reason,
            "marker_position": document.marker_position,
            "marker_score": document.marker_score,
            "ocr_pages": [model_to_dict(page) for page in document.pages],
        },
    )


def process_ocr_text(
    text: str,
    source_file: str | None = None,
    output_stem: str = "ocr_text",
    settings: Settings | None = None,
    use_local_llm: bool | None = None,
    marker_found: bool | None = None,
    marker_text: str | None = None,
    marker_page: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> ProcessResult:
    settings = settings or get_settings()
    settings.ensure_dirs()
    use_local_llm = settings.enable_local_llm if use_local_llm is None else use_local_llm

    normalized_text = normalize_ocr_text(text)
    split = split_before_marker(normalized_text, marker=settings.section_marker)
    text_before_marker = split.before_text
    marker_found = split.marker.found if marker_found is None else marker_found
    marker_text = split.marker.text if marker_text is None and split.marker.found else marker_text

    if not marker_found and not settings.extract_without_marker:
        text_before_marker = ""

    persist_text_artifacts = settings.persist_ocr_text_artifacts or settings.debug_sensitive
    text_before_path = None
    corrected_path = None
    if persist_text_artifacts:
        text_before_path = settings.ocr_corrected_dir / f"{output_stem}_before_marker.txt"
        corrected_path = settings.ocr_corrected_dir / f"{output_stem}_normalized.txt"
        write_text(corrected_path, normalized_text)
        write_text(text_before_path, text_before_marker)

    warnings = []
    if not marker_found:
        warnings.append(
            f"Không tìm thấy marker trong {settings.max_scan_pages} trang đầu; cần review."
        )
        if settings.extract_without_marker:
            warnings.append("Đã bóc tách từ các trang đã OCR vì EXTRACT_WITHOUT_MARKER=true.")

    primary = None
    if use_local_llm and text_before_marker:
        try:
            primary = LocalLLMExtractor(settings).extract(text_before_marker)
        except Exception as exc:
            primary = anchor_support_output(text_before_marker)
            primary.method = "rule_support_due_to_local_llm_error"
            primary.warnings.append(
                "Local LLM chưa sẵn sàng nên đã dùng rule support. "
                f"Chi tiết kỹ thuật: {exc}"
            )
    else:
        primary = anchor_support_output(text_before_marker)
        primary.method = "rule_support_no_local_llm"
        primary.warnings.append("Local LLM disabled or empty text; used rule support only.")

    support = anchor_support_output(text_before_marker) if text_before_marker else None
    if settings.enable_gliner and text_before_marker:
        gliner_output = GLiNERExtractor(settings).extract(text_before_marker)
        primary.entities.extend(gliner_output.entities)
        primary.warnings.extend(gliner_output.warnings)

    extraction = merge_extractor_outputs(
        source_file=source_file,
        text_before_marker=text_before_marker,
        marker_found=bool(marker_found),
        marker_text=marker_text,
        marker_page=marker_page,
        primary=primary,
        support=support,
        warnings=warnings,
    )
    extraction.corrected_text = normalized_text
    extraction.metadata.update(metadata or {})
    extraction = validate_extraction(extraction)

    include_sensitive_json = settings.persist_sensitive_json_text or settings.debug_sensitive
    extraction_json_path = settings.json_dir / f"{output_stem}.json"
    write_json(
        extraction_json_path,
        redact_sensitive_payload(model_to_dict(extraction), include_sensitive=include_sensitive_json),
    )
    excel_path = settings.excel_dir / f"{output_stem}.xlsx"
    try:
        write_excel(extraction, excel_path)
    except ModuleNotFoundError:
        excel_path = None

    return ProcessResult(
        corrected_text_path=path_to_str(corrected_path),
        text_before_marker_path=path_to_str(text_before_path),
        extraction_json=path_to_str(extraction_json_path),
        excel_path=path_to_str(excel_path),
        result=extraction,
    )


def _ocr_until_marker(
    *,
    pdf_path: Path,
    output_stem: str,
    page_count: int,
    dpi: int,
    remove_red_stamp: bool,
    max_scan_pages: int,
    stop_on_marker: bool,
    force_full_ocr: bool,
    settings: Settings,
    mock_page_texts: dict[int, str] | None,
) -> OcrDocument:
    engine = _build_ocr_engine(settings, mock_page_texts=mock_page_texts)
    return EarlyStopPipeline(settings, ocr_adapter=engine).run(
        pdf_path=pdf_path,
        output_stem=output_stem,
        page_count=page_count,
        config=EarlyStopConfig(
            dpi=dpi,
            remove_red_stamp=remove_red_stamp,
            max_pages_before_marker=max_scan_pages,
            stop_on_marker=stop_on_marker,
            force_full_ocr=force_full_ocr,
        ),
    )


def _build_ocr_engine(settings: Settings, mock_page_texts: dict[int, str] | None = None):
    if settings.use_remote_gpu_worker:
        from court_ocr_extract.remote_worker.client import FallbackOcrAdapter, RemoteOcrAdapter

        remote = RemoteOcrAdapter.from_settings(settings)
        if settings.gpu_worker_fallback:
            fallback = _build_local_ocr_engine(settings, mock_page_texts=mock_page_texts)
            fallback_name = (
                "mock"
                if settings.enable_mock_ocr or settings.gpu_worker_fallback_to_mock
                else "local"
            )
            return FallbackOcrAdapter(remote, fallback, fallback_name=fallback_name)
        return remote
    return _build_local_ocr_engine(settings, mock_page_texts=mock_page_texts)


def _build_local_ocr_engine(settings: Settings, mock_page_texts: dict[int, str] | None = None):
    from court_ocr_extract.ocr.mock_adapter import MockOcrAdapter
    from court_ocr_extract.ocr.surya_adapter import SuryaOcrEngine

    if settings.enable_mock_ocr or settings.gpu_worker_fallback_to_mock:
        return MockOcrAdapter(page_texts=mock_page_texts)
    return SuryaOcrEngine(settings.surya_language_list)


def _cache_key(**items: Any) -> str:
    serial = "|".join(f"{key}={items[key]}" for key in sorted(items))
    return sha256_text(serial)


def _write_checkpoint(settings: Settings, result: ProcessResult) -> None:
    if not result.metadata:
        return
    checkpoint = settings.checkpoint_dir / f"{result.metadata.file_id}.json"
    write_json(checkpoint, model_to_dict(result.metadata))
