# Visual QA Guide

Visual QA dùng để kiểm tra PDF thật bằng mắt trước khi tin Excel. Dữ liệu giả/fixture không được dùng để kết luận chất lượng OCR hoặc extraction.

## Synthetic Smoke Output

Trước khi chạy pilot thật, có thể tạo output debug an toàn từ fixture không thật:

```powershell
python -m scripts.smoke_synthetic_debug
```

Reviewer có thể mở:

- `outputs\debug_visual\synthetic_smoke\index.html`
- `outputs\debug_visual\synthetic_smoke\manifest.json`
- `outputs\excel\synthetic_smoke.xlsx`
- `outputs\qa\synthetic_smoke_report.json`

Synthetic smoke chỉ chứng minh các module tạo được artifact kiểm tra thủ công; không thay thế pilot PDF thật.

## Render

Kiểm tra ảnh không xoay, không cắt mép, chữ đủ rõ và dấu mộc không che vùng quan trọng.

```powershell
python -m court_ocr_extract.cli debug-render --input data\raw_pdfs\uploads --limit 20 --review-sample-size 5 --pages 1-3 --output outputs\debug_visual --open
```

## Preprocess

So sánh before/after. Không bật preprocess mạnh nếu mất nét hoặc mất dấu tiếng Việt.

```powershell
python -m court_ocr_extract.cli debug-preprocess --input data\raw_pdfs\uploads --limit 20 --review-sample-size 5 --pages 1-3 --output outputs\debug_visual --open
```

## Red Seal

Không bật mặc định. Chỉ bật sau khi xem nhiều PDF thật và thấy không làm mất chữ.

```powershell
python -m court_ocr_extract.cli debug-red-seal --input data\raw_pdfs\uploads --limit 20 --review-sample-size 5 --pages 1-3 --output outputs\debug_visual --open
```

## OCR Review

Ảnh ở trái, text OCR ở phải. Nếu backend không có bbox thì báo rõ là không hỗ trợ bbox.

```powershell
python -m court_ocr_extract.cli debug-ocr-review --input data\raw_pdfs\uploads --limit 20 --review-sample-size 5 --pages 1-3 --ocr-backend tesseract --output outputs\debug_visual --open
```

## Extraction Preview

Bên trái phải giống cột Excel. Bên phải phải có evidence hoặc trạng thái cần review.

```powershell
python -m court_ocr_extract.cli preview-extraction --ocr-cache outputs\ocr_cache --review-sample-size 5 --review-mode mixed --extractor local_llm --output outputs\debug_visual --open
```
