# Debug Output Spec

Last updated: 2026-07-10

Debug output is mandatory for reviewer trust. It must be safe by default and should never print or expose full real OCR text in logs.

## Output Layout

Target synthetic-safe layout pattern:

```text
outputs/debug_visual/<run_id>/
  index.html
  manifest.json
  cases/
    <case_id>/
      render.html
      preprocess.html
      ocr.html
      extraction.html
      qa.html
```

Codex must not inspect real folders under `outputs/`. This layout is a target spec only.

## Index Page

Must show:

- run metadata
- case list
- step status
- rows needing review
- warning counts
- links to per-case pages

## Render View

Must show:

- page grid
- rendered page image
- page size/DPI
- warnings for blank, rotated, cropped, or unreadable pages

Default page scope:

- `debug-render` mặc định render toàn bộ trang khi không truyền `--pages`.
- Muốn giới hạn thì truyền rõ page range, ví dụ `--pages 1-3`.

## Preprocess View

Must show:

- original, `red_mask`, `black_text_protection_mask`, `seal_removed`, `text_enhanced`, final và before/after images
- red mask method/components, removal mode/residual/overlap, text-enhance mode, deskew metadata và before/after foreground metrics
- non-overwrite guarantee
- warnings và fallback source khi transform bị bỏ qua hoặc blank guard kích hoạt

Safety contract:

- Red seal detection kết hợp HSV + Lab + RGB trên ảnh màu; protection mask giữ nét tối khi seal overlap text.
- Default là `red_removal_mode=neutralize` và `text_enhance=light`; `white_fill`/`strong` chỉ dành cho thử nghiệm.
- Thứ tự: red removal -> background normalization -> text enhancement -> optional safe deskew -> final guard/fallback.
- Red/text guard phải ghi `red_removal_guard_triggered`, `text_enhance_guard_triggered`, `dark_pixel_explosion` hoặc `foreground_loss_too_high` khi áp dụng.
- `--deskew off` là mặc định; `safe` chỉ xoay trong ngưỡng 0.3-5 độ khi confidence đủ cao và không có crop/multi-column risk.
- Nếu output mất quá nhiều foreground hoặc gần trắng, dùng original/previous safe stage và ghi `preprocess_blank_guard_triggered` cùng `foreground_loss_too_high`.
- Mỗi page có `metadata.json`; Project Owner phải review `debug-preprocess` trước khi chạy OCR thật.

Default page scope:

- `debug-preprocess` mặc định render/preprocess toàn bộ trang khi không truyền `--pages`.
- Muốn giới hạn thì truyền rõ page range, ví dụ `--pages 1-3`.

## OCR View

Must show:

- original image
- bbox overlay
- line table with `line_id`, bbox, reading order, text, confidence, warnings
- low-confidence filter
- `ocr_input_source` và preprocess options khi input là preprocessed
- link/ảnh `page_NNN_ocr_input.png`, phân biệt với rendered original và final preprocess

Layout artifact Surya của Phase 2A:

```text
<run_dir>/<case_id>/ocr_surya/
  page_001_original.png
  page_001_ocr_input.png
  page_001_bbox.png
  page_001_lines.json
  page_001_text.md
  combined_text.md
  manifest.json
  ocr_review.html
  index.html
```

Review HTML cần hiển thị original page image, bbox overlay, line table, warnings, và link đến page text/line JSON.

Khi bật `--use-preprocessed`, case directory còn có `preprocess/page_NNN_{original,red_mask,black_text_protection_mask,seal_removed,text_enhanced,final_preprocessed}.png` và metadata JSON. OCR manifest phải ghi Mode 3 đã truyền và `ocr_input_source=preprocessed`.

Full-document OCR review:

- `debug-ocr-review --full-document` xử lý toàn bộ trang của PDF đã chọn.
- Khi bật `--full-document`, backend nhận `max_pages=None` và `stop_marker=""`, nên marker `NỘI DUNG VỤ ÁN` không được làm dừng/truncate OCR review.
- Nếu cần giới hạn OCR review theo số trang, dùng `--max-pages <n>` khi không bật `--full-document`.

## VLM View

Must show:

- page image
- model output
- parsed JSON status
- extracted fields
- evidence and hallucination warnings

## Extraction View

Must show:

- field/value/evidence table
- source page and line IDs
- warning code
- link to OCR line or bbox when available

## QA View

Must show:

- row count
- needs-review count
- missing evidence
- evidence mismatch
- invalid date/ID
- low OCR confidence
- duplicate participant warnings

## Privacy

- Do not include full real OCR text in terminal logs.
- Do not include sensitive filenames in logs.
- Debug outputs from real data are derived sensitive artifacts and must stay out of Git.
## OCR stamp review

Moi page co the co stamp suppression mask, OCR input stamp suppressed, raw/filtered/excluded lines JSON, raw/text markdown va metadata. OCR review HTML hien thi mode, line counts, excluded reason va overlap de kiem false removal.
