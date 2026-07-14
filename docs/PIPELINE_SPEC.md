# Pipeline Spec

## Local LLM context budget và chunked extraction

Local LLM mặc định dùng `Qwen/Qwen2.5-3B-Instruct`, context 8192, output 1024, input tối đa 6000 token/22000 ký tự và safety margin 512. OpenAI-compatible payload luôn có `temperature=0` và `max_tokens>0`. Adapter ước lượng tiếng Việt bằng `ceil(chars/3.2)`, trim `preserve_head` trước HTTP và fail `llm_context_budget_exceeded` nếu vẫn không an toàn.

Pre-content không được gửi nguyên khối. Extractor chia request thành document metadata, trial panel, từng defendant và participants; mỗi chunk có status/budget/error riêng. Kết quả thành công được merge và de-duplicate; một chunk lỗi không xóa chunk khác. Hybrid giữ rule output khi LLM lỗi. Nếu mọi chunk `llm_only` lỗi, status là `llm_only_failed`, `result_valid=false`; schema null/rỗng không được coi là model output hợp lệ.

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


## Pre-content extraction A/B

Nhánh thử nghiệm nhận filtered OCR lines, route document và cắt phần trước `NỘI DUNG VỤ ÁN`. Mode A chạy rule-based trước rồi Local LLM chỉ fill/repair field chưa giải quyết; mode B chạy Local LLM trên cùng pre-content input. Cả hai phải giữ evidence/warnings và không dùng nội dung sau heading. Rule-only không phải output quyết định cuối.

## Stamp suppression contract

Khi dung preprocessed input, tao `stamp_suppression_mask` va `ocr_input_stamp_suppressed`; post-OCR filter giu raw lines, filtered lines va excluded lines co `reason`, `stamp_overlap_ratio`, `dark_text_overlap_ratio`. Khong hard-code noi dung dau moc va khong fallback sang OCR backend khac.

Last updated: 2026-07-10

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

Excel should include or prepare for:

- `SOURCE_CASE_ID`
- `SOURCE_PAGE`
- `SOURCE_LINE_IDS`
- `OCR_CONFIDENCE`
- `EXTRACTION_CONFIDENCE`
- `EVIDENCE`
- `WARNINGS`
- `NEEDS_REVIEW`

## Fallback Rules

- No silent OCR fallback.
- No silent extractor fallback.
- Fallbacks must be explicit, logged, and visible in QA/debug output.
