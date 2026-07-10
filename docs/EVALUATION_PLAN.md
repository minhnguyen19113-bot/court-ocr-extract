# Evaluation Plan

Last updated: 2026-07-08

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

## Metric extraction đề xuất

- JSON valid rate.
- Field completeness.
- Evidence coverage.
- Evidence mismatch rate.
- Participant row correctness.
- Duplicate/role/date/id warning rate.
- Rows with `NEEDS_REVIEW`.

## Metric Excel/QA đề xuất

- Column schema match.
- Row count match với expected participants.
- Warning readability.
- Không log/output PII ngoài artifact kiểm soát.
- Reviewer acceptance rate.

## Không kết luận từ synthetic

Synthetic fixtures chỉ trả lời câu hỏi “pipeline contract có chạy không”. Chúng không trả lời “OCR có đọc đúng án thật không” hoặc “Local LLM có extract đúng dữ liệu thật không”.
