# AI Changelog

## 2026-07-21 - Pilot 10 Sentence Audit Final Hardening

- Mở rộng probation-start parser cho `sơ thảm/sơ thẳm`, parenthesized/bare/textual date trong bounded clause; không sửa raw OCR hoặc dùng metadata fallback.
- Thay probation partial heuristic bằng kiểm tra capture + phần dư, loại warning sai cho year-only/month-only/year-month duration hoàn chỉnh.
- Tách sentence evidence thành tám loại, thu hẹp span và thêm custody/UBND/section/numbered-item boundaries mà không chặn additional item hợp lệ phía sau.
- Thêm structured warning records có severity/scope/entity/source evidence; workbook warning/evidence sheets xuất đầy đủ audit columns.
- Thay validator-note substring matching bằng field-level whitelist; procedural rejection không còn lan note hoặc review state tới mọi đương sự.
- Thêm cross-source name audit với similarity và explicit disagreement warning; front name/FINAL_EXCEL name không bị thay đổi.
- Targeted `30 passed`, sentence regression `84 passed`, regression group `150 passed`, full suite `394 passed`, `0 failed`, không thêm skip/xfail.
- Không đọc/chạy dữ liệu thật, không gọi OCR/Docker/Surya inference/LLM/cloud và không commit/push.

## 2026-07-21 - Pilot 10 Sentence Completeness and Evidence Hardening

- Mở rộng deterministic sentence parser cho textual date, OCR `bất giam/bắt giảm`, probation nhiều đơn vị và structured `probation_start_text`.
- Canonicalize time-served completion, OCR `hình phát tù` và detention-credit date range; không tính số ngày hay suy completion khi thiếu explicit evidence.
- Thêm bounded follow-on scanner cho numbered additional-penalty item, OCR `hình phát/phát bổ sung`, defendant-specific mapping và civil/court-fee exclusions.
- Làm nhất quán sentence evidence theo line, giữ release/additional lines và trim trước các section không liên quan.
- Thêm bảy completeness warnings, case review flag và final-row note cho warning quan trọng; không phát warning sentence cho victim.
- Thêm đủ 20 test modules synthetic; targeted `61 passed`, regression `94 passed`, full suite `367 passed`, `0 failed`, không thêm skip/xfail.
- Không đọc/chạy dữ liệu thật, không gọi OCR/Docker/Surya inference/LLM/cloud và không commit/push.

## 2026-07-21 - Defendant Sentence Column + Final Address Hardening

- Nâng canonical `FINAL_EXCEL` lên 14 cột và thêm `HÌNH PHẠT` đúng vị trí.
- Thêm `sentence_parser.py` deterministic, tái sử dụng verdict scanner/name matcher, hỗ trợ primary sentence, duration, án treo/thử thách, execution details, aggregate và additional penalties.
- Map sentence theo defendant entity ID; victim blank, same-person/different-role độc lập và defendant thiếu evidence có note riêng.
- Wire sentence output vào cache-only compare flow, source audit và ba workbook sheets mới.
- Tách permanent/current address, thêm `Nơi ở` priority, presence-line boundary và punctuation-aware presence suffix cleanup.
- Thêm synthetic tests bắt buộc; không đọc dữ liệu thật, không gọi OCR/Docker/Surya inference/LLM/cloud và không commit/push.
- Verification: address `29 passed`; sentence/schema/final `47 passed`; regression cuối `148 passed`; full suite `342 passed`, `0 failed`, không có skip/xfail mới.

## 2026-07-17 - Fast Patch Final Excel 13 Cột, Verdict Block và Địa Chỉ Qua Trang

- Nâng canonical `FINAL_EXCEL` lên đúng 13 cột, thêm số/ngày tuyên án và khóa mapping độc lập với số/ngày thụ lý.
- Thu hẹp final role về `Bị cáo`/`Bị hại`; giữ participant khác trong JSON/`PARTICIPANTS` và chuyển sheet/HTML phụ sang opt-in mặc định off.
- Thay charge window ngắn bằng verdict block có line/char guard, hỗ trợ punishment phrase, quoted/unquoted charge, nhiều dòng và qua page break.
- Thêm decision-tail diagnostics cùng candidate raw blocks/evidence/warnings vào workbook, JSON và HTML review.
- Nối current address qua page break theo line sequence, bỏ số trang độc lập và dừng trước identity/entity tiếp theo.
- Thêm đúng 9 test modules synthetic theo task: targeted 10/10 passed; focused address regression 11/11 passed. Full suite 240/252 passed, còn 12 assertion legacy mâu thuẫn trực tiếp với schema/role/output default mới và không được sửa vì task khóa danh sách test.
- Không dùng dữ liệu thật, OCR, Surya, Docker, LLM hoặc cloud; không commit/push.

## 2026-07-17 - Front + Decision Source và Row-specific Legal Relationship

- Thêm `source_region_policy.py`; production chỉ chấp nhận `front_pre_content` và `decision_tail`, loại `middle_excluded` khỏi final field/fallback.
- Chuẩn hóa charge result thành `case_charges`, entity-ID keyed `defendant_charge_map`, `charge_evidence`, `warnings`; hỗ trợ explicit quoted/unquoted verdict và ambiguity-safe matching.
- Đổi final legal relationship sang row-specific: defendant chỉ nhận specific charges, primary role khác nhận case charges; thiếu/ambiguous để trống có ghi chú, không fallback `Hình sự`.
- Siết reverse decision scan bắt buộc giới hạn dương/hữu hạn và status `heading_not_found`; không tự OCR toàn văn bản.
- Thêm workbook sheets `CHARGES`, `DEFENDANT_CHARGES`, `SOURCE_REGION_AUDIT`, `CHARGE_WARNINGS` cùng HTML charge/source review đúng thứ tự.
- Thêm 11 test modules bắt buộc và cập nhật regression cũ. Full suite 242/242 passed với synthetic fixtures; không đọc/chạy dữ liệu thật, không gọi OCR/LLM/Docker/cloud, không commit/push.

## 2026-07-17 - Final Excel Role, Boundary và Decision Charge

- Sửa pre-content marker boundary để giữ mọi line trước heading, kể cả phần trước marker trên trang vượt fallback limit.
- Cô lập defendant region bằng intro/strong identity evidence, chặn trial-panel leakage và xuất rejected candidates/reasons.
- Sửa multi-anchor metadata cùng dòng, acceptance number/date binding và warning khi thiếu number token.
- Thêm `final_excel_role_policy.py` cùng sheet `NGUOI_THAM_GIA_KHAC`; final row dedupe theo case + normalized name + normalized role.
- Split support-role block nhiều person có kiểm soát; giữ represented person, shared note và evidence line IDs.
- Xóa fallback `QUAN HỆ PHÁP LUẬT = Hình sự`; thêm explicit decision charge parser, reverse-scan tail cache và command Surya-only `ocr-decision-tail`.
- Mở rộng workbook/HTML debug với role policy, charge evidence, defendant region và metadata anchor evidence.
- Thêm/cập nhật synthetic regression tests; không đọc dữ liệu thật, không gọi OCR/LLM/Docker/cloud và không commit/push.
- Verification hoàn tất: 226/226 test passed; compile, snapshot, repo/architecture guardrails, static Surya backend và extractor checks đều passed.

## 2026-07-14 - Final Excel Schema First Realignment

- Tạo canonical `FINAL_EXCEL_COLUMNS` đúng 11 cột và final row builder riêng cho rule-anchor output.
- Đổi final sheet của canonical writers và compare workbook thành `FINAL_EXCEL`, luôn đứng đầu; giữ mọi sheet kỹ thuật làm debug phụ.
- Bổ sung `case_acceptance_date`, `legal_relationship`, entity `cccd`, birth-year-only, address priority và missing-data notes.
- Đưa `FINAL EXCEL PREVIEW` đúng 11 cột lên trước phần runtime/anchor/evidence trong HTML.
- Mở rộng QA/validation cho approved participant roles và CCCD/CMND 9-12 chữ số liên tục.
- Thêm năm test modules synthetic; không đọc PDF/cache/Excel/output thật hoặc gọi LLM, Surya, Docker, cloud.
- Verification hoàn tất: 199/199 test passed; repo guardrails, architecture guardrails, static Surya backend và Local LLM config checks đều passed.

## 2026-07-14 - Fix Rule Anchor Metadata + Participant Splitter Case001

- Bỏ metadata line cap và giới hạn các field số thụ lý/đưa ra xét xử/hoãn phiên tòa về đúng token sau anchor.
- Tách juror theo newline để workbook có từng dòng `juror` riêng.
- Viết lại participant boundary cho numbering phân cấp và inline role/person; parse đúng name, presence, guardian note và lawyer note theo block.
- Sửa defendant `tam giam`, `Vợ con`, address continuation và prefix `hiện tại:`.
- Giữ standalone page-number warning trong `ANCHOR_WARNINGS` nhưng không coi riêng warning này là lý do review.
- Thêm năm regression test modules synthetic; không đọc PDF/cache/output thật hoặc gọi LLM, Surya, Docker, cloud.

## 2026-07-14 - Rule Anchor Extractor + LLM Theo Từng Block

- Thêm anchor segmenter và deterministic parser cho metadata, trial panel, defendant, participant cùng evidence line IDs/validators.
- Thêm `rule_anchor_only`, `llm_per_block`, `rule_then_llm_per_block`; đổi default compare sang rule-anchor và giữ `hybrid_rule_llm`/`llm_only` làm legacy benchmark.
- LLM mới chỉ nhận từng entity block, cap input 6000 ký tự và output 512 token; không gửi full pre-content.
- Tổng quát hóa JSON/Excel/HTML compare, thêm `ANCHOR_BLOCKS`, `ANCHOR_WARNINGS` và anchor review theo case.
- Bộ rule-anchor hiện có 23 tình huống synthetic/fake-LLM; không đọc PDF thật hoặc gọi Surya/Docker/LLM/cloud thật.

## 2026-07-14 - Local LLM Context Budget + Chunked Extraction Fix

- Chuyển default Local LLM sang Qwen2.5-3B/8192 và thêm toàn bộ env budget/chunk.
- Hợp nhất request qua budget-aware client, bắt buộc `max_tokens`, thêm error taxonomy và preflight `/models` + chat.
- Chia pre-content theo nhóm thông tin, merge partial output và loại bỏ LLM-only null giả khi runtime/chunk lỗi.
- Nâng compare CLI, HTML và workbook với structured review sheets cùng `LLM_STATUS`.
- Tests chỉ dùng mock HTTP/synthetic text; không gọi LLM, PDF, Surya, Docker hoặc cloud thật.

## 2026-07-14 - OCR Marker Early Stop Fix

- Thêm shared marker detector có Unicode folding, diacritic-insensitive matching, spacing/split-line tolerance và confidence.
- Chuyển Surya pre-content OCR sang page batch loop mặc định 1, tái sử dụng predictor và dừng ngay sau marker page.
- Bỏ page limit ngầm khi không truyền `--max-pages`; `--full-document` vẫn là explicit full OCR override.
- Thêm marker/early-stop/text-before-marker cache metadata, HTML summary/highlight và extraction wiring.
- Thêm synthetic tests; không chạy PDF, Docker, Surya inference, Local LLM hoặc cloud API thật.

## 2026-07-14 - Lưu Runtime Recipe Surya/vLLM Windows Đã Xác Nhận

- Ghi nhận Project Owner đã chạy thành công OCR page 1 với Docker shim không khoảng trắng, vLLM keep-alive, Docker named pipe và timeout 900 giây.
- Chuyển safe OCR operational recipe sang `--stamp-erase-mode mask`; component/object erase chỉ dành cho thử nghiệm có review.
- Thêm `scripts/setup_surya_windows_runtime.ps1` để tạo local shim, set env và in command runtime/OCR chuẩn mà không tự thực thi.
- Thêm ignore cho generated `tools/docker.cmd`; không chạy PDF, Docker, Surya inference, Local LLM hoặc cloud API trong Codex.

## 2026-07-14 - Surya Runtime Preflight No-Hang Fix

- Sửa GPU Docker smoke để có `checked=true`, command, return code, output tail và timeout khi được yêu cầu.
- Thêm Docker/Surya preflight mặc định cho `debug-ocr-review` và `ocr`.
- Thêm `surya_runtime_preflight.json`, `surya_runtime_diagnostics.json`, 8 stage và startup timeout.
- Thêm unit tests monkeypatch; không chạy Docker, PDF, Surya inference, Local LLM hoặc cloud API thật.

## 2026-07-10 - Pin Surya OCR Version

- Pin `surya-ocr==0.20.0` trong `pyproject.toml` và `requirements.txt`.
- Thêm version guard trước import/API/runtime; 0.21.x báo Surya 2/Docker và reinstall instructions.
- Nâng `scripts.check_ocr_backend` để in installed/supported version mà không inference.
- Thêm tests cho supported, drifted, missing và no-inference paths.
- Không chạy PDF/OCR/Surya inference/LLM/cloud/full pipeline.

## 2026-07-10 - OCR Uses Preprocessed Input

- Xác nhận Surya trước đây dùng rendered original, không dùng output từ `debug-preprocess`.
- Thêm opt-in `--use-preprocessed` và preprocess options cho `debug-ocr-review`/`ocr`.
- Nối final preprocessed path vào Surya; giữ rendered-original behavior khi không có flag.
- Thêm OCR input source/options vào result/cache/manifest và giữ preprocess/OCR artifacts cạnh nhau.
- Thêm fake Surya/CLI tests; không chạy PDF/OCR/LLM/cloud/full pipeline thật.

## 2026-07-10 - Red Seal + Text Enhancement Fix

- Mở rộng red mask thành HSV + Lab + RGB, morphology, component count và residual metrics.
- Thêm `neutralize`, `inpaint`, `white_fill` cùng black-text protection/overlap warning.
- Thêm `text-enhance off|light|medium|strong`, staged artifact và dark/foreground guard.
- Nâng CLI/debug HTML với protection mask, text-enhanced image và metadata mới.
- Thêm synthetic tests; giữ nguyên deskew và không chạy PDF/OCR/Surya/LLM/cloud/full pipeline thật.

## 2026-07-10 - Preprocess Safety Fix

- Thay auto-deskew mặc định bằng `off`; thêm `safe`/`force` và metadata angle/confidence/reason.
- Chuyển red seal HSV detection/removal lên ảnh màu trước grayscale; thêm mask, ratio và high-ratio safeguard.
- Thêm foreground/dark/brightness/entropy blank guard cùng fallback original/previous safe stage.
- Nâng `debug-preprocess` HTML/CLI với artifacts, metadata, warnings và ba preprocess profiles.
- Thêm synthetic tests; không đọc/chạy PDF thật, OCR/Surya/model/cloud hoặc full pipeline.

## 2026-07-10 - TOOLKIT-1 Evaluation Harness + Gold Dataset Manifest

- Thêm `evaluation/manifest.py`, `metrics.py`, `report.py`, `privacy.py` và package exports.
- Thêm schema validation nhẹ cho gold/prediction JSONL cùng duplicate case/obvious PII checks.
- Implement OCR, section, field, participant, evidence, source reference, review và warning metrics.
- Thêm safe JSON/Markdown report whitelist chỉ numeric metrics.
- Thêm `scripts.check_gold_manifest` và `scripts.evaluate_gold_manifest` với required paths, không real-data default.
- Thêm synthetic redacted gold/prediction fixtures và tests cho valid/mismatch/PII/report/CLI behavior.
- Mở rộng guardrail cho `data_private/`, `data/gold/`, manifest ngoài tests và PII trong fixture.
- Không tạo/đọc gold thật, không chạy PDF/OCR/Excel thật, không gọi model/cloud, không commit/push.

## 2026-07-10 - Phase 1F Consolidate Duplicate Extraction Modules

- Chọn `src/court_ocr_extract/extraction_pipeline.py` và `src/court_ocr_extract/extractors/` làm canonical extraction path.
- Hợp nhất Local LLM backend cùng typed compatibility adapter vào `extractors/local_llm_extractor.py`.
- Hợp nhất rule backend/typed anchor vào `extractors/rule_support.py`; chuyển regex parser vào `extractors/rule_parser.py`.
- Migrate pipeline, remote worker, runtime script, và tests sang canonical imports.
- Xóa `extraction/base.py`, `extraction/local_llm_extractor.py`, `extraction/rule_support.py`, root `extractor.py`, và root `llm.py`.
- Giữ typed merge/schema/validation/GLiNER helpers và direct vision/cloud benchmark adapters đúng vai trò riêng.
- Sửa `scripts.check_extractor` thành static configuration check mặc định, không endpoint request.
- Thêm synthetic no-network extraction contract tests và architecture guardrails.
- Không chạy PDF/dữ liệu/model endpoint thật, không gọi cloud API, không sửa prompt/schema lớn, và không push.

## 2026-07-10 - Phase 1E Consolidate Duplicate Excel / Export Paths

- Audited Excel/export filenames, imports, docs references, import graph, và safe repo inventory.
- Giữ `src/court_ocr_extract/excel_writer.py` làm canonical Excel writer duy nhất.
- Chuyển `rows_from_result()` và `write_excel_from_results()` từ duplicate writer vào canonical module.
- Chuyển pipeline, evaluation script, và tests sang canonical import path.
- Xóa `src/court_ocr_extract/excel.py` và `src/court_ocr_extract/export/excel_writer.py`; restore path là Git history trước Phase 1E.
- Thêm synthetic workbook contract tests cho draft records và typed `ExtractionResult`.
- Cập nhật architecture guardrail để fail khi canonical writer thiếu hoặc legacy Excel import quay lại.
- Không thay đổi 11 domain headers; 8 audit/trace columns mục tiêu vẫn cần phase schema riêng.
- Không chạy PDF thật, không đọc dữ liệu thật/Excel thật, không gọi cloud API, và không push.

## 2026-07-09 - Phase 1D Old App Folders Cleanup

- Audited old app references with `scripts.import_graph`, `scripts.repo_inventory`, and `git grep`.
- Confirmed the main `src/court_ocr_extract`/CLI path does not import `app/`, `app_fastapi/`, or `app_streamlit/`.
- Removed old app folders: `app/`, `app_fastapi/`, and `app_streamlit/`.
- Removed stale old app launch/doc/template artifacts: `scripts/ezycloudx_run_api.sh`, `scripts/ezycloudx_run_api_windows.ps1`, `docs/streamlit_vs_fastapi.md`, and `templates/upload.html`.
- Removed old UI-only optional dependencies `streamlit` and `jinja2`; kept FastAPI/uvicorn dependencies for supported remote worker tooling.
- Updated architecture guardrails/tests so old app run instructions in README/docs/scripts fail.
- Updated repo memory/docs for restore path: use Git history before Phase 1D if old UI code is needed.
- Did not run real PDFs, inspect real data, call cloud APIs, or modify Surya OCR, Local LLM extractor, Excel writer, or VLM benchmark modules.

## 2026-07-08 - Phase 1C Architecture Audit + Production Toolkit

- Thêm `scripts/repo_inventory.py` để tạo inventory an toàn, bỏ qua protected real-data/output roots.
- Thêm `scripts/import_graph.py` để dựng import graph bằng `ast` cho `src/`, `scripts/`, và `tests/`.
- Thêm `scripts/check_architecture_guardrails.py` để kiểm default/main path, cloud disabled defaults, protected path policy, CLI full-document support, và duplicate/legacy warnings.
- Thêm tests cho architecture audit scripts.
- Thêm docs Phase 1C: `REPO_INVENTORY`, `IMPORT_GRAPH`, `LEGACY_ARCHIVE_PLAN`, `PRODUCTION_TOOLKIT`, `EVALUATION_PLAN`, `GOLD_DATASET_GUIDE`, `PRIVACY_REDACTION_PLAN`, `OBSERVABILITY_PLAN`, và `MLOPS_PLAN`.
- Cập nhật `AGENTS.md`, `AGENT_ROLES.md`, `TESTING.md`, `CLEANUP_PLAN.md`, `PROJECT_STATE.md`, `TASKS.md`, `DECISIONS.md`, và `CODEX_HANDOFF.md`.
- Không xóa file, không archive/mass-move tracked code, không chạy PDF thật, không đọc dữ liệu thật, không gọi cloud API.
- Không push vì Phase 1C chưa yêu cầu push.

## 2026-07-08 - Repo Cleanup Audit

- Dọn generated cache local trong workspace, gồm `__pycache__/` và `.pytest_cache/`.
- Xác nhận không có cache Python tracked trong Git.
- Giữ nguyên tracked legacy/duplicate modules vì chưa có bằng chứng an toàn để xóa mà không ảnh hưởng pipeline.
- Không inspect hoặc dọn `data/`, `outputs/`, `logs/`, `work/`, PDF thật, image thật, Excel thật, hoặc artifact real-data.
- `ruff` không chạy được vì package chưa được cài trong `.venv`.

## 2026-07-07 - Sửa giới hạn trang debug/full-document

- Sửa `parse_page_range()` để `None`, chuỗi rỗng, và `all` nghĩa là toàn bộ trang; không còn default 3 trang đầu.
- Sửa default `--pages` của debug render/preprocess/red-seal thành toàn bộ trang; muốn giới hạn phải truyền rõ `--pages 1-3`.
- Thêm `--full-document` và `--max-pages` cho `debug-ocr-review` và `ocr`.
- `debug-ocr-review --full-document` và `ocr --full-document` truyền `max_pages=None`, `stop_marker=""`.
- Sửa Surya OCR để `stop_marker=""` không gọi marker detector, không truncate text, không break sớm, và không warning marker missing.
- Thêm test synthetic cho page range, CLI full-document, Surya full-document marker behavior, và no-fallback guard.
- Không chạy PDF thật, không inspect dữ liệu thật, không chạy extraction/LLM/Excel.

## 2026-07-07 - Phase 2A Surya OCR Runtime + Visual OCR Review

- Triển khai code path `SuryaOCRBackend` cho rendered images và output `OCRResult/OCRPage`.
- Thay placeholder runtime bằng flow thật `ocr_pdf_prefix()` -> `render_pdf_pages()` -> Surya OCR trên image -> `OCRResult`.
- Thêm kiểm tra Surya import/version/API availability có install hints.
- Hỗ trợ API `surya-ocr 0.20.0` qua `RecognitionPredictor(..., full_page=True)`.
- Nếu API Surya cài đặt không nhận diện được, adapter raise lỗi rõ: `Surya package is installed but this adapter does not support the installed API. Detected ...`.
- Thêm chuẩn hóa line với `line_id`, bbox, confidence, reading order, và warnings.
- Sắp xếp combined text theo `reading_order` khi Surya trả về thứ tự đọc.
- Thêm Surya page artifacts: original image, bbox overlay, line JSON, page text markdown, combined text, manifest, và HTML index.
- Nâng cấp OCR review HTML với original image, bbox overlay, line table, artifact links, và warnings.
- Thêm test synthetic/mocking cho `ocr_pdf_prefix()`, Surya OCR contract, placeholder guard, no-Tesseract fallback guard, và visual review.
- Không chạy PDF thật.
- Không inspect artifact OCR/debug/output thật.
- Không gọi cloud API.
- Không sửa Local LLM extractor hoặc Excel writer.

## 2026-07-07 - Cập nhật quy tắc ngôn ngữ

- Thêm quy tắc báo cáo tiếng Việt vào `AGENTS.md`.
- Thêm template `# BÁO CÁO TASK` với 9 mục tiếng Việt.
- Đồng bộ `PROJECT_STATE`, `DECISIONS`, `CODEX_HANDOFF`, `AGENT_ROLES`, và `TASKS` để các phiên Codex sau dùng tiếng Việt trong report.
- Không sửa pipeline code.
- Không xóa file.
- Không chạy hoặc đọc dữ liệu thật.

## 2026-07-07 - Phase 1B Clean Main Defaults

- Cleaned README, Ezycloudx setup/runbook docs, visual QA guide, workflow docs, `.env.example`, and sample/full run scripts away from Tesseract defaults.
- Set `settings.py` defaults to Surya OCR target, local vLLM Qwen2.5-14B target, and local VLM benchmark target.
- Added `surya` as the supported backend name for the existing Surya wrapper while keeping old `surya_optional` compatibility.
- Marked `config.py` as legacy/compatibility config.
- Recorded `excel_writer.py` as canonical Excel writer.
- Updated cleanup plan, architecture, testing, runbook, project state, decisions, tasks, and handoff.
- No real PDFs, OCR text, derived real-data outputs, or sensitive artifacts were inspected.
- No files were deleted or moved into archive.
- No real Surya/VLM runtime implementation was added.

## 2026-07-07 - Phase 1A Reorientation

- Added project memory files for state, architecture, decisions, tasks, handoff, pipeline spec, data schema, debug output spec, testing, model benchmark, Ezycloudx runbook, security/privacy, cleanup plan, and agent roles.
- Updated `AGENTS.md` with the new rebuild direction, Codex memory protocol, and cleanup approval rule.
- Added safe repo snapshot and guardrail check scripts.
- Added focused tests for the new guardrail/snapshot helpers.
- No real PDFs, OCR text, derived real-data outputs, or sensitive artifacts were inspected.
- No production pipeline behavior was intentionally changed.
- No files were deleted.
## 2026-07-10 - SURYA WINDOWS RUNTIME + OCR STAMP SUPPRESSION V3

- Them resolver Docker runtime cho Windows va script diagnostics Surya.
- Them stamp suppression/filter theo mask, overlap metadata, raw/filtered/excluded artifacts.
- Sua relative link trong OCR review khi artifact nam ngoai `ocr_surya/`.
- Bo sung synthetic tests; khong chay du lieu/PDF/OCR inference that.
## 2026-07-13 - PRE-CONTENT EXTRACTION A/B TEST

- Thêm nhánh thử nghiệm so sánh hybrid rule+LLM và LLM-only trên phần trước `NỘI DUNG VỤ ÁN`.
- Thêm document router, segmenter, schema, rule extractor, hybrid merge, prompts và compare runner.
- Thêm review artifacts JSON/Excel/HTML và synthetic tests; không chạy PDF/Surya/Local LLM thật trong Codex.
## 2026-07-14 - STAMP OBJECT ERASE FIX

- Thêm component-level stamp object mask và erase modes.
- Thêm expanded object region, noise/page-size guards, dark-text overlap fallback và metadata.
- OCR filter tiếp tục hoạt động, ưu tiên object mask khi có.
- Thêm synthetic artifacts/tests; không chạy dữ liệu thật.
## 2026-07-14 - FINAL PREPROCESS CANDIDATE SELECTION FIX

- Object seed chuyển sang union `red_mask OR stamp_suppression_mask` và morphology ưu tiên stamp ngang.
- Thêm `object_seed_mask`, candidate scoring và selected final/OCR stage metadata.
- Ngăn text-enhanced candidate làm residual đậm hoặc làm mất foreground được chọn làm final.
- Thêm synthetic selection tests; không chạy PDF/OCR thật.
