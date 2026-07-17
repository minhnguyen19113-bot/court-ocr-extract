# Codex Handoff

## Bàn Giao Fast Patch 13 Cột, Verdict Charge và Địa Chỉ Qua Trang

`FINAL_EXCEL` hiện theo schema 13 cột và chỉ chứa `Bị cáo`/`Bị hại`. Số/ngày bản án và số/ngày thụ lý map độc lập; thiếu field nào để trống và note đúng field. Participant khác vẫn ở structured JSON/`PARTICIPANTS`; sheet và HTML `NGUOI_THAM_GIA_KHAC` chỉ bật khi caller truyền `include_other_participants_output=true`.

Charge parser đọc verdict block có guard 10 lines/1600 chars, hỗ trợ 1-8 dòng synthetic, punishment phrase, quoted/unquoted charge và page break. Decision diagnostics đã có status, heading page, tail lines, candidate/parsed/mapped/unmapped counts, candidate raw block, evidence và warning phân loại. Current address được nối qua page break đến identity/entity boundary, bỏ standalone page number và giữ evidence line IDs.

Gate patch đã qua: targeted 10/10 và focused address regression 11/11. Full suite hiện 240/252 passed; 12 failure đều là assertion legacy còn đòi schema 11 cột, role liên quan trong final, sheet/HTML participant khác bật mặc định hoặc chỉ số cột cũ. Task chỉ cho cập nhật đúng 9 test modules mới, vì vậy chưa realign các test legacy ngoài danh sách. Không có PDF/cache/output thật, OCR, Surya, Docker, LLM, cloud, commit hoặc push.

Project Owner chỉ rerun extraction từ cache bằng `compare-pre-content --ocr-cache-dir outputs\ocr_cache_pre_content_early_stop_1 --decision-tail-cache-dir outputs\decision_tail_cache_pilot_one --output-dir outputs\final_schema_charge_address_patch_check_1 --strategies rule_anchor_only --limit 1 --open`. Kiểm `compare_summary.xlsx`, `compare_summary.json`, `index.html`, `cases\<case_id>\review.html` và strategy JSON trong thư mục case; không OCR lại front hoặc decision tail.

## Bàn Giao Front + Decision Source và Legal Relationship Theo Dòng

Nguồn production hiện bị khóa ở `front_pre_content` và `decision_tail`. `middle_excluded` gồm narrative/tranh luận/nhận định không được fill final field, không được làm fallback và không xuất hiện trong charge/source review. Front entities có stable `entity_id`; decision parser chỉ đối chiếu với dictionary này, không tạo defendant mới từ phần cuối.

`QUAN HỆ PHÁP LUẬT` của dòng bị cáo lấy riêng từ `defendant_charge_map[entity_id]`; primary role không phải bị cáo lấy `case_charges`. Mapping ambiguous/collective không chắc để trống và warning. Parser chỉ dùng explicit verdict language, hỗ trợ quoted/unquoted, không suy từ statute, behavior, document type, filename hoặc LLM.

Reverse decision scan bắt buộc `--decision-tail-max-scan-pages` dương và hữu hạn. Khi heading vắng, status là `heading_not_found`, final relationship để trống có note và code không quét toàn PDF. Review workbook dùng `CHARGES`, `DEFENDANT_CHARGES`, `SOURCE_REGION_AUDIT`, `CHARGE_WARNINGS`; HTML đặt các section tương ứng sau hai preview user-facing.

Gate local mới nhất: 242/242 synthetic tests passed; compile/guardrail/static checks cần được chạy lại sau khi docs hoàn tất. Task không mở PDF/cache/output thật, không gọi Surya/LLM/Docker/cloud và không commit/push. Project Owner phải dùng `data\raw_pdfs\pilot_one` và `outputs\ocr_cache_pre_content_early_stop_1`, review một case trước khi tăng batch.

## Bàn Giao Final Role, Boundary và Decision Tail

Pre-content hiện giữ toàn bộ line trước marker, chỉ dùng page limit khi marker vắng. Defendant segmenter không còn fallback từ numbered line toàn tài liệu; intro có thể nằm giữa/cuối metadata line, trial panel/metadata/participant IDs bị cô lập, và rejected candidate có reason trong HTML/anchor output. Metadata anchors được kiểm tra độc lập; ngày thụ lý chỉ parse sau số thụ lý.

`FINAL_EXCEL` vẫn là sheet đầu với đúng 11 cột, nhưng chỉ chứa primary roles. Sheet thứ hai `NGUOI_THAM_GIA_KHAC` chứa guardian/representative/defense/protection/witness/support roles; court roles chỉ ở debug. `QUAN HỆ PHÁP LUẬT` không còn giá trị generic `Hình sự`; nếu chưa có explicit charge thì để trống và ghi note.

Stage mới `ocr-decision-tail` chỉ chấp nhận Surya, scan ngược theo batch, dừng ở normalized decision heading và ghi cache riêng. Extraction có thể nhận `--decision-tail-cache-dir`; parser chỉ chấp nhận explicit verdict phrases, không suy đoán từ điều luật, hành vi, tên file hoặc document type. OCR cache cũ không đổi schema.

Project Owner phải chạy cache-only extraction cho 1 case trước, review `FINAL_EXCEL` và `NGUOI_THAM_GIA_KHAC`, rồi mới chạy decision-tail OCR cho chính case đó. Codex chỉ chạy synthetic tests, chưa mở/chạy dữ liệu thật và không commit/push.

Gate local đã qua: 226/226 test, compile, snapshot, repo/architecture guardrails, static Surya `0.20.0` adapter check và static Local LLM configuration check. Warning duy nhất là deprecation từ Surya/Pydantic.

## Bàn Giao Final Excel Schema First

Output chính hiện là sheet đầu `FINAL_EXCEL`, đúng 11 cột từ `FINAL_EXCEL_COLUMNS`. `final_excel_builder.py` map metadata/panel/defendants/participants thành một dòng mỗi người; không đưa JSON, evidence blob hoặc field kỹ thuật vào final sheet. `DATA` và `Trich xuat` không còn là tên sheet final.

Verification synthetic/static hiện tại: 199/199 test passed; repo guardrails, architecture guardrails, static Surya backend check và Local LLM config check đều passed. Architecture check chỉ còn các warning inventory đã biết, không có failure.

Project Owner chạy `rule_anchor_only --limit 1` trước và review hai sheet user-facing: số/ngày thụ lý, primary/support role placement, role dài không bị collapse, năm sinh chỉ còn năm, judge lặp đúng và field thiếu để trống kèm note. Không dùng kỳ vọng số dòng lịch sử; sau đó mới dùng debug sheets để truy nguyên. Codex chưa chạy/đọc case hoặc runtime thật.

## Bàn Giao Bản Vá Rule Anchor Case001

Code đã có regression contract cho ba metadata case-number tokens, juror newline, bốn participant blocks theo cấu trúc `7.x.`, các field defendant nhỏ và informational warning severity. Không rebuild architecture và không thay Local LLM/Surya/Excel writer.

Project Owner cần chạy lại `case_001` bằng `rule_anchor_only` trước. Kiểm `case_acceptance_number`, `postponement_decision_number`, hai dòng `juror`, bốn participant đúng role/name, `Vợ con`, detention/address và `CASES.needs_review`. Chỉ khi rule-only đạt mới chạy `rule_then_llm_per_block --require-llm`. Codex chưa đọc output thật hoặc gọi runtime thật.

## Bàn giao Rule Anchor Baseline

Pre-content default hiện là `rule_anchor_only,rule_then_llm_per_block`. Anchor segmenter cắt metadata/trial-panel/defendant/participant blocks; deterministic parser sở hữu metadata, trial panel và entity fields; Local LLM chỉ repair từng block cần thiết với cap 6000 ký tự/512 token.

Project Owner chạy 1 case trước và review `ANCHOR_BLOCKS`, `ANCHOR_WARNINGS`, `CASES`, `DEFENDANTS`, `PARTICIPANTS`, `TRIAL_PANEL`, `LLM_STATUS` cùng HTML. Không tiếp tục 3 case nếu block boundary, full name, judgment date hoặc role participant ở case đầu chưa đúng. `hybrid_rule_llm`, `legacy_hybrid_rule_llm` và `llm_only` chỉ còn dùng khi cần benchmark lịch sử.

## Bàn giao Local LLM context budget

Canonical Local LLM hiện là `Qwen/Qwen2.5-3B-Instruct` tại `http://127.0.0.1:8000/v1`, context 8192, output 1024, input 6000 và safety margin 512. Không đổi lại 7B full bf16 trên RTX 5060 Ti 16GB nếu chưa có runtime profile khác chứng minh đủ KV cache.

Trước compare, chạy `.\.venv\Scripts\python.exe -B -m scripts.check_llm_backend`; sau khi `ok=true`, chạy `compare-pre-content --require-llm --limit 1`. Review `LLM_STATUS`, chunk errors, `llm_actually_called` và HTML. `llm_only_failed`/`llm_only_not_run` không phải extraction hợp lệ; hybrid rule-only fallback phải được đánh dấu cần review. Codex chưa gọi endpoint thật.

## Bàn giao OCR marker early-stop

Surya `ocr` hiện mặc định xử lý từng page với một predictor runner dùng lại và dừng ở high/medium marker `NỘI DUNG VỤ ÁN`. Không truyền `--max-pages` nghĩa là chạy đến marker hoặc hết file. `--full-document` là override duy nhất để không dừng/trim.

Kiểm cache `metadata.marker`, `metadata.early_stop`, `pages_total`, `text_before_marker`; kiểm HTML marker highlight và pages skipped. Low-confidence `noi dung` đơn lẻ không kích hoạt stop. Project Owner cần giữ vLLM container warm và chạy lại 1 PDF trước, sau đó mới chạy 9 PDF.

## Bàn giao runtime Windows đã chạy thành công

Project Owner đã xác nhận OCR page 1 chạy được với `C:\court-ocr-extract\tools\docker.cmd`, `SURYA_INFERENCE_BACKEND=vllm`, `SURYA_INFERENCE_KEEP_ALIVE=1`, Docker named pipe và startup timeout 900 giây. GPU checker phải trả `checked=true`, `ok=true`; giữ container `surya-vllm-*` warm và allow cả Private/Public nếu Windows Firewall/Docker hỏi trên VM.

Dùng `scripts/setup_surya_windows_runtime.ps1` để tái tạo shim/env và in command chuẩn. Safe OCR bắt buộc dùng `--stamp-erase-mode mask`; không đổi sang component/object erase nếu chưa có visual review riêng. Lỗi khựng đã xác định là vLLM cold start, không phải preprocess/stamp.

## Bàn giao Surya runtime preflight

Surya OCR CLI hiện fail-fast qua preflight mặc định. Trước pilot, Project Owner phải chạy `scripts.check_surya_runtime_backend` và lệnh có `--check-gpu-container`; lệnh thứ hai chỉ đạt khi `gpu_container.checked=true` và `ok=true`. Khi OCR timeout, đọc `surya_runtime_preflight.json` và `<case>/surya_runtime_diagnostics.json`, đặc biệt `last_stage`.

Các option mới: `--skip-surya-runtime-preflight`, `--surya-runtime-check-gpu-container`, `--surya-runtime-timeout-seconds`, `--surya-startup-timeout-seconds`; env startup là `SURYA_STARTUP_TIMEOUT_SECONDS`. Codex chưa chạy Docker/PDF/Surya thật và không sửa preprocess/stamp.

Last updated: 2026-07-17

## Read First

For the next Codex session, read these before acting:

1. `AGENTS.md`
2. `docs/PROJECT_STATE.md`
3. `docs/DECISIONS.md`
4. `docs/TASKS.md`
5. `docs/CODEX_HANDOFF.md`
6. `docs/ARCHITECTURE.md`
7. `docs/PIPELINE_SPEC.md`
8. `docs/CLEANUP_PLAN.md` if cleanup/refactor is involved
9. `docs/REPO_INVENTORY.md`, `docs/IMPORT_GRAPH.md`, `docs/LEGACY_ARCHIVE_PLAN.md`, and `docs/PRODUCTION_TOOLKIT.md` if architecture audit, cleanup/archive, or production readiness is involved
10. `docs/EVALUATION_PLAN.md`, `docs/GOLD_DATASET_GUIDE.md`, `docs/PRIVACY_REDACTION_PLAN.md`, `docs/OBSERVABILITY_PLAN.md`, and `docs/MLOPS_PLAN.md` if evaluation, privacy, observability, or runtime/model governance is involved

## Current State

Phase 1C đã thêm architecture audit + repo slimming plan + production toolkit blueprint. Các artifact mới:

- `scripts/repo_inventory.py`
- `scripts/import_graph.py`
- `scripts/check_architecture_guardrails.py`
- `docs/REPO_INVENTORY.md`
- `docs/IMPORT_GRAPH.md`
- `docs/LEGACY_ARCHIVE_PLAN.md`
- `docs/PRODUCTION_TOOLKIT.md`
- `docs/EVALUATION_PLAN.md`
- `docs/GOLD_DATASET_GUIDE.md`
- `docs/PRIVACY_REDACTION_PLAN.md`
- `docs/OBSERVABILITY_PLAN.md`
- `docs/MLOPS_PLAN.md`

Phase 1C không xóa file, không archive/mass-move tracked code, không chạy dữ liệu thật, không inspect protected artifacts, và không push khi chưa được yêu cầu.

Phase 1D removed old app/UI folders after audit confirmed no main `src/`/CLI import dependency:

- Removed `app/`
- Removed `app_fastapi/`
- Removed `app_streamlit/`
- Removed `docs/streamlit_vs_fastapi.md`
- Removed `scripts/ezycloudx_run_api.sh`
- Removed `scripts/ezycloudx_run_api_windows.ps1`
- Removed `templates/upload.html`
- Removed `streamlit` and `jinja2` from optional `web` dependencies

Restore path: use Git history before the Phase 1D commit if an old UI is needed. Do not recreate `legacy/`, `archive/`, `old/`, or `deprecated/` folders for this code unless Project Owner explicitly asks.

Phase 1E consolidated Excel/export paths:

- Canonical: `src/court_ocr_extract/excel_writer.py`.
- Migrate pipeline, evaluation script, và tests sang canonical import.
- Removed `src/court_ocr_extract/excel.py`.
- Removed `src/court_ocr_extract/export/excel_writer.py`.
- Không tạo compatibility wrapper vì không còn caller trong repo.
- Restore path: use Git history before the Phase 1E commit.
- Workbook schema vẫn là 11 domain headers; 8 audit/trace columns mục tiêu cần phase schema riêng.

Phase 1F consolidated extraction modules:

- Canonical orchestrator: `src/court_ocr_extract/extraction_pipeline.py`.
- Canonical package: `src/court_ocr_extract/extractors/`.
- Canonical Local LLM: `src/court_ocr_extract/extractors/local_llm_extractor.py`.
- Canonical rule helper: `src/court_ocr_extract/extractors/rule_support.py`.
- Removed `extraction/base.py`, `extraction/local_llm_extractor.py`, `extraction/rule_support.py`, root `extractor.py`, và root `llm.py`.
- `extraction/` chỉ còn typed merge/schema/validation/GLiNER helpers, không phải backend owner.
- `TypedLocalLLMExtractor` giữ old typed pipeline behavior trong canonical module; không có wrapper file.
- `scripts.check_extractor` là static config check, không endpoint request.
- Restore path: use Git history before the Phase 1F commit.

TOOLKIT-1 added a privacy-aware evaluation foundation:

- Package: `src/court_ocr_extract/evaluation/`.
- Scripts: `scripts/check_gold_manifest.py`, `scripts/evaluate_gold_manifest.py`.
- Synthetic fixtures: `tests/fixtures/gold_manifest_synthetic.jsonl`, `prediction_manifest_synthetic.jsonl`.
- Report chỉ whitelist aggregate numeric metrics, không chứa raw expected/predicted values.
- `data_private/`, `data/gold/` và manifest ngoài `tests/fixtures/` bị guardrail chặn.
- Gold thật không commit/không đưa vào Codex; Project Owner review và chạy ngoài Codex.
- TOOLKIT-1 chưa nối trực tiếp pipeline output thật và chưa tính OCR CER/WER.

Phase 2A đã triển khai đường chạy Surya OCR ở mức code/contract và thêm artifact để review OCR bằng hình ảnh. README, `.env.example`, Ezycloudx docs, visual QA docs, workflow docs, run scripts, và `settings.py` vẫn trỏ về default Surya target thay vì Tesseract.

Canonical decisions:

- `src/court_ocr_extract/settings.py` is canonical rebuild config.
- `src/court_ocr_extract/config.py` is compatibility/legacy.
- `src/court_ocr_extract/excel_writer.py` là canonical Excel writer duy nhất; không import hai path đã xóa.
- `src/court_ocr_extract/extraction_pipeline.py` và `src/court_ocr_extract/extractors/` là canonical extraction path.
- `src/court_ocr_extract/evaluation/` là canonical manifest/metrics/report toolkit.
- Surya OCR + local LLM is the main candidate.
- Local VLM is the benchmark path.

Phase 2A đã có wiring Surya OCR ở mức code/contract, nhưng chất lượng OCR thật chưa được validate trên PDF thật trong Codex.

Phase 2A notes:

- `src/court_ocr_extract/ocr_backends/surya_ocr.py` không còn placeholder `runtime wiring is incomplete`.
- `ocr_pdf_prefix()` đã implement flow `pdf_path` -> `render_pdf_pages()` -> Surya OCR trên rendered images -> normalize `OCRResult`.
- Adapter hỗ trợ API `surya-ocr 0.20.0` bằng `RecognitionPredictor(..., full_page=True)`.
- Nếu API Surya cài đặt không được hỗ trợ, adapter raise lỗi rõ với prefix `Surya package is installed but this adapter does not support the installed API. Detected ...`.
- `--ocr-backend surya` route qua Surya backend.
- `debug-ocr-review` có thể dùng wiring `surya`, nhưng Codex không được chạy command này trên PDF thật.
- Surya artifact theo page được ghi dưới `ocr_surya/` khi bật debug visual.
- Synthetic tests chỉ chứng minh schema/control-flow, không chứng minh chất lượng OCR thật.
- Nếu thiếu/sai version Surya, uninstall rồi cài lại bằng `pip install -e ".[dev,ocr]"`; không dùng install không pin.

Full-document debug review notes:

- `debug-render`, `debug-preprocess`, và `debug-red-seal` mặc định chạy toàn bộ trang nếu không truyền `--pages`.
- Muốn giới hạn trang review thì truyền rõ `--pages 1-3` hoặc range tương tự.
- `debug-ocr-review --full-document` truyền `max_pages=None` và `stop_marker=""` vào backend, nên không dừng/truncate tại marker `NỘI DUNG VỤ ÁN`.
- `ocr --full-document` cũng truyền `max_pages=None` và `stop_marker=""`, chỉ tạo OCR cache/debug visual, không chạy extraction/LLM/Excel.
- Pilot 1 PDF nên dùng folder `data\raw_pdfs\pilot_one` với `--limit 1` và `--review-sample-size 1`.

Preprocess safety notes:

- Auto-deskew `minAreaRect` cũ đã bị thay; canonical preprocess default không rotate.
- `debug-preprocess` default: `--deskew off --red-seal-removal on --preprocess-profile conservative`.
- Red mask/removal chạy trên original color trước grayscale; output có per-page `red_mask.png`, `seal_removed.png`, `final_preprocessed.png` và `metadata.json`.
- `safe` deskew chỉ rotate khi đủ confidence và qua angle/crop/multi-column guard; rotation mở rộng canvas.
- Blank guard fallback về original/previous safe stage và ghi warnings rõ.
- Không có real PDF/OCR run trong task; Project Owner phải review bản `off` trên Ezycloudx trước khi tiếp tục OCR.

Red seal/text enhancement v2 notes:

- Default CLI: `--red-removal-mode neutralize --text-enhance light`; deskew vẫn `off`.
- Detector dùng HSV + Lab + RGB; artifacts thêm `black_text_protection_mask.png` và `text_enhanced.png`.
- Modes: `neutralize` bảo thủ, `inpaint` làm sạch residual hai lượt, `white_fill` chỉ thử nghiệm.
- Protection mask giữ nét tối; overlap đáng kể ghi `red_mask_overlaps_dark_text`.
- Text enhancement chạy sau red removal; guard fallback khi dark pixels/foreground bùng nổ hoặc entropy collapse.
- Project Owner cần so sánh ba run v2 trong runbook; Codex chưa đọc/chạy real PDF/output.

OCR preprocessed-input notes:

- Trước wiring này, Surya backend render và OCR ảnh gốc; `debug-preprocess` không nối vào OCR.
- `--use-preprocessed` hiện opt-in cho `debug-ocr-review` và `ocr`, chỉ hỗ trợ Surya.
- Candidate được chọn: deskew off, red removal inpaint, text medium, profile balanced, red removal on.
- Backend ghi `ocr_input_source`/options vào `OCRResult.metadata`, cache và manifest; page artifact có `ocr_input_image_path`.
- Không có flag thì giữ rendered-original behavior. Preprocess exception tạo final safe copy có warning.
- Fake-backend tests chứng minh wiring; Project Owner vẫn phải chạy visual OCR review thật.

Surya version-pin notes:

- Main path hỗ trợ exact `surya-ocr==0.20.0`; pin nằm trong `pyproject.toml` và `requirements.txt`.
- 0.21.x là Surya 2, cần inference backend/Docker và không được hỗ trợ trong phase này.
- Guard đọc package metadata trước import; `check_ocr_backend` in installed/supported version và không inference.
- VM bị drift phải uninstall Surya rồi reinstall `.[dev,ocr]`; không dùng `pip install surya-ocr` không pin.
- Local `.venv` tại thời điểm task có 0.20.0 và static availability check pass.

Repo cleanup notes:

- Generated cache local đã được dọn khỏi workspace.
- Tracked legacy/duplicate modules chưa bị xóa; chúng vẫn cần canonical owner decision trước khi archive/delete.
- Không inspect hoặc cleanup protected real-data folders trong Codex.

## Important Warnings

- Do not inspect real data directories or outputs.
- Do not run real PDF workflows inside Codex.
- Do not call cloud APIs by default.
- Do not use synthetic smoke to judge real quality.
- Do not clean/delete/archive files until a later cleanup scope is approved.

## Quy tắc ngôn ngữ

- Báo cáo gửi Project Owner/ChatGPT phải viết bằng tiếng Việt.
- Heading report dùng tiếng Việt.
- Giữ nguyên tiếng Anh cho tên kỹ thuật chuẩn như file path, class, function, CLI command, env var, model name, package name, schema field.
- Không dùng format nửa Anh nửa Việt.
- Nếu prompt từ ChatGPT có heading tiếng Anh, Codex vẫn trả lời bằng tiếng Việt trừ khi được yêu cầu khác.

Template report chuẩn:

1. Tóm tắt
2. File đã thay đổi
3. Quyết định đã áp dụng
4. Lệnh đã chạy
5. Kết quả test
6. Output/debug đã tạo
7. Rủi ro còn lại
8. Câu hỏi cần quyết định
9. Bước tiếp theo đề xuất

## Known Conflicts

- Tesseract remains in code/docs only as legacy optional; Surya backend must not fallback to Tesseract.
- `settings.py` and `config.py` still overlap internally, but `settings.py` is canonical for new work.
- Validation, render, và OCR paths vẫn overlap; Excel/extraction backend overlap đã được xử lý trong Phase 1E/1F.
- Old app folders were removed in Phase 1D; do not reintroduce old app run instructions in README/docs/scripts.

## Suggested Next Step

Project Owner chạy `rule_anchor_only` từ OCR cache cũ cho 1 case, review `FINAL_EXCEL` và `NGUOI_THAM_GIA_KHAC`. Khi role/boundary/metadata đạt mới chạy `ocr-decision-tail` cho case đó và rerun extraction với tail cache; chưa bật Local LLM và chưa tăng lên 3/9 PDF.
## Ban giao moi nhat

Task hien tai da hoan thien contract cho Windows Surya runtime va stamp suppression V3. Dung `--stamp-suppression balanced` va `--ocr-stamp-filter balanced` khi co `--use-preprocessed`; dung aggressive chi sau visual review.

Codex chua chay PDF that, chua goi Surya inference/Local LLM/cloud API, va khong commit/push. Project Owner can kiem balanced output, excluded stamp lines, raw-vs-filtered text va false removal tren Ezycloudx.
## Bàn giao pre-content legacy A/B

CLI `compare-pre-content` vẫn nhận `hybrid_rule_llm`, `legacy_hybrid_rule_llm` và `llm_only`, nhưng không chọn chúng mặc định. Correction notice vẫn route riêng và không tính vào judgment benchmark.
## Bàn giao Stamp Object Erase

`red_mask` không còn được xem là bằng chứng dấu mộc đã bị xóa sạch. `stamp_object_mask` và `stamp_object_erased` chỉ phục vụ thử nghiệm/review object erase. Operational safe recipe phải truyền `--stamp-erase-mode mask`; không dựa vào parser default lịch sử `component_white_fill`. Post-OCR stamp filter vẫn được giữ.

Codex chỉ chạy synthetic tests, không chạy PDF, Surya inference, Local LLM hoặc cloud API. Project Owner cần so sánh residual và false removal bằng hai command balanced/inpaint và aggressive/white-fill trong runbook.
## Bàn giao Final Candidate Selection

`final_preprocessed` không còn là stage cố định trước suppression. Bản trước selection nằm ở `final_preprocessed_candidate`; selected output được ghi vào `final_preprocessed` và `ocr_input_stamp_suppressed`. Review `object_seed_mask`, `candidate_scores`, `final_selected_stage` và `ocr_input_source_stage`. Nếu lowest-residual candidate không an toàn cho text, metadata phải ghi warning/fallback.

Codex không chạy dữ liệu thật. Project Owner cần xác nhận dấu ngang chính xuất hiện trong object mask và selected final thực sự không tệ hơn `stamp_object_erased` trên page 1.
