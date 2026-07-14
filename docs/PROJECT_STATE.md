# Project State

## Baseline Rule Anchor + LLM Theo Từng Block

- Hướng chính cho pre-content đã chuyển từ merge `hybrid_rule_llm` sang anchor/block deterministic: `rule_anchor_only`, `llm_per_block`, `rule_then_llm_per_block`.
- `pre_content_anchor_segmenter.py` giữ metadata lines, trial-panel lines, defendant blocks, participant blocks, `line_ids`, ranh giới và lý do split; không tự quyết định chất lượng OCR.
- `rule_anchor_extractor.py` parse metadata/trial panel/entity, gắn evidence và chặn tên/field bất thường bằng validator.
- Metadata và trial panel không gọi LLM mặc định. LLM chỉ nhận từng defendant/participant block, tổng input tối đa 6000 ký tự và output tối đa 512 token; `rule_then_llm_per_block` chỉ repair field thiếu hoặc bị validator đánh dấu.
- `compare-pre-content` mặc định so sánh `rule_anchor_only,rule_then_llm_per_block`; `hybrid_rule_llm`, alias `legacy_hybrid_rule_llm` và `llm_only` vẫn còn để benchmark legacy khi truyền rõ.
- Workbook có `ANCHOR_BLOCKS` và `ANCHOR_WARNINGS`; HTML hiển thị line IDs, block, rule output, warning/validator và LLM call status.
- Codex chỉ chạy text/record synthetic và fake LLM; không đọc PDF/OCR cache thật, không gọi Surya, Docker, Local LLM hay cloud.

## Latest Local LLM Context Budget + Chunked Extraction Fix

- Default Local LLM đã chuyển sang `Qwen/Qwen2.5-3B-Instruct`, endpoint `127.0.0.1:8000/v1`, context 8192 và output 1024; Qwen2.5-7B full bf16 không dùng mặc định trên RTX 5060 Ti 16GB.
- Client chặn request vượt budget trước HTTP, luôn gửi `max_tokens`, phân loại context/connection errors và lưu request metadata.
- Pre-content được chunk theo metadata/panel/defendants/participants; chunk lỗi không xóa kết quả thành công, hybrid giữ rule output, `llm_only` không còn trả null giả.
- Compare có preflight/fail-fast policy, structured Excel sheets và HTML runtime/chunk status.
- Codex chỉ chạy mock HTTP/synthetic tests; chưa gọi vLLM/PDF/Surya/Docker/cloud thật.

## Latest OCR Marker Early Stop Fix

- Marker detector mới scan filtered lines, raw lines và canonical page text; normalize Unicode/dấu/punctuation/spacing và hỗ trợ split line/truncated marker.
- Surya pre-content path render/preprocess/OCR theo batch page, mặc định 1, với một predictor runner được tái sử dụng cho toàn PDF.
- Không có `--full-document`: dừng tại high/medium marker và trim `text_before_marker`. Có `--full-document`: OCR toàn file, không early-stop.
- Cache/debug có marker và early-stop metadata, pages total/skipped và marker highlight. Extraction ưu tiên `metadata.text_before_marker`.
- Codex chỉ chạy synthetic tests; không đọc 9 PDF/OCR cache thật và không gọi Surya/Docker/LLM.

## Surya/vLLM Windows Runtime Đã Được Project Owner Xác Nhận

- Project Owner đã chạy thành công OCR page 1 với shim `C:\court-ocr-extract\tools\docker.cmd`, vLLM backend, Docker named pipe và GPU smoke đạt `checked=true`, `ok=true`.
- Nguyên nhân khựng là cold start Surya/vLLM lần đầu; container có thể xuất hiện sau timeout 300 giây. Runtime recipe mới dùng 900 giây và giữ `surya-vllm-*` warm bằng `SURYA_INFERENCE_KEEP_ALIVE=1`.
- Safe OCR mode dùng balanced preprocess/suppression, `--stamp-erase-mode mask` và balanced post-OCR filter. Component/object erase không còn là khuyến nghị vận hành mặc định vì có thể xóa chữ thật.
- Thêm `scripts/setup_surya_windows_runtime.ps1`; script chỉ tạo shim, set env và in command, không tự chạy Docker/OCR.
- Kết quả runtime trên là xác nhận của Project Owner; Codex không chạy hoặc đọc dữ liệu thật.

## Latest Surya Runtime Preflight No-Hang Fix

- `check_surya_runtime_backend --check-gpu-container` thực thi GPU Docker smoke với command/return code/stdout/stderr tail và timeout rõ; không còn hợp lệ nếu trả `checked=false` khi có flag.
- `debug-ocr-review` và `ocr` chạy preflight nhẹ mặc định trước đường predictor; Docker path CLI được ưu tiên hơn env/PATH.
- Surya adapter ghi 8 stage vào `surya_runtime_diagnostics.json`, giới hạn startup bằng timeout và kiểm tra container khi dùng vLLM Docker resolver.
- Unit tests chỉ monkeypatch Docker/Surya; Codex không chạy PDF, Docker GPU smoke hoặc inference thật.

## Latest Final Preprocess Candidate Selection Fix

- `stamp_object_mask` hiện tạo từ union seed, hỗ trợ horizontal stamp và không chỉ giữ component lớn/mép phải.
- Thêm `object_seed_mask` và `final_preprocessed_candidate` artifacts.
- Thêm candidate scoring/selection; `final_preprocessed` là selected output và OCR input dùng cùng stage.
- Text enhancement residual amplification bị phát hiện qua stamp residual score và không được ưu tiên.
- OCR stamp filter raw/filtered/excluded vẫn giữ nguyên. Tests chỉ dùng synthetic images.


## Latest Stamp Object Erase Fix

- Đã mở rộng pixel-level stamp suppression thành component/object-level erase.
- CLI có `--stamp-erase-mode mask|component_white_fill|component_inpaint|local_background`. Ghi chú parser default `component_white_fill` là lịch sử triển khai object-erase; operational safe recipe hiện phải truyền rõ `--stamp-erase-mode mask`.
- Object candidates được lọc noise, gộp morphology, mở rộng bbox và chặn vùng giống toàn trang.
- Dark-text overlap cao sẽ chặn white-fill, ghi warning và fallback mask-level; OCR stamp filter vẫn được giữ.
- Tests chỉ dùng synthetic images; Codex chưa chạy PDF/OCR thật.


## Nhánh legacy pre-content A/B

- A/B `hybrid_rule_llm` so với `llm_only` được giữ để đối chiếu lịch sử, không còn là hướng chính hoặc default CLI.
- Baseline mới là rule anchors/block segmentation; `rule_anchor_only` là output deterministic có thể review, còn Local LLM theo block là lớp repair tùy chọn.
- Document router phân loại `judgment_criminal_first_instance`, `correction_notice`, `unknown`; correction notice không bị ép vào schema bản án và không tính trong benchmark bản án chính.
- Local LLM chỉ fill/repair field thiếu hoặc chạy LLM-only trên pre-content; tên người/địa danh không được tự sửa khi thiếu evidence.
- Đây là nhánh thử nghiệm, chưa thay đổi extraction pipeline production sau `NỘI DUNG VỤ ÁN`.
- 9 PDF có thể đặt local tại `data/test_pdfs/pre_content_9/` nhưng không commit mặc định. Codex chưa chạy hoặc đọc các PDF này.

## Latest Surya Windows Runtime + OCR Stamp Suppression

- Da them `surya_runtime.py` de resolve Docker theo `SURYA_DOCKER_BINARY`, `DOCKER_BINARY`, PATH va Docker Desktop path tren Windows.
- Da them `scripts.check_surya_runtime_backend`; GPU container chi duoc kiem khi co `--check-gpu-container`.
- Da them stamp suppression va post-OCR stamp filter theo mode `off|conservative|balanced|aggressive`; raw/filtered/excluded lines va overlap metadata duoc giu de review.
- `rel_link()` ho tro artifact o sibling stage directory nhu `preprocess/` khi tao OCR review HTML.
- Khong auto-correct ten nguoi, dia danh, hay noi dung OCR bang heuristic.
- Codex chi dung synthetic tests; chua chay PDF that, Surya inference that, Local LLM, cloud API, hay full pipeline.

Last updated: 2026-07-14

## Current Phase

RULE ANCHOR EXTRACTOR + PER-BLOCK LLM BASELINE.

Task này thay default pre-content compare bằng anchor/parser deterministic và LLM theo từng entity block. Không thay Surya OCR runtime, không chạy dữ liệu thật và không gọi model thật.

## Active Direction

The rebuild has two approved candidate paths:

1. Main candidate: PDF render -> optional preprocess -> Surya OCR -> OCR cache -> anchor/block segmentation -> deterministic metadata/trial-panel/entity parse -> optional Local LLM repair theo block -> evidence validation -> Excel -> QA report -> debug UI/human review.
2. Benchmark path: page image -> local VLM end-to-end extraction -> validation -> Excel -> QA report -> debug UI/human review.

Tesseract is legacy only. PaddleOCR is not part of the rebuild path. Cloud OCR/extraction adapters are disabled by default and may only be used for explicit opt-in benchmarks.

## Quy tắc ngôn ngữ

- Báo cáo gửi Project Owner/ChatGPT phải viết bằng tiếng Việt.
- Heading report ưu tiên tiếng Việt.
- Tên kỹ thuật như file path, class, function, CLI command, env var, model name, package name, schema field được giữ nguyên tiếng Anh.
- Không dùng report nửa Anh nửa Việt.
- Nếu prompt từ ChatGPT có heading tiếng Anh, Codex vẫn trả lời bằng template tiếng Việt trừ khi được yêu cầu khác.
- Project memory docs ưu tiên tiếng Việt trong các cập nhật mới.

## Current Repo Facts

- Surya đã có đường chạy backend ở mức code/contract, nhưng các adapter legacy chưa được hợp nhất toàn bộ và chất lượng OCR thật chưa được Project Owner xác nhận.
- VLM modules and synthetic smoke tests exist and should be treated as experimental benchmark assets.
- README, Ezycloudx docs, visual QA docs, run scripts, `.env.example`, and `settings.py` now point to the Surya target/default instead of Tesseract.
- `src/court_ocr_extract/settings.py` is canonical config for new rebuild work.
- `src/court_ocr_extract/config.py` remains a legacy compatibility module for older imports.
- `src/court_ocr_extract/excel_writer.py` là Excel writer canonical duy nhất; `excel.py` và `export/excel_writer.py` đã được xóa trong Phase 1E sau khi migrate caller.
- Extraction backend overlap đã được xử lý trong Phase 1F; validation modules, Surya adapters, và PDF/render modules vẫn có implementation chồng lấn.
- Evaluation harness chỉ đọc JSONL path được truyền rõ; report chỉ chứa aggregate numeric metrics, không chứa raw expected/predicted values.
- Existing tests are contract/control-flow oriented and use synthetic fixtures only.
- Old app folders `app/`, `app_fastapi/`, and `app_streamlit/` were removed in Phase 1D. Restore path: use Git history before the Phase 1D commit if needed.

## Safety Boundary

Codex may inspect code, config, docs, prompts, and synthetic tests/fixtures. Codex must not inspect real PDFs, real OCR text, real rendered images, real Excel outputs, real debug outputs, or real logs that may contain sensitive data.

## Latest Phase 1B Work

- Cleaned README, `.env.example`, Ezycloudx docs, visual QA docs, workflow docs, and run scripts away from Tesseract defaults.
- Changed `settings.py` default OCR backend to `surya` and enabled Surya target config by default.
- Added `surya` as a supported alias for the existing Surya OCR backend wrapper.
- Marked `config.py` as compatibility/legacy and `excel_writer.py` as canonical in docs.
- Updated cleanup plan and project memory for Phase 1B.
- Did not delete files.
- Did not implement real Surya or VLM runtime.
- Did not read real data artifacts.

## Latest Memory-Only Update

- Added project-wide Vietnamese language/reporting rule.
- Added standard Vietnamese task report template.
- Did not change pipeline code.
- Did not delete files.
- Did not run or inspect real data.

## Latest Phase 2A Work

- Triển khai routing `SuryaOCRBackend` cho backend `surya` ở mức code/contract.
- Thêm kiểm tra import/version/API Surya có hướng dẫn cài đặt khi thiếu runtime.
- Adapter hiện hỗ trợ API `surya-ocr 0.20.0` qua `RecognitionPredictor(..., full_page=True)` và báo lỗi rõ nếu API cài đặt không được hỗ trợ.
- Thêm đường render PDF thành image trước khi gọi Surya OCR backend.
- Chuẩn hóa output line của Surya vào `OCRPage.lines` với `line_id`, `text`, `bbox`, `confidence`, `reading_order`, và `warnings`.
- Thêm artifact theo từng page để review Surya OCR: ảnh gốc, bbox overlay, line JSON, page text markdown, combined text, manifest, và HTML index.
- Nâng cấp OCR review HTML để hiển thị ảnh gốc, bbox overlay, line table, warnings, và link đến artifact từng page.
- Thêm test synthetic/mocking cho `ocr_pdf_prefix()`, contract Surya, placeholder guard, no-Tesseract fallback guard, và visual review.
- `src/court_ocr_extract/ocr_backends/surya_ocr.py` không còn placeholder `runtime wiring is incomplete`.
- Không chạy PDF thật và không inspect output thật.
- Chất lượng OCR thật phải do Project Owner đánh giá trên Ezycloudx.

## Latest Full-Document Debug Fix

- `parse_page_range(None)`, `parse_page_range("")`, và `parse_page_range("all")` trả `None`, nghĩa là toàn bộ trang.
- `debug-render`, `debug-preprocess`, và `debug-red-seal` mặc định chạy toàn bộ trang khi không truyền `--pages`.
- `debug-ocr-review` và `ocr` có `--full-document` để truyền `max_pages=None`, `stop_marker=""`.
- Surya OCR không còn dừng/truncate tại marker `NỘI DUNG VỤ ÁN` khi `stop_marker=""`.
- Thêm test synthetic cho page range, CLI full-document, và Surya full-document behavior.
- Không chạy PDF thật, không đọc dữ liệu thật, không chạy extraction/LLM/Excel.

## Latest Repo Cleanup

- Dọn generated cache local như `__pycache__/` và `.pytest_cache/` trong workspace.
- Không xóa tracked source/docs legacy vì `docs/CLEANUP_PLAN.md` vẫn phân loại chúng là `legacy_optional`, `duplicate_conflict`, `experimental`, hoặc `unknown_need_review`.
- Không inspect hoặc dọn `data/`, `outputs/`, `logs/`, `work/`, model files, PDF thật, Excel thật, image thật.
- `ruff` không chạy được vì chưa được cài trong `.venv`.

## Latest Phase 1C Work

- Thêm `scripts/repo_inventory.py` để tạo inventory an toàn, bỏ qua protected real-data/output roots.
- Thêm `scripts/import_graph.py` để dựng import graph bằng `ast` cho `src/`, `scripts/`, và `tests/`.
- Thêm `scripts/check_architecture_guardrails.py` để kiểm Surya/main defaults, cloud disabled defaults, protected path policy, CLI full-document behavior, và duplicate/legacy warnings.
- Thêm test synthetic/contract cho các script architecture audit mới.
- Thêm docs Phase 1C: `REPO_INVENTORY`, `IMPORT_GRAPH`, `LEGACY_ARCHIVE_PLAN`, `PRODUCTION_TOOLKIT`, `EVALUATION_PLAN`, `GOLD_DATASET_GUIDE`, `PRIVACY_REDACTION_PLAN`, `OBSERVABILITY_PLAN`, và `MLOPS_PLAN`.
- Cập nhật `AGENTS.md`, `AGENT_ROLES.md`, `TESTING.md`, `CLEANUP_PLAN.md`, `DECISIONS.md`, `TASKS.md`, `CHANGELOG_AI.md`, và `CODEX_HANDOFF.md`.
- Không xóa file, không chạy dữ liệu thật, không inspect protected artifacts, không push.

## Latest Phase 1D Work

- Audited old app references with `scripts.import_graph`, `scripts.repo_inventory`, and `git grep`.
- Confirmed `src/court_ocr_extract` and CLI main path do not import `app/`, `app_fastapi/`, or `app_streamlit/`.
- Removed old app folders: `app/`, `app_fastapi/`, and `app_streamlit/`.
- Removed stale old app artifacts: `docs/streamlit_vs_fastapi.md`, `scripts/ezycloudx_run_api.sh`, `scripts/ezycloudx_run_api_windows.ps1`, and `templates/upload.html`.
- Removed old UI-only optional dependencies `streamlit` and `jinja2`; kept `fastapi`, `uvicorn`, and `python-multipart` for supported remote worker tooling.
- Updated architecture guardrails to fail if README/docs/scripts reintroduce old app run instructions.
- Did not touch Surya OCR backend, Local LLM extractor, Excel writer, VLM benchmark modules, or protected real-data paths.

## Latest Phase 1E Work

- Hợp nhất `rows_from_result()` và `write_excel_from_results()` vào canonical `src/court_ocr_extract/excel_writer.py`.
- Chuyển pipeline, evaluation script, và tests khỏi `court_ocr_extract.excel`/`court_ocr_extract.export.excel_writer` sang canonical module.
- Xóa `src/court_ocr_extract/excel.py` và `src/court_ocr_extract/export/excel_writer.py`; restore bằng Git history trước Phase 1E nếu cần.
- Giữ nguyên 11 domain headers và hai workbook contract hiện hữu: draft records dùng `DATA` + `RUN_SUMMARY`, typed `ExtractionResult` dùng `Trich xuat`.
- Thêm synthetic workbook contract tests và architecture guardrail cho canonical path/legacy imports.
- Các cột audit/trace mục tiêu chưa được thêm trong phase này; cần một phase schema riêng nếu Project Owner duyệt.
- Không chạy PDF thật, không đọc Excel thật, không gọi cloud API, và không push.

## Latest Phase 1F Work

- Chọn `src/court_ocr_extract/extraction_pipeline.py` làm canonical orchestrator và `src/court_ocr_extract/extractors/` làm canonical backend package.
- Hợp nhất Local LLM backend/typed adapter vào `extractors/local_llm_extractor.py`; hợp nhất rule backend/typed anchor vào `extractors/rule_support.py`.
- Chuyển rule parser vào `extractors/rule_parser.py` và migrate pipeline, remote worker, scripts, tests sang canonical imports.
- Xóa `extraction/base.py`, `extraction/local_llm_extractor.py`, `extraction/rule_support.py`, root `extractor.py`, và root `llm.py`; restore bằng Git history trước Phase 1F nếu cần.
- Giữ `extraction/merge.py`, `schemas.py`, `validators.py`, và `gliner_extractor.py` vì có trách nhiệm typed merge/schema/validation/experimental riêng.
- `scripts.check_extractor` mặc định chạy static configuration check, không gọi endpoint.
- Thêm synthetic extraction contract tests với fake response; không network/model thật.

## Latest TOOLKIT-1 Work

- Thêm `src/court_ocr_extract/evaluation/` gồm manifest validation, privacy/hash/redaction, metrics và safe report.
- Thêm gold/prediction JSONL synthetic fixtures trong `tests/fixtures/`; gold thật vẫn nằm ngoài Git/Codex.
- Thêm `scripts.check_gold_manifest` và `scripts.evaluate_gold_manifest`; không có default path vào `data/` hoặc `outputs/`.
- Implement OCR, field, participant, evidence, source reference, review và warning aggregate metrics.
- Guardrail bảo vệ `data_private/`, `data/gold/`, manifest ngoài tests và obvious PII trong synthetic manifests.
- Synthetic evaluation không chứng minh chất lượng OCR/extraction thật và không thay human review.

## Latest Preprocess Safety Fix

- `debug-preprocess` có `--deskew off|safe|force`, `--red-seal-removal on|off` và `--preprocess-profile conservative|balanced|aggressive`.
- Default an toàn là `deskew=off`, red-seal removal bật và profile conservative.
- HSV red mask/removal chạy trên original color trước grayscale; ratio quá cao sẽ skip thay vì xóa mạo hiểm.
- Safe deskew cần đủ horizontal evidence, góc 0.3-5 độ, không có foreground sát mép và không có layout hai cột mơ hồ.
- Blank guard so foreground/dark ratio/brightness/entropy và fallback original hoặc `seal_removed` khi after mất nội dung.
- Debug review hiển thị original, red mask, seal removed, final, compare, metadata và warnings theo page.
- Tests chỉ dùng ảnh synthetic; chất lượng và ngưỡng trên scan thật chưa được xác nhận.

## Latest Red Seal + Text Enhancement Fix

- Red detector kết hợp HSV + Lab + RGB, morphology cleanup, component count và residual estimate.
- Thêm `neutralize`, `inpaint`, `white_fill`; default `neutralize`, còn `inpaint` có residual second pass.
- Thêm `black_text_protection_mask`, overlap ratio và warning `red_mask_overlaps_dark_text`.
- Thêm `text_enhance=off|light|medium|strong`; default `light`, chạy sau red removal.
- Text guard phát hiện foreground loss/dark-pixel explosion/entropy collapse và fallback stage an toàn.
- Debug per-page có red mask, protection mask, seal removed, text enhanced, final và metadata đầy đủ.
- Deskew logic/default giữ nguyên; tests chỉ dùng synthetic images.

## Latest OCR Uses Preprocessed Input

- Trước task này, Surya luôn nhận rendered original; `debug-preprocess` là nhánh review độc lập.
- `debug-ocr-review` và `ocr` có `--use-preprocessed` cùng toàn bộ preprocess options.
- Khi opt-in, backend truyền final preprocessed path vào Surya và lưu preprocess + OCR input artifacts cạnh nhau.
- `OCRResult.metadata`, OCR cache và Surya manifest ghi `ocr_input_source` cùng Mode 3 options.
- Không có flag thì behavior cũ và `ocr_input_source=rendered_original` được giữ nguyên.
- Preprocess exception tạo named final safe copy và warning, không âm thầm gọi OCR bằng rendered path.
- Tests dùng fake Surya; chưa có real PDF/OCR inference trong Codex.

## Latest Surya Version Pin

- `pyproject.toml` và `requirements.txt` pin exact `surya-ocr==0.20.0`.
- Main adapter chưa hỗ trợ Surya 2 / `surya-ocr>=0.21.0`.
- Version guard đọc distribution metadata trước `import surya`, API detection hoặc runtime call.
- `check_ocr_backend` in installed/supported version; local `.venv` hiện pass với 0.20.0.
- Sai version/missing package trả reinstall commands rõ; không chờ tới Docker/vLLM error.
- Tests mock version/import và không gọi inference.

## Next Gate

Project Owner chạy `compare-pre-content` với 1 case bằng `rule_anchor_only,rule_then_llm_per_block`, review `ANCHOR_BLOCKS`, `ANCHOR_WARNINGS`, structured sheets và HTML; chỉ tăng lên 3 case sau khi case đầu đạt.
