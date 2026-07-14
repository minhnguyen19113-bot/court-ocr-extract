# MLOps Plan

Last updated: 2026-07-14

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

- Main adapter đã pin `surya-ocr==0.20.0`; guard fail mọi version khác trước runtime. Surya 2/0.21.x cần phase/runtime governance riêng.
- Local LLM runtime mặc định đã xác nhận là `Qwen/Qwen2.5-3B-Instruct`, vLLM OpenAI-compatible, context 8192/output 1024 trên RTX 5060 Ti 16GB. Qwen2.5-7B full bf16 không là default vì thiếu KV cache.
- Manifest/report phải giữ context window, input token estimate, output budget, chunk name, truncation, request status và error type; không lưu prompt/OCR text trong log an toàn.
- Pre-content baseline version phải ghi strategy (`rule_anchor_only`, `llm_per_block`, `rule_then_llm_per_block`), anchor/parser/prompt version và validator warning taxonomy. Per-block runtime cap là 6000 ký tự/512 output token dù global Local LLM budget lớn hơn.
- Ghi model/runtime version vào run manifest.
- Khi prompt/schema đổi, cập nhật `docs/CHANGELOG_AI.md` và evaluation baseline.
- Không thay default sang cloud model nếu không có explicit opt-in decision.

## Benchmark policy

- Surya OCR + deterministic rule anchors/block parser + optional Local LLM repair theo block là main candidate.
- Local VLM là benchmark path, phải dùng cùng validation/evidence/QA rule.
- Benchmark chỉ có ý nghĩa khi chạy trên gold/pilot dataset do Project Owner quản trị ngoài Codex.

TOOLKIT-1 prediction manifest đã chuẩn bị các field `ocr_backend_version`, `model_name`, `prompt_version`, `run_id` để so sánh run. Gold split (`pilot`/`validation`/`test`) phải được Project Owner quản trị ổn định ngoài Git.

Mọi baseline metric cần gắn với manifest version/hash và runtime version. Synthetic baseline chỉ kiểm code contract, không được dùng làm model quality baseline.

## Rollback policy

- Mọi thay đổi runtime lớn cần commit riêng.
- Giữ config default local-first.
- Nếu Surya API thay đổi, adapter phải fail rõ thay vì fallback sang Tesseract/cloud.
- Nếu local LLM lỗi JSON, extraction phải báo warning/fail rõ, không tự ghi Excel như thành công.
