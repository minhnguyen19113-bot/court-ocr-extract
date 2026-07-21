# Pipeline Spec

## Pre-content Boundary và Defendant Region Contract

`segment_pre_content()` tìm stop heading trên toàn bộ filtered OCR lines trước. Nếu có heading, output là mọi line nằm strictly trước heading, không phụ thuộc `max_fallback_pages`; nếu không có heading mới giữ các line trong fallback page limit và ghi `pre_content_stop_heading_not_found_using_page_limit`.

Defendant region cần intro normalized `Đối/Đồi với (các) bị cáo:` ở bất kỳ vị trí nào trong line. Metadata prefix trước intro vẫn thuộc metadata; region bắt đầu ở line kế tiếp, trừ inline value có strong identity evidence. Không được fallback từ toàn văn bản sang numbered line đầu tiên. Defendant block phải có full name và explicit label hoặc identity profile; line IDs overlap metadata-only/trial-panel/participant region bị reject với `defendant_block_overlaps_forbidden_region`.

Metadata anchors `thụ lý số`, quyết định đưa vụ án ra xét xử và quyết định hoãn được kiểm tra bằng các nhánh độc lập. Acceptance number là token ngay sau anchor; acceptance date chỉ parse từ tail sau token này. Thiếu number thì date để trống và có `acceptance_date_blocked_missing_acceptance_number`.

## Final Role và Other Participants Contract

`FINAL_EXCEL` có đúng 14 cột và chỉ nhận `Bị cáo`, `Bị hại`, `Pháp nhân thương mại bị cáo` cùng alias chính xác trong `final_excel_role_policy.py`. Không suy role từ cụm từ tự do.

Support roles được giữ trong sheet thứ hai `NGUOI_THAM_GIA_KHAC`; court procedural roles không phải final entity. Dedupe dùng case + normalized full name + normalized role. Multi-person support block chỉ split khi role cho phép, có nhiều honorific/name starts và không có address/organization marker; các entity con giữ cùng evidence IDs, represented person và relationship note.

Criminal defendant row không có specific charge map phải để `QUAN HỆ PHÁP LUẬT` trống và thêm `Chưa gắn chắc tội danh với bị cáo từ phần Quyết định`. Primary role không phải bị cáo dùng toàn bộ `case_charges`; nếu chưa có charge thì để trống và thêm `Chưa trích xuất được tội danh từ phần Quyết định`. `Hình sự` chỉ được dùng trong `LOẠI ÁN`.

## Source-region Contract

Production chỉ chấp nhận `front_pre_content` và `decision_tail`. Các field loại án, thụ lý, role, identity, địa chỉ và chủ tọa là front-only. Tội danh và các field tuyên án là decision-only. Nội dung từ `NỘI DUNG VỤ ÁN`, tranh luận và `NHẬN ĐỊNH CỦA TÒA ÁN` thuộc `middle_excluded`; không được dùng để fill final field hoặc fallback khi hai vùng hợp lệ thiếu dữ liệu.

Workflow là forward scan đến marker và reverse scan có giới hạn từ cuối đến decision heading. `scan_decision_tail()` bắt buộc nhận `max_scan_pages` dương, hữu hạn; thiếu guard phải fail rõ thay vì OCR toàn văn bản. Hết guard mà không thấy heading thì status là `heading_not_found`, relationship để trống và row có ghi chú ngắn tương ứng.

## Decision Tail và Charge Contract

`ocr-decision-tail` chỉ dùng Surya và tái sử dụng predictor runner. Stage bắt đầu từ cuối PDF, OCR theo batch page tăng dần trong từng batch nhưng các batch đi ngược về đầu, rồi dừng ở batch đầu tiên có normalized decision heading. Output chỉ giữ heading đến hết tài liệu và ghi cache riêng `DecisionTailRecord`; không sửa OCR cache pre-content cũ.

`decision_tail_batch_size`, `decision_tail_max_scan_pages` và `decision_heading_variants` là cấu hình. Hết guard mà không có heading phải ghi `decision_heading_not_found_within_scan_limit`. Parser chỉ nhận explicit `Tuyên ... phạm tội`, `Xử phạt ... về tội` hoặc `Bị cáo ... phạm tội`; hỗ trợ quoted/unquoted charge có điểm dừng an toàn. Parser không suy từ điều luật, hành vi, cáo trạng, nhận định, tên file hoặc document type.

`case_charges` unique theo thứ tự xuất hiện. `defendant_charge_map` dùng defendant `entity_id`; matching lần lượt exact normalized name, exact name sau honorific và unique fuzzy match qua `DECISION_NAME_MATCH_MIN_SCORE`/`DECISION_NAME_MATCH_AMBIGUITY_GAP`. Ambiguous hoặc collective không xác định chắc chỉ ghi warning, không gán charge và không tạo defendant mới. Dòng bị cáo chỉ dùng charge map riêng; primary role khác dùng `; `.join(case charges). Cùng người khác role vẫn là hai dòng độc lập.

## Final Excel schema contract

`FINAL_EXCEL` là output nghiệp vụ chính và phải là sheet đầu tiên của mọi final workbook. Schema duy nhất là `FINAL_EXCEL_COLUMNS` trong `src/court_ocr_extract/final_excel_schema.py`, đúng 14 cột và đúng thứ tự Project Owner duyệt. `HÌNH PHẠT` đứng sau `QUAN HỆ PHÁP LUẬT`; source/evidence/confidence/strategy/JSON chỉ nằm trong debug sheets.

`final_excel_builder.py` nhận rule-anchor output và tạo một dòng cho mỗi entity có primary role. Case type, số/ngày thụ lý, explicit legal relationship và chủ tọa được lặp trên từng dòng. Năm sinh chỉ giữ năm; CCCD/CMND chỉ nhận 9-12 chữ số liên tục sau label; defendant address ưu tiên current rồi permanent. Field thiếu để trống và thêm lý do vào `GHI CHÚ`; không suy đoán từ tên, địa chỉ hoặc số quyết định.

Khi compare nhiều strategy, `FINAL_EXCEL` dùng primary strategy để tránh nhân đôi các dòng không có strategy column. `rule_anchor_only` hoặc `rule_then_llm_per_block` khi chạy riêng đều phải tạo final sheet. `CASES`, `DEFENDANTS`, `PARTICIPANTS`, `TRIAL_PANEL`, `ANCHOR_*`, `LLM_STATUS`, `RAW_JSON` và các sheet trace khác nằm sau và chỉ phục vụ debug.

## Local LLM context budget và chunked extraction

Local LLM mặc định dùng `Qwen/Qwen2.5-3B-Instruct`, context 8192, output 1024, input tối đa 6000 token/22000 ký tự và safety margin 512. OpenAI-compatible payload luôn có `temperature=0` và `max_tokens>0`. Adapter ước lượng tiếng Việt bằng `ceil(chars/3.2)`, trim `preserve_head` trước HTTP và fail `llm_context_budget_exceeded` nếu vẫn không an toàn.

Pre-content không được gửi nguyên khối. Main baseline cắt deterministic metadata lines, trial-panel lines, từng defendant block và participant block. Metadata/trial panel được rule parser xử lý; Local LLM chỉ nhận một entity block cần repair, tổng input tối đa 6000 ký tự và output tối đa 512 token. Một block lỗi không xóa rule output hoặc block thành công khác. Strategy không chạy phải có status rõ; schema null/rỗng không được coi là model output hợp lệ.

`compare-pre-content` preflight `/models` và chat nhỏ trước vòng case. `--require-llm` fail-fast, `--allow-llm-failure` ghi strategy không chạy, `--skip-llm-preflight` là opt-out rõ ràng.

## Marker detection và page-level early-stop

Pre-content OCR mặc định chạy `render page/batch -> preprocess -> predictor call -> normalize raw/filtered lines -> marker detection -> cache/debug -> break`. Predictor Surya được tạo một lần cho mỗi PDF và tái sử dụng; `ocr_page_batch_size=1` là default. `--full-document` đặt marker rỗng và giữ bulk/full-document behavior.

Detector dùng NFKC/NFKD, lowercase, bỏ dấu, punctuation/whitespace collapse và chịu được OCR spacing/split-line. High/medium confidence mới được dừng; `noi dung` đơn lẻ là low-confidence candidate và không dừng. Cache giữ raw review lines nhưng `result.text`/`metadata.text_before_marker` được trim trước marker. Không tìm thấy marker thì OCR hết selected file và ghi warning.

## Surya runtime preflight và no-hang contract

Hai CLI `debug-ocr-review` và `ocr` phải chạy preflight trước discover/render/predictor khi backend là Surya. Preflight kiểm Docker binary đã resolve, `docker --version`, `docker info`, Surya version và API; failure phải dừng trước inference. GPU container smoke không chạy mặc định, nhưng khi bật phải thực thi thật với timeout và trả `checked=true`.

Surya adapter ghi các stage từ `stage_01_render_pdf` đến `stage_08_parse_predictions` vào `surya_runtime_diagnostics.json`. Constructor/predictor call bị giới hạn bởi `SURYA_STARTUP_TIMEOUT_SECONDS` hoặc `--surya-startup-timeout-seconds`; timeout raise `SuryaRuntimeError`, giữ `last_stage`, Docker diagnostics và hành động đề xuất. Không fallback sang OCR backend khác một cách âm thầm.

## Final preprocess selection contract

Object detection dùng `red_mask OR stamp_suppression_mask`, horizontal close và light dilation trước component filtering để giữ dấu mộc ngang nhiều nét rời. Sau erase, pipeline chấm điểm `seal_removed`, `text_enhanced`, `final_preprocessed_candidate`, mask result và `stamp_object_erased`. Candidate có stamp residual thấp nhất chỉ được chọn khi text preservation an toàn. Text enhancement có residual cao hơn hoặc làm mất foreground không được chọn; OCR dùng đúng selected stage. Post-OCR stamp filter vẫn bắt buộc.


## Component-level stamp erase

Stamp cleanup chạy `red_mask -> connected components -> grouped/expanded stamp object -> dark-text overlap check -> object erase -> OCR input`. Nếu overlap dưới ngưỡng an toàn, `component_white_fill`, `component_inpaint` hoặc `local_background` có thể xử lý toàn object. Nếu overlap cao, pipeline không white-fill object, ghi `stamp_object_overlaps_dark_text`, fallback mask-level suppression và giữ post-OCR stamp filter.


## Pre-content rule anchor baseline

Nhánh chính nhận filtered OCR lines, route document và chỉ dùng phần trước `NỘI DUNG VỤ ÁN`. `rule_anchor_only` parse deterministic toàn bộ; `llm_per_block` dùng rule cho metadata/panel và model cho từng entity block; `rule_then_llm_per_block` chỉ gọi model khi entity thiếu field cốt lõi hoặc validator báo lỗi. Mọi block giữ `line_ids`, raw text, split reason, warnings và evidence. `hybrid_rule_llm`/`llm_only` vẫn có thể gọi rõ để benchmark legacy nhưng không phải default.

Metadata case-number fields chỉ chứa token `number/year/suffix` ngay sau anchor và metadata region kéo dài đến entity đầu tiên, không có line cap tùy ý. Participant line có numbering phân cấp hoặc inline role/person tạo block mới; role được match longest-first và address/detail chỉ thuộc block gần nhất. Juror newline tạo nhiều row. Known standalone page-number removal warning được export nhưng không tự kích hoạt case review.

## Stamp suppression contract

Khi dung preprocessed input, tao `stamp_suppression_mask` va `ocr_input_stamp_suppressed`; post-OCR filter giu raw lines, filtered lines va excluded lines co `reason`, `stamp_overlap_ratio`, `dark_text_overlap_ratio`. Khong hard-code noi dung dau moc va khong fallback sang OCR backend khac.

Last updated: 2026-07-14

This is the target rebuild spec. Phase 1B cleaned defaults to match this spec but did not implement real runtime changes.

## Render

Terminal summary must include:

- `case_id`
- page count
- DPI
- output paths
- warnings for blank, rotated, or cropped pages

Debug UI must include:

- page render grid
- page image
- page size/DPI metadata

## Preprocess / Enhance

Preprocess là optional và phải theo thứ tự an toàn:

```text
original color -> HSV + Lab + RGB red mask -> dark-text protection
-> neutralize/inpaint/white-fill -> background normalization -> black-text enhancement
-> optional confidence-gated deskew -> blank/foreground guard -> final hoặc safe fallback
```

- Default là `preprocess_profile=conservative`, `deskew=off`, `red_seal_removal=on`, `red_removal_mode=neutralize`, `text_enhance=light`.
- Red seal không được detect sau grayscale; ratio quá cao phải skip removal và warning.
- `inpaint` là mode so sánh khi neutralize còn residual; `white_fill` và text `strong` chỉ dùng review.
- Text enhancement phải chạy sau red removal để không biến red residual thành nét đen giả; dark-pixel explosion phải fallback.
- `deskew=safe` chỉ xoay góc 0.3-5 độ khi đủ horizontal evidence, không gần mép và không có layout hai cột mơ hồ.
- Rotation dùng expanded canvas để tránh cắt góc. `force` chỉ dành cho thử nghiệm có review.
- Nếu after gần blank hoặc mất quá nhiều foreground/dark pixels, fallback về original hoặc `seal_removed` stage.

Terminal summary must include:

- before image path
- after image path
- transforms applied
- warnings when transforms may remove text or accents

Debug UI must include:

- original, red mask, black-text protection, seal-removed, text-enhanced, final và comparison
- red residual/overlap, text enhancement, deskew, foreground/brightness/entropy metrics và warnings
- clear indication that original images are not overwritten

## Surya OCR

Runtime contract: main adapter chỉ hỗ trợ `surya-ocr==0.20.0`. Version guard phải chạy trước import/API detection; Surya 2/0.21.x và Docker/vLLM backend không thuộc phase hiện tại.

OCR input routing:

- Không có `--use-preprocessed`: Surya dùng rendered original như behavior cũ và metadata ghi `ocr_input_source=rendered_original`.
- Có `--use-preprocessed`: backend render, preprocess từng page, rồi chỉ truyền `page_NNN_final_preprocessed.png` vào Surya; metadata ghi source và toàn bộ options.
- `debug-preprocess` chỉ tạo review preprocess độc lập, không tự thay đổi OCR input.
- Mode hiện được Project Owner chọn cho pilot OCR: `deskew=off`, red removal `inpaint`, text enhance `medium`, profile `balanced`, red-seal removal bật.
- Preprocess failure phải tạo final safe copy, ghi warning và vẫn dùng named final path; không âm thầm chuyển call sang rendered path.

Terminal summary must include:

- pages processed
- total OCR lines
- low-confidence line count
- bbox overlay output path
- OCR cache output path
- short safe preview only; never full real OCR text

Debug UI must include:

- original page image
- bbox overlay image
- `line_id`
- bbox
- per-line text
- confidence if available
- reading order
- low-confidence filter

Ghi chú triển khai Phase 2A:

- `SuryaOCRBackend` chuẩn hóa line output vào `OCRPage.lines`.
- Line record dùng `line_id`, `page_number`, `text`, `bbox`, `confidence`, `reading_order`, và `warnings`.
- Nếu Surya không trả về reading order, line được sort từ trên xuống dưới rồi trái sang phải bằng bbox và ghi `reading_order_fallback_used`.
- Nếu Surya không trả về confidence, `confidence` giữ giá trị `null`.
- Debug artifacts chỉ được ghi khi bật debug visual/work directory.
- Khi dùng preprocessed input, giữ cả `preprocess/` artifacts và `ocr_surya/page_NNN_ocr_input.png` để reviewer đối chiếu.
- Test synthetic/mocking chỉ bao phủ contract; chất lượng thật vẫn cần Project Owner validate.

## VLM End-to-End

Terminal summary must include:

- pages processed
- model name
- JSON valid yes/no
- extraction warnings
- debug output path
- no full PII

Debug UI must include:

- page image
- VLM output
- extracted fields
- evidence
- warning and hallucination checks

## Extraction

Canonical implementation sau Phase 1F:

- Orchestrator: `src/court_ocr_extract/extraction_pipeline.py`.
- Backend package/interface: `src/court_ocr_extract/extractors/` và `extractors/base.py`.
- Local LLM backend: `extractors/local_llm_extractor.py`.
- Rule support helper: `extractors/rule_support.py`; chỉ dùng khi được chọn rõ hoặc làm support/validation.
- `scripts.check_extractor` là static configuration check; không xác nhận endpoint/model quality.

Terminal summary must include:

- JSON valid status
- participant/row count
- missing evidence count
- evidence mismatch count
- rows needing review
- output paths

Debug UI must include:

- field/value table
- evidence
- source page/line
- warning code
- link to bbox/page when available

## Excel / QA

Terminal summary must include:

- total rows
- rows needing review
- invalid dates/IDs
- missing evidence count
- evidence mismatch count
- low OCR confidence count
- output Excel path
- output QA report path

Sheet `FINAL_EXCEL` chỉ có 14 cột canonical. `SOURCE_CASE_ID`, source page/line IDs, OCR/extraction confidence, evidence, warnings kỹ thuật và `NEEDS_REVIEW` phải nằm trong debug sheets/QA report, không được thêm vào final columns.

## Fallback Rules

- No silent OCR fallback.
- No silent extractor fallback.
- Fallbacks must be explicit, logged, and visible in QA/debug output.
