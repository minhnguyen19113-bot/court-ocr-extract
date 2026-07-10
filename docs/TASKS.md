# Tasks

Last updated: 2026-07-10

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

## Phase 1C

- [x] Tạo safe repo inventory script và doc.
- [x] Tạo Python import graph script và doc.
- [x] Tạo architecture guardrail script.
- [x] Thêm tests cho architecture audit scripts.
- [x] Tạo legacy archive/repo slimming plan không xóa file.
- [x] Tạo production toolkit blueprint.
- [x] Tạo evaluation plan và gold dataset guide.
- [x] Tạo privacy redaction, observability, và MLOps plans.
- [x] Cập nhật `AGENTS.md`, `AGENT_ROLES.md`, `TESTING.md`, memory docs, và cleanup plan.
- [x] Không chạy PDF thật, không đọc dữ liệu thật, không xóa file, không push khi chưa được yêu cầu.

## Phase 1D

- [x] Audit `app/`, `app_fastapi/`, `app_streamlit/`.
- [x] Chạy `scripts.import_graph` và `scripts.repo_inventory` trước cleanup.
- [x] Tìm references bằng `git grep` trong README/docs/scripts/tests/src/pyproject.
- [x] Xác nhận không có import từ main `src/`/CLI path vào old app folders.
- [x] Xóa `app/`, `app_fastapi/`, `app_streamlit/`.
- [x] Xóa stale old app artifacts: `docs/streamlit_vs_fastapi.md`, `scripts/ezycloudx_run_api.sh`, `scripts/ezycloudx_run_api_windows.ps1`, `templates/upload.html`.
- [x] Gỡ `streamlit` và `jinja2` khỏi optional `web` dependencies.
- [x] Cập nhật architecture guardrail để bắt old app run instructions quay lại.
- [x] Không tạo `legacy/`, `archive/`, `old/`, hoặc `deprecated/` folder mới.
- [x] Không chạy PDF thật, không đọc dữ liệu thật, không sửa Surya OCR backend, Local LLM extractor, Excel writer, hoặc VLM benchmark modules.

## Phase 1E

- [x] Audit mọi file/reference Excel/export trong safe roots.
- [x] Xác nhận `src/court_ocr_extract/excel_writer.py` là canonical writer.
- [x] Migrate typed `ExtractionResult` mapping/writing vào canonical writer.
- [x] Chuyển pipeline, evaluation script, và tests sang canonical import.
- [x] Xóa `src/court_ocr_extract/excel.py` và `src/court_ocr_extract/export/excel_writer.py` sau khi không còn caller.
- [x] Thêm synthetic `.xlsx` contract tests bằng `tmp_path` + `openpyxl`.
- [x] Thêm architecture guardrail cho canonical writer và legacy import.
- [x] Cập nhật inventory/import graph/memory/schema/testing docs.
- [x] Không chạy PDF thật, không đọc dữ liệu thật, không gọi cloud API, không push.

## Phase 1F

- [x] Audit extraction/extractor/rule/schema modules và mọi caller trong safe roots.
- [x] Xác nhận `extraction_pipeline.py` là canonical orchestrator và `extractors/` là canonical backend package.
- [x] Hợp nhất Local LLM typed compatibility behavior vào canonical `extractors/local_llm_extractor.py`.
- [x] Hợp nhất rule support và chuyển rule parser vào canonical `extractors/` package.
- [x] Migrate pipeline, remote worker, scripts, và tests khỏi legacy imports.
- [x] Xóa 5 duplicate/unimported extraction paths; không tạo compatibility wrapper.
- [x] Giữ merge/schema/validation/GLiNER và direct vision/cloud benchmark paths đúng vai trò.
- [x] Thêm synthetic no-network contract tests và static `check_extractor` mode.
- [x] Cập nhật architecture guardrail, inventory/import graph, docs và memory.
- [x] Không chạy PDF/dữ liệu/model endpoint thật, không gọi cloud API, không push.

## Phase 2 / Phase 3 Candidates

Do not start without Project Owner / ChatGPT approval.

- Consolidate Surya OCR adapter path.
- Define and implement real Surya OCR cache contract.
- Expand debug UI around bbox/evidence/QA links.
- Phase 3A Local LLM strict JSON/evidence hardening.
- Bổ sung audit/trace columns vào Excel trong một phase schema riêng nếu được duyệt.

## TOOLKIT-1

- [x] Tạo gold/prediction JSONL manifest validators.
- [x] Tạo synthetic redacted fixtures; không tạo gold thật.
- [x] Implement OCR/field/participant/evidence/review aggregate metrics.
- [x] Tạo safe JSON/Markdown report chỉ chứa numeric metrics.
- [x] Tạo PII hash/detection/redaction helper nhẹ.
- [x] Tạo `check_gold_manifest` và `evaluate_gold_manifest` không có real-data default.
- [x] Thêm guardrail cho `data_private/`, `data/gold/`, manifest ngoài tests và fixture PII.
- [x] Thêm synthetic manifest/metrics/report/script tests.
- [x] Cập nhật evaluation/privacy/observability/MLOps/toolkit memory docs.
- [x] Không chạy PDF/OCR/Excel/model/cloud thật, không stage/commit/push.

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

## Repo Cleanup

- [x] Audit generated cache trong các root code/docs/tests/app an toàn.
- [x] Xóa local cache generated (`__pycache__/`, `.pytest_cache/`) khỏi workspace.
- [x] Xác nhận không có cache Python tracked trong Git.
- [x] Không xóa tracked legacy/duplicate code khi chưa có canonical owner decision.
- [x] Không inspect hoặc dọn real-data/protected artifact folders.

## Backlog

- Local Qwen runtime hardening with strict JSON, retries, and evidence coverage.
- VLM benchmark harness with comparable QA output.
- Gold dataset workflow outside Codex for real quality assessment.
- Ezycloudx runtime checks for GPU, Surya, vLLM/Ollama, and transfer server.
- Cleanup/archive slice theo `docs/LEGACY_ARCHIVE_PLAN.md` sau khi reviewer duyệt.
