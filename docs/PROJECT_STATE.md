# Project State

## Pilot 10 Sentence Audit Final Hardening

- Probation start nhận bounded OCR variants `sơ thảm/sơ thẳm`, parenthesized/bare/textual date và canonicalize display về `sơ thẩm DD/MM/YYYY`; raw evidence giữ nguyên OCR và không fallback judgment metadata.
- `probation_duration_partial` chỉ phát khi phần dư cho thấy unit/value bị cắt thật. Duration hợp lệ một hoặc nhiều đơn vị như `3 năm`, `18 tháng`, `4 năm 6 tháng` không warning.
- Sentence evidence được tách theo `evidence_type`: `primary_penalty`, `probation`, `sentence_start`, `detention_credit`, `completion`, `release`, `aggregate_penalty`, `additional_penalty`. Primary/probation dừng trước custody measure, UBND supervision, vật chứng, tư pháp, án phí, kháng cáo và nơi nhận; scanner vẫn có thể nhận additional penalty hợp lệ ở item sau.
- `sentence_warnings` là structured audit theo case/entity với severity, scope, page, line IDs, raw text và source region. Name disagreement bổ sung front/decision names, normalized names, match method và similarity; FINAL_EXCEL luôn giữ front name.
- `procedural_verdict_candidate_rejected` và procedural rejection tương tự chỉ là debug/informational, không tạo `Field bị validator loại` cho mọi dòng và không tự bật `needs_review`. Field-level whitelist vẫn gắn note đúng entity.
- Workbook `SENTENCE_EVIDENCE` và `SENTENCE_WARNINGS` có đầy đủ typed/source/audit columns; không còn sentence warning row rỗng khi parser có source evidence.
- Verification synthetic: targeted `30 passed`; sentence regression `84 passed`; regression group `150 passed`; full suite `394 passed`, `0 failed`, không thêm skip/xfail. Không đọc dữ liệu thật và không gọi OCR, Docker, Surya inference, LLM hoặc cloud.

## Pilot 10 Sentence Completeness and Evidence Hardening

- `sentence_parser.py` nhận ngày Việt Nam dạng chữ, ba biến thể hẹp của `bắt giam`, probation nhiều đơn vị có dấu phẩy và `probation_start_text`; trường probation start không bị ghi nhầm vào custodial `sentence_start_text`.
- Completion hỗ trợ `bằng với thời gian tạm giam` và OCR `hình phát tù`, luôn canonical về `hình phạt`; detention credit hỗ trợ `trừ ngày`/`trừ thời gian`/`được trừ` và chuẩn hóa date range mà không tự tính số ngày.
- Hình phạt bổ sung được scan theo bounded clause trong `decision_tail`, kể cả numbered item riêng và OCR `hình phát/phát bổ sung`; chỉ explicit additional-penalty anchor mới cho phép map khoản tiền theo defendant entity, không dùng case fallback và không lấy án phí/nghĩa vụ dân sự.
- Mỗi sentence evidence giữ `raw_text` khớp `line_ids`, bao gồm release/additional lines tạo display và dừng trước vật chứng, biện pháp tư pháp, án phí, kháng cáo hoặc nơi nhận.
- Completeness validator phát bảy warning canonical và đẩy case/row có warning quan trọng vào review; victim không nhận sentence warning. `FINAL_EXCEL` vẫn đúng 14 cột, victim `HÌNH PHẠT` vẫn blank.
- Verification synthetic: targeted sentence `61 passed`; regression schema/role/charge/address/source-region `94 passed`; full suite `367 passed`, `0 failed`, không thêm skip/xfail. Codex không đọc dữ liệu thật và không gọi OCR, Docker, Surya inference, LLM hoặc cloud.

## Defendant Sentence Column + Final Address Hardening

- `FINAL_EXCEL` dùng contract mới đúng 14 cột; `HÌNH PHẠT` đứng sau `QUAN HỆ PHÁP LUẬT`, trước `TƯ CÁCH TỐ TỤNG`, và `GHI CHÚ` vẫn là cột cuối.
- `sentence_parser.py` chỉ đọc `decision_tail`, tái sử dụng verdict blocks và defendant matcher từ `charge_parser.py`, tạo `defendant_sentence_map`, `sentence_evidence`, warnings và diagnostics. Không có case-level sentence fallback.
- Defendant row lấy sentence theo `entity_id`/`source_block_id`; victim row luôn để `HÌNH PHẠT` trống và không nhận missing-sentence note. Cùng người khác role vẫn độc lập.
- Parser deterministic hỗ trợ tù có thời hạn, án treo/thử thách, cải tạo không giam giữ, phạt tiền hình sự, chung thân, tử hình, cảnh cáo, trục xuất, miễn hình phạt, execution details, hình phạt chung và hình phạt bổ sung; không tự cộng aggregate và không lấy án phí/nghĩa vụ dân sự.
- Workbook review có `DEFENDANT_SENTENCES`, `SENTENCE_EVIDENCE`, `SENTENCE_WARNINGS`; source-region audit nhận `HÌNH PHẠT` từ `decision_tail`.
- Address parser tách permanent/current candidates, ưu tiên `Nơi ở`, chặn presence sentence khỏi địa chỉ và loại presence suffix có dấu câu nhưng giữ parenthetical không phải presence.
- Verification synthetic: address `29 passed`; sentence/schema/final `47 passed`; regression group cuối `148 passed`; full suite `342 passed`, `0 failed`, không có skip/xfail mới.
- Codex chỉ dùng synthetic tests; không đọc PDF/cache/output thật và không gọi OCR, Docker, Surya inference, LLM hoặc cloud.

## Fast Patch 13 Cột, Verdict Block và Địa Chỉ Qua Trang

- `FINAL_EXCEL` hiện có đúng 13 cột; `SỐ BẢN ÁN`, `NGÀY TUYÊN ÁN`, `SỐ THỤ LÝ`, `NGÀY THỤ LÝ` map độc lập từ metadata và không fallback chéo. Field thiếu để trống, kèm note đúng field.
- Output final mặc định chỉ tạo dòng `Bị cáo` và `Bị hại`. Participant khác vẫn ở structured JSON và sheet debug `PARTICIPANTS`; `NGUOI_THAM_GIA_KHAC` cùng section HTML tương ứng mặc định tắt, có thể bật bằng `include_other_participants_output=true`.
- `charge_parser.py` dùng verdict block tối đa 10 lines/1600 chars, sắp theo page/reading order, bỏ số trang độc lập và không kết thúc ở page break. Name matching dùng front defendant dictionary; punishment phrase không bị coi là tên.
- Decision-tail output có đủ heading/tail/candidate/parsed/mapped/unmapped diagnostics, candidate raw blocks, charge evidence và ba warning phân biệt nguyên nhân blank.
- Defendant current address nối continuation qua page break, bỏ standalone page number, dừng tại identity/entity boundary và giữ evidence line IDs. Tiền tố phụ `hiện tại:`/`hiện nay:` sau label được bỏ.
- Targeted patch: 10/10 passed; focused rerun gồm regression địa chỉ cũ: 11/11 passed. Full suite hiện 240/252 passed; 12 test legacy còn khóa schema 11 cột, role phụ hoặc output participant khác bật mặc định. Task giới hạn test được sửa ở đúng 9 module mới nên các legacy assertion chưa được realign.
- Không đọc/chạy PDF, cache hoặc output thật; không gọi OCR, Surya, Docker, LLM hay cloud; không commit/push.

## Front + Decision Only Source Policy và Row-specific Legal Relationship

- Production extraction chỉ dùng `front_pre_content` và `decision_tail`; `middle_excluded` không được fill `FINAL_EXCEL` hay làm fallback. `source_region_policy.py` giữ canonical region, field-source allowlist và audit contract.
- Front sở hữu loại án, thụ lý, role, identity, địa chỉ và chủ tọa. Decision tail sở hữu tội danh; các field tuyên án khác mới chỉ được bảo lưu trong contract để mở rộng sau, chưa thêm cột final.
- `charge_parser.py` hỗ trợ explicit quoted/unquoted verdict, giữ `ChargeEvidence`, `case_charges` theo thứ tự và `defendant_charge_map` keyed by front defendant `entity_id`. Exact/honorific/unique-fuzzy matching đều fail-safe; ambiguous/collective không chắc chỉ warning, không gán charge.
- Dòng bị cáo chỉ dùng specific charge của entity đó. Primary role không phải bị cáo dùng toàn bộ case charges. Cùng người khác role giữ hai dòng với relationship tương ứng. Thiếu hoặc ambiguous để trống kèm note; không fallback `Hình sự`.
- Reverse scan bắt buộc guard `decision_tail_max_scan_pages` dương, hữu hạn. Không thấy heading thì `decision_tail_status=heading_not_found`; không có silent full-document fallback.
- Workbook có `CHARGES`, `DEFENDANT_CHARGES`, `SOURCE_REGION_AUDIT`, `CHARGE_WARNINGS`; HTML đặt charge summary/map/source audit ngay sau hai preview user-facing và không hiển thị middle content.
- Task không dùng LLM, OCR, Docker, cloud hay dữ liệu thật; không commit/push. Verification synthetic hiện tại: 242/242 test passed; còn một warning deprecation từ Surya/Pydantic.

## Final Excel Role, Pre-content Boundary và Decision Tail

- `segment_pre_content()` giữ toàn bộ line trước stop heading ở bất kỳ trang nào; `max_fallback_pages` chỉ áp dụng khi không tìm thấy marker.
- Defendant region chỉ bắt đầu sau intro `Đối/Đồi với (các) bị cáo:` hoặc inline identity đủ mạnh. Numbered trial-panel line không còn là fallback defendant; block overlap metadata/trial panel/participant bị loại và có lý do debug.
- Metadata parser kiểm tra độc lập các anchor cùng dòng. Số thụ lý lấy token ngay sau anchor; ngày thụ lý chỉ được parse sau token đó và để trống với warning nếu thiếu số.
- `FINAL_EXCEL` vẫn đúng 11 cột nhưng chỉ nhận sáu primary roles canonical. Guardian, representative, defense/protection, witness và support roles nằm trong sheet thứ hai `NGUOI_THAM_GIA_KHAC`; court procedural roles không đi vào hai sheet user-facing.
- Dedupe final row dùng `case_id + normalized_full_name + normalized_procedural_role`; cùng tên khác role vẫn giữ hai dòng.
- Criminal row không còn fallback `QUAN HỆ PHÁP LUẬT = Hình sự`. Khi chưa có explicit charge, field để trống và `GHI CHÚ` có `Chưa trích xuất tội danh`.
- Command `ocr-decision-tail` dùng Surya, scan ngược theo batch cấu hình, dừng khi gặp heading quyết định, ghi cache schema riêng và không thay đổi OCR cache cũ. `compare-pre-content --decision-tail-cache-dir` parse explicit verdict phrases rồi lặp `case_charges` trên các final rows.
- HTML/workbook review đặt `FINAL EXCEL PREVIEW` rồi `NGƯỜI THAM GIA KHÁC` trước debug; debug có defendant region/rejection, metadata evidence, role policy và charge evidence.
- Toàn bộ fixture/test do Codex dùng là synthetic. Codex không mở PDF/cache/output thật, không gọi Surya/LLM/Docker/cloud và không commit/push.
- Verification: 226/226 test passed; compile, snapshot, repo/architecture guardrails, static Surya backend và extractor configuration checks đều passed. Chỉ có một warning deprecation từ dependency Surya/Pydantic.

## Final Excel Schema First Realignment

- `FINAL_EXCEL` là output workbook chính và luôn là sheet đầu tiên; schema canonical nằm tại `final_excel_schema.py` với đúng 11 cột của Project Owner.
- `final_excel_builder.py` tạo một dòng cho mỗi entity có primary role, lặp case metadata/judge và chỉ ghi đúng 11 cột. Support participants nằm ở sheet riêng; dữ liệu thiếu để trống, lý do nằm trong `GHI CHÚ` và không có JSON/debug field trong final sheet.
- Rule-anchor metadata bổ sung `case_acceptance_date` và `legal_relationship`; entity bổ sung `cccd`. Ngày thụ lý chỉ lấy từ line `thụ lý số ... ngày ...`; CCCD/CMND chỉ lấy 9-12 chữ số liên tục sau label định danh.
- `rule_anchor_only` và `rule_then_llm_per_block` đều tạo `FINAL_EXCEL`; khi compare nhiều strategy, final sheet dùng primary strategy, còn mọi strategy vẫn được giữ trong debug sheets.
- `CASES`, `DEFENDANTS`, `PARTICIPANTS`, `TRIAL_PANEL`, `ANCHOR_*`, `LLM_STATUS`, `RAW_JSON` và các sheet khác chỉ là debug phụ. HTML đặt `FINAL EXCEL PREVIEW` 11 cột trước debug sections.
- Audit không phát hiện schema final cạnh tranh: `EXCEL_HEADERS`, template và field docs cũ đã dùng đúng cùng 11 tên cột. Contract sheet `DATA`/`Trich xuat` cũ được thay bằng `FINAL_EXCEL`.
- Codex chỉ chạy tests synthetic; không đọc PDF/OCR cache/Excel/output thật và không gọi LLM, Surya, Docker hay cloud.
- Verification: 199/199 test passed; compile, snapshot, repo/architecture guardrails, static Surya backend và Local LLM config checks đều passed.

## Bản Vá Rule Anchor Metadata + Participant Case001

- Metadata parser không còn giới hạn cứng 100 dòng trước entity đầu tiên và chỉ lấy token số ngay sau anchor, nên `case_acceptance_number`, `trial_decision_number`, `postponement_decision_number` không nuốt phần `ngày`/`theo` phía sau.
- Trial panel giữ newline của juror trước khi split, vì vậy mỗi juror được xuất thành một dòng `TRIAL_PANEL` riêng.
- Participant splitter nhận numbering phân cấp như `7.1.`, ưu tiên role dài trước `Bị hại`, tạo block mới cho inline role có person và chỉ gắn address/detail vào block gần nhất.
- Defendant parser normalize `tam giam`, xử lý `Vợ con`, nối continuation address bắt đầu bằng `số` và bỏ prefix `hiện tại:`.
- `standalone_page_number_removed_from_defendant_blocks` vẫn xuất trong `ANCHOR_WARNINGS` nhưng là informational và không tự bật `CASES.needs_review`.
- Codex chỉ dùng OCR-line/OCR-cache synthetic. Project Owner vẫn phải chạy lại `case_001` trên VM để xác nhận output thật; Codex không đọc PDF/cache/output thật và không gọi LLM, Surya, Docker hay cloud.

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

FINAL EXCEL SCHEMA FIRST REALIGNMENT.

Task này realign extraction/export theo 11 cột final và giữ các sheet kỹ thuật làm debug phụ. Không thay Surya OCR runtime, không chạy dữ liệu thật và không gọi model thật.

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
- Tại thời điểm Phase 1E, giữ nguyên 11 domain headers và hai workbook contract khi đó: draft records dùng `DATA` + `RUN_SUMMARY`, typed `ExtractionResult` dùng `Trich xuat`. Quyết định lịch sử này đã được D-043 thay thế bằng sheet đầu `FINAL_EXCEL`.
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

Project Owner rerun extraction từ OCR cache cũ cho đúng 1 case bằng `rule_anchor_only`, không OCR và không bật LLM. Review cả `FINAL_EXCEL` lẫn `NGUOI_THAM_GIA_KHAC`; chỉ khi boundary/role/metadata đạt mới chạy `ocr-decision-tail` cho case đó, rồi rerun extraction với tail cache. Không tăng lên 3/9 PDF trước khi case đầu được chấp nhận.
