# Evaluation Plan

Last updated: 2026-07-10

## Mục tiêu

Đánh giá chất lượng phải tách rõ contract tests trong Codex và real-data evaluation do Project Owner chạy ngoài Codex.

## Tầng đánh giá

| Tầng | Dữ liệu | Owner | Mục tiêu |
| --- | --- | --- | --- |
| Contract tests | Synthetic fixtures | Codex | Schema/control-flow không vỡ. |
| Synthetic smoke | Non-real generated artifacts | Codex | Debug UI/output shape có thể mở. |
| Pilot 1 PDF | Real PDF do Owner chọn | Project Owner | Kiểm OCR/render/bbox/extraction bằng mắt. |
| Pilot 10 PDF | Real sample có kiểm soát | Project Owner | Đo warning, evidence, Excel quality. |
| Gold dataset | Real-data labels đã quản trị riêng | Project Owner | So sánh OCR/extraction định lượng. |
| Benchmark | Surya vs local VLM | Project Owner + Reviewer | Quyết định path tốt hơn hoặc hybrid. |

## Metric OCR đề xuất

- Page render success rate.
- OCR line count hợp lý theo page.
- Bbox coverage rate.
- Low-confidence line rate nếu Surya trả confidence.
- Manual text accuracy sample theo line/page.
- Marker detection accuracy nếu dùng marker.

TOOLKIT-1 đã implement aggregate contract metrics:

- `page_count_match`
- `empty_page_rate`
- `bbox_coverage_rate`
- `low_confidence_line_rate`
- `section_presence_accuracy`

## Metric extraction đề xuất

- JSON valid rate.
- Field completeness.
- Evidence coverage.
- Evidence mismatch rate.
- Participant row correctness.
- Duplicate/role/date/id warning rate.
- Rows with `NEEDS_REVIEW`.

TOOLKIT-1 đã implement field/participant/evidence metrics:

- `field_exact_match_rate`, required missing, unexpected, mismatch.
- `participant_role_match_count`, missing, extra, field match rate.
- evidence/source page/source line ID coverage.
- `needs_review_rate` và `warning_count`.

## Harness hiện có

- Gold loader: `court_ocr_extract.evaluation.manifest.load_gold_manifest`.
- Prediction loader: `load_prediction_manifest`.
- Metrics: `evaluate_manifests`.
- Safe report: `build_safe_report`, `write_report`.
- CLI validation: `python -m scripts.check_gold_manifest --gold <path>`.
- CLI evaluation: `python -m scripts.evaluate_gold_manifest --gold <path> --predictions <path>`.

CLI không có default vào `data/`, `data_private/`, `outputs/` hoặc pipeline runtime. Report chỉ chứa aggregate numeric metrics.

## Metric Excel/QA đề xuất

- Column schema match.
- Row count match với expected participants.
- Warning readability.
- Không log/output PII ngoài artifact kiểm soát.
- Reviewer acceptance rate.

## Không kết luận từ synthetic

Synthetic fixtures chỉ trả lời câu hỏi “pipeline contract có chạy không”. Chúng không trả lời “OCR có đọc đúng án thật không” hoặc “Local LLM có extract đúng dữ liệu thật không”.

TOOLKIT-1 chưa tính OCR CER/WER vì repo không có và Codex không được đọc line-level gold text thật. Human review và real gold evaluation do Project Owner thực hiện ngoài Codex.
