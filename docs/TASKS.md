# Tasks

Last updated: 2026-07-07

## Phase 1A

- [x] Record project reorientation in repo memory.
- [x] Define Codex memory protocol.
- [x] Define agent role system.
- [x] Classify current repo files/folders for cleanup planning without deletion.
- [x] Add lightweight project snapshot script.
- [x] Add lightweight repo guardrail script.
- [x] Add focused tests for new scripts.
- [x] Reviewer approval for Phase 1B.

## Phase 1B

- [x] Clean docs and runbooks so Tesseract is no longer presented as default.
- [x] Clean `.env.example` so Surya is the target OCR default and cloud remains disabled.
- [x] Choose `src/court_ocr_extract/settings.py` as canonical config.
- [x] Mark `src/court_ocr_extract/config.py` as compatibility/legacy.
- [x] Choose `src/court_ocr_extract/excel_writer.py` as canonical Excel writer.
- [x] Update run scripts default backend to Surya target.
- [x] Keep legacy files in place; no deletion or mass move.

## Phase 1C / Phase 2 Candidates

Do not start without Project Owner / ChatGPT approval.

- Archive or move legacy app folders and legacy backends.
- Consolidate Surya OCR adapter path.
- Define and implement real Surya OCR cache contract.
- Expand debug UI around bbox/evidence/QA links.
- Choose canonical extraction package/API.
- Consolidate duplicate Excel/export wrappers.

## Memory/Reporting Rules

- [x] Add project-wide Vietnamese reporting rule.
- [x] Add standard Vietnamese task report template.
- [x] Record that technical identifiers remain in English when they are standard names.
- [x] Confirm no pipeline code change, no deletion, and no real-data run for this memory-only update.

## Phase 2A

- [x] Triển khai đường chạy Surya OCR backend ở mức code/contract.
- [x] Giữ backend name `surya` làm main path và `surya_optional` làm compatibility alias.
- [x] Thêm kiểm tra Surya availability/API có hướng dẫn cài đặt.
- [x] Hỗ trợ API `surya-ocr 0.20.0` bằng `RecognitionPredictor(..., full_page=True)`.
- [x] Đảm bảo `ocr_pdf_prefix()` không còn placeholder `RuntimeError`.
- [x] Chuẩn hóa output mocked/Surya OCR vào `OCRPage.lines`.
- [x] Sắp xếp combined text theo `reading_order` nếu Surya trả về field này.
- [x] Thêm artifact bbox overlay.
- [x] Thêm artifact OCR theo page và link trong review HTML.
- [x] Thêm test synthetic/mocking cho `ocr_pdf_prefix()`, Surya OCR contract, no-placeholder guard, no-Tesseract fallback guard, và visual review.
- [x] Giữ Tesseract là legacy only; không fallback sang Tesseract.
- [x] Không chạy PDF thật hoặc inspect output thật.

## Phase 2B Candidates

Do not start without Project Owner / ChatGPT approval.

- [x] Sửa default `--pages` để debug render/preprocess/red-seal chạy toàn bộ trang khi không truyền page range.
- [x] Thêm `--full-document` và `--max-pages` cho `debug-ocr-review` và `ocr`.
- [x] Đảm bảo `debug-ocr-review --full-document` và `ocr --full-document` truyền `max_pages=None`, `stop_marker=""`.
- [x] Đảm bảo Surya OCR không break/truncate tại marker khi `stop_marker=""`.
- [x] Thêm test synthetic cho page range, CLI full-document, và Surya full-document marker behavior.
- Chạy/check Surya package và model behavior trên Ezycloudx.
- Pin hoặc document version `surya-ocr` tương thích nếu cần.
- Thêm command riêng `ocr-surya-review` nếu reviewer muốn command hẹp hơn `debug-ocr-review`.
- Cải thiện review UI sau khi thấy behavior thật của Surya bbox/text.
- Chỉ bắt đầu hardening Local LLM strict JSON/evidence sau khi OCR review path được duyệt.

## Backlog

- Local Qwen runtime hardening with strict JSON, retries, and evidence coverage.
- VLM benchmark harness with comparable QA output.
- Gold dataset workflow outside Codex for real quality assessment.
- Ezycloudx runtime checks for GPU, Surya, vLLM/Ollama, and transfer server.
