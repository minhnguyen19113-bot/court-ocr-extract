# Debug Output Spec

## Surya runtime artifacts

- `surya_runtime_preflight.json`: kết quả Docker/Surya API trước OCR; có `gpu_container.checked` và command output tail khi GPU smoke được yêu cầu.
- `<case>/surya_runtime_diagnostics.json`: journal có `last_stage`, stage history, Docker binary, startup timeout, container spawn check, warning và lỗi cuối.
- Stage chuẩn: `stage_01_render_pdf`, `stage_02_preprocess`, `stage_03_resolve_docker`, `stage_04_patch_surya_resolver`, `stage_05_import_surya`, `stage_06_create_predictor`, `stage_07_predictor_call`, `stage_08_parse_predictions`.
- Log terminal chỉ nêu trạng thái runtime, không in OCR text hoặc dữ liệu nhạy cảm.

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
## Stamp object erase artifacts

- `red_mask` là mask pixel-level, chỉ thể hiện các pixel đỏ đã detect và không bảo đảm xóa sạch residual xám/low-saturation.
- `stamp_suppression_mask` là mask morphology ở mức nét.
- `stamp_object_mask` gộp connected components thành vùng object mở rộng để phủ residual quanh dấu mộc.
- `stamp_object_erased` là kết quả sau object-level erase; `ocr_input_stamp_suppressed` là ảnh cuối đưa vào OCR.
- `black_text_protection_mask` chỉ dùng bảo vệ chữ thật và tính overlap, không phải output cuối.
- Review phải hiển thị object count, erase mode, mask ratio, dark-text overlap và warnings.
## Final preprocess candidate selection

- `object_seed_mask` là union của `red_mask` và `stamp_suppression_mask`.
- `final_preprocessed_candidate` giữ output preprocess trước stamp selection; `final_preprocessed` là best safe candidate đã chọn.
- `candidate_scores` phải có stamp residual, text preservation, foreground loss, dark-pixel explosion, blank và entropy metrics.
- Debug UI phải đặt `stamp_object_erased` cạnh `final_preprocessed` và hiển thị `final_selected_stage`, `final_selection_reason`, `ocr_input_source_stage`.
- OCR input phải giống final selected candidate, không quay lại candidate residual cao hơn.
