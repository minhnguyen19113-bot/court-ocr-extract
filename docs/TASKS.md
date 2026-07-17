# Tasks

## FINAL EXCEL SCHEMA FIRST REALIGNMENT

- [x] Audit toàn repo và xác nhận không có bộ final columns cạnh tranh với 11 cột được duyệt.
- [x] Tạo `final_excel_schema.py` và `final_excel_builder.py`.
- [x] Bổ sung extraction cho ngày thụ lý, quan hệ pháp luật explicit và CCCD/CMND có label.
- [x] Đổi mọi final workbook writer sang sheet đầu `FINAL_EXCEL` đúng 11 cột.
- [x] Nối final builder vào `rule_anchor_only` và `rule_then_llm_per_block`; debug sheets vẫn nằm phía sau.
- [x] Đặt `FINAL EXCEL PREVIEW` 11 cột trước mọi debug section trong HTML review.
- [x] Thêm năm test modules bắt buộc và cập nhật writer contract cũ.
- [x] Chạy full suite: 199/199 test passed; các static/architecture/repo checks đều passed.
- [ ] Project Owner chạy rule-only trên `case_001`, review 10 dòng người và xác nhận mapping thật.

## FIX RULE ANCHOR METADATA + PARTICIPANT SPLITTER CASE001

- [x] Bỏ metadata line cap gây mất anchor phía cuối header và chỉ capture token số thụ lý/quyết định.
- [x] Split juror chứa newline thành các dòng `TRIAL_PANEL` riêng.
- [x] Sửa participant splitter cho numbering `7.x.`, inline role/person, longest-role-first và address/detail theo block gần nhất.
- [x] Sửa participant name, presence và relationship/note cho guardian/lawyer lines.
- [x] Sửa `tam giam`, `Vợ con`, address continuation và prefix `hiện tại:` trong defendant parser.
- [x] Phân loại `standalone_page_number_removed_from_defendant_blocks` là informational nhưng vẫn export `ANCHOR_WARNINGS`.
- [x] Thêm năm regression test modules synthetic; 23/23 test rule-anchor liên quan đã qua.
- [ ] Project Owner chạy lại `case_001` theo thứ tự rule-only rồi rule + LLM và xác nhận workbook/HTML thật.

## RULE ANCHOR EXTRACTOR + PER-BLOCK LLM BASELINE

- [x] Thêm `rule_anchor_only`, `llm_per_block`, `rule_then_llm_per_block`; giữ strategy legacy để compare khi gọi rõ.
- [x] Thêm anchor segmenter cho metadata, trial panel, defendant và participant blocks với line IDs/split reasons.
- [x] Thêm deterministic metadata/trial-panel/defendant/participant parsers và validators.
- [x] Sửa document router nhận bản án thiếu/mất OCR judgment number và ưu tiên correction notice.
- [x] Giới hạn Local LLM theo từng block ở 6000 ký tự/512 output token; không gửi full pre-content.
- [x] Tổng quát hóa compare runner, thêm `ANCHOR_BLOCKS`, `ANCHOR_WARNINGS` và HTML anchor review.
- [x] Có 11 test modules, 23 tình huống rule-anchor contract/fake LLM; không có real-data/model call.
- [ ] Project Owner chạy 1 case trên VM, review anchor/validator/structured output rồi mới chạy 3 case.

## LOCAL LLM CONTEXT BUDGET + CHUNKED EXTRACTION FIX

- [x] Chuyển default VM sang Qwen2.5-3B, context 8192 và output 1024.
- [x] Thêm token estimator, input char/token cap, safety margin, trim và fail rõ theo error type.
- [x] Bắt buộc `max_tokens` trong OpenAI-compatible payload.
- [x] Thêm chunk metadata/panel/defendants/participants, partial merge và de-duplicate.
- [x] Thêm `/models` + chat preflight, CLI require/allow/skip policy và không tạo null giả.
- [x] Thêm structured Excel, HTML runtime status và mock/synthetic tests.
- [ ] Project Owner chạy `scripts.check_llm_backend`, sau đó compare 1 case trên VM và review chunk errors/output.

## OCR MARKER EARLY STOP FIX

- [x] Thêm shared marker detector cho raw/filtered/page text và noisy Unicode/spacing.
- [x] Refactor Surya thành page loop mặc định batch 1, giữ một predictor runner warm.
- [x] Dừng sau marker page; `--full-document` vẫn OCR toàn file.
- [x] Ghi marker/early-stop/pages/text-before-marker metadata vào cache/debug.
- [x] Cho extraction ưu tiên `text_before_marker`.
- [x] Thêm synthetic tests cho detector, stop/full override, cache, extraction và HTML.
- [ ] Project Owner chạy lại 1 PDF rồi 9 PDF trên VM và xác nhận tổng pages giảm.

## SURYA/VLLM WINDOWS RUNTIME RECIPE

- [x] Project Owner xác nhận GPU container smoke `checked=true`, `ok=true`.
- [x] Project Owner xác nhận OCR page 1 với Docker shim không khoảng trắng và timeout 900 giây.
- [x] Ghi env vLLM keep-alive, Docker named pipe, firewall và warm-container guidance vào runbook/memory.
- [x] Chốt safe OCR operational mode dùng `--stamp-erase-mode mask`.
- [x] Thêm setup helper tạo shim, set env và in command; không tự chạy runtime.
- [ ] Project Owner tiếp tục human review chất lượng OCR và giữ container warm trong cùng VM session.

## SURYA RUNTIME PREFLIGHT + NO-HANG FIX

- [x] Chuẩn hóa GPU container smoke output và timeout.
- [x] Dùng resolver cho CLI option, env, PATH và Windows Docker Desktop.
- [x] Gắn preflight mặc định vào `debug-ocr-review` và `ocr` trước predictor.
- [x] Thêm startup timeout, container spawn check và 8-stage diagnostics.
- [x] Thêm synthetic tests cho checked true/false, success/failure/timeout và fail-fast.
- [x] Project Owner đã chạy hai runtime checks và OCR page 1 trên VM.

## FINAL PREPROCESS CANDIDATE SELECTION FIX

- [x] Tạo `object_seed_mask` từ union red/stroke masks.
- [x] Sửa horizontal grouping và giữ đồng thời side seal + horizontal stamp.
- [x] Thêm candidate metrics, safety checks và final selection.
- [x] Ghi selected stage/reason/scores vào metadata và debug UI.
- [x] Dùng final selected candidate làm OCR input.
- [x] Thêm synthetic tests cho horizontal stamp, side seal, amplification và blank rejection.
- [ ] Project Owner visual review page 1 preprocess và OCR trên VM.


## STAMP OBJECT ERASE FIX

- [x] Thêm `stamp_object_mask` từ connected components và expanded object regions.
- [x] Thêm bốn `stamp_erase_mode`; operational safe recipe mới luôn truyền rõ `mask`, không dùng parser default object erase.
- [x] Thêm dark-text overlap guard, fallback và warnings.
- [x] Nối artifacts/metadata vào debug-preprocess và Surya OCR path.
- [x] Giữ post-OCR raw/filtered/excluded stamp lines.
- [x] Thêm synthetic tests cho residual, low saturation, overlap, blank và noise.
- [ ] Project Owner visual review balanced/inpaint và aggressive/white-fill trên VM.


## PRE-CONTENT EXTRACTION A/B TEST

- [x] Thêm document router và pre-content segmenter trên filtered OCR lines.
- [x] Thêm schema chung và rule-based intermediate extractor.
- [x] Thêm `hybrid_rule_llm` với bảo vệ rule field và conflict review.
- [x] Thêm `llm_only` với prompt giới hạn pre-content và JSON repair.
- [x] Thêm `compare-pre-content` cùng JSON, Excel, HTML artifacts.
- [x] Thêm synthetic tests cho segmenter, rule, hybrid và compare.
- [x] Reviewer quyết định không dùng hai strategy này làm hướng chính; giữ làm legacy comparison.

## SURYA WINDOWS RUNTIME + OCR STAMP SUPPRESSION V3

- [x] Codify Windows Docker resolver va runtime diagnostics.
- [x] Them stamp suppression mask/output va bao ve dark text.
- [x] Them post-OCR filter, raw/filtered/excluded line artifacts va metadata.
- [x] Sua artifact link cho sibling stage directory.
- [x] Them synthetic tests cho resolver, suppression, filter va preprocessed OCR path.
- [x] Khong auto-correct ten nguoi/dia danh/noi dung bang heuristic.
- [ ] Project Owner review balanced/aggressive tren Ezycloudx voi PDF that.

Last updated: 2026-07-14

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

## Preprocess Safety Fix

- [x] Thay auto-deskew `minAreaRect` mạo hiểm bằng default `off` và mode `safe` có confidence/range/layout/crop guard.
- [x] Chạy HSV red mask/removal trên ảnh màu trước grayscale, tạo mask và metadata.
- [x] Thêm foreground/dark/brightness/entropy blank guard và safe fallback.
- [x] Thêm CLI options cho deskew, red-seal removal và preprocess profile.
- [x] Nâng debug HTML để hiển thị original/red mask/seal removed/final/metadata/warnings.
- [x] Thêm synthetic tests cho seal/no-seal, color-order, deskew, blank fallback và debug review.
- [x] Không chạy PDF/OCR/Surya/model/cloud/full pipeline thật.
- [ ] Project Owner chạy lại `debug-preprocess --deskew off` trên Ezycloudx và duyệt toàn bộ trang.
- [ ] Chỉ thử `--deskew safe` sau khi preview mặc định được chấp nhận.

## Red Seal + Text Enhancement Fix

- [x] Kết hợp HSV/Lab/RGB red mask, morphology và component metadata.
- [x] Thêm `neutralize|inpaint|white_fill` cùng residual/removed metrics.
- [x] Thêm black-text protection mask và overlap warning.
- [x] Thêm `text-enhance off|light|medium|strong` và default `light`.
- [x] Thêm red-removal/text-enhancement guard và staged fallback.
- [x] Nâng debug artifacts/HTML và synthetic test matrix.
- [x] Giữ nguyên deskew; không chạy PDF/OCR/model/cloud/full pipeline thật.
- [ ] Project Owner so sánh ba cấu hình preprocess v2 trên Ezycloudx trước OCR.

## OCR Uses Preprocessed Input

- [x] Audit xác nhận OCR cũ chỉ dùng rendered original.
- [x] Thêm `--use-preprocessed` và preprocess options cho `debug-ocr-review`/`ocr`.
- [x] Truyền final preprocessed path vào Surya khi opt-in; giữ behavior cũ khi không bật.
- [x] Ghi source/options vào OCR result, cache, page artifacts và manifest.
- [x] Giữ preprocess artifacts và tạo `page_NNN_ocr_input.png`.
- [x] Thêm safe-copy warning khi preprocess exception.
- [x] Thêm fake-backend tests; không chạy PDF/Surya/LLM/cloud/full pipeline thật.
- [ ] Project Owner chạy visual OCR review Mode 3 trên Ezycloudx.

## Pin Surya OCR Version

- [x] Pin `surya-ocr==0.20.0` trong project extra và requirements.
- [x] Chặn mọi installed version khác trước import/API/runtime.
- [x] Báo rõ installed/supported version và reinstall commands.
- [x] Nâng `check_ocr_backend` để in version mà không inference.
- [x] Thêm tests cho 0.20.0, 0.21.1, missing package và no-inference.
- [x] Ghi Surya 2/Docker thành phase riêng, không hỗ trợ trong main path hiện tại.
- [ ] Project Owner reinstall pinned extras trên VM rồi chạy lại check.

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
