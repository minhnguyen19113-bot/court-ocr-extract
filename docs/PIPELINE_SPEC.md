# Pipeline Spec

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
