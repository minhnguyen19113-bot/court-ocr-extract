# MLOps Plan

Last updated: 2026-07-08

## Mục tiêu

Quản trị version, runtime, benchmark, và rollback cho Surya OCR, local LLM, và local VLM mà không đưa dữ liệu thật vào repo.

## Thành phần cần quản trị

| Thành phần | Cần ghi nhận |
| --- | --- |
| Surya OCR | package version, API adapter kind, model cache path ngoài Git. |
| Local LLM | provider, model name, base URL, temperature, max tokens, JSON mode. |
| Local VLM | provider, model name, render DPI, max pages, benchmark status. |
| Prompt | prompt file path, version/change date, required schema. |
| Schema | extraction schema version, Excel column version, QA warning taxonomy. |

## Versioning đề xuất

- Pin hoặc document `surya-ocr` version sau khi Ezycloudx check thật.
- Ghi model/runtime version vào run manifest.
- Khi prompt/schema đổi, cập nhật `docs/CHANGELOG_AI.md` và evaluation baseline.
- Không thay default sang cloud model nếu không có explicit opt-in decision.

## Benchmark policy

- Surya OCR + local LLM là main candidate.
- Local VLM là benchmark path, phải dùng cùng validation/evidence/QA rule.
- Benchmark chỉ có ý nghĩa khi chạy trên gold/pilot dataset do Project Owner quản trị ngoài Codex.

## Rollback policy

- Mọi thay đổi runtime lớn cần commit riêng.
- Giữ config default local-first.
- Nếu Surya API thay đổi, adapter phải fail rõ thay vì fallback sang Tesseract/cloud.
- Nếu local LLM lỗi JSON, extraction phải báo warning/fail rõ, không tự ghi Excel như thành công.
